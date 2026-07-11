"""
LOCAL 24/7 GENERATION WORKER
================================
Runs directly on your Windows PC (which already has a residential IP).
No VPS needed. No Tailscale. No SSH. Just pure local power.

Features:
  - Auto-refreshes Google auth tokens via Playwright
  - Keeps browser alive to extract fresh reCAPTCHA before each generation
  - Cycles through your model roster (16 character sheets)
  - Picks random prompts from the elite prompt library
  - Saves generated images to output_ugc/
  - Runs in a loop with configurable delays
  - Logs everything to worker_log.txt

HOW TO RUN:
  python local_generation_worker.py          # Run once (test mode)
  python local_generation_worker.py --loop   # Run 24/7 loop
"""

import os
import sys
import json
import base64
import uuid
import time
import random
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from pricing_engine import calculate_final_price
from utils import save_generated_images
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Configuration
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output_ugc"
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_FILE = BASE_DIR / "worker_log.txt"
MODELS_DIR = BASE_DIR / "models" / "character_sheets"
INPUT_DIR = BASE_DIR / "input_sourcing"

MIN_DELAY_SECONDS = 90
MAX_DELAY_SECONDS = 180

UPLOAD_URL = "https://aisandbox-pa.googleapis.com/v1/flow/uploadImage"
BRIDGE_URL = "http://localhost:9877"


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[{}] {}".format(timestamp, msg)
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def discover_models():
    models = []
    if not MODELS_DIR.exists():
        log("[!] Models dir not found: {}".format(MODELS_DIR))
        return models
    
    # Group files by prefix (e.g., f1, f2, m1, m2)
    files = list(MODELS_DIR.glob("*.png")) + list(MODELS_DIR.glob("*.jpg")) + list(MODELS_DIR.glob("*.jpeg"))
    prefixes = set()
    for f in files:
        # Expect naming like f1_face.png, f1_body.png, f1_sheet.png
        parts = f.name.split('_')
        if len(parts) > 1:
            prefixes.add(parts[0])
    
    for prefix in sorted(list(prefixes)):
        # ONLY load the face reference image (which is named _1.jpg), ignore any others
        ref_files = sorted([str(f) for f in files if f.name.startswith(prefix + "_1")])
        if ref_files:
            models.append({
                "id": prefix,
                "references": ref_files,
                "gender": "female" if prefix.startswith("f") else "male"
            })
            
    log("[+] Discovered {} models: {}".format(len(models), [m['id'] for m in models]))
    return models


def discover_products():
    outfits = []
    curation_dir = BASE_DIR / "MANUAL_CURATION"
    if not curation_dir.exists():
        log("[!] MANUAL_CURATION dir not found.")
        return outfits
    
    for folder in curation_dir.iterdir():
        if folder.is_dir() and folder.name != "_merged_outfits":
            images = list(folder.glob("*.jpg")) + list(folder.glob("*.png")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.webp"))
            
            # Filter out size chart images from the main product shots list
            product_images = []
            for img in images:
                if any(bad in img.name.lower() for bad in ["chart", "size", "guide", "grid"]):
                    continue
                product_images.append(str(img))
                
            if product_images:
                link_file = folder / "link.txt"
                link = ""
                if link_file.exists():
                    try:
                        with open(link_file, "r", encoding="utf-8") as f:
                            link = f.read().strip()
                    except Exception:
                        pass
                
                outfits.append({
                    "folder_path": str(folder),
                    "name": folder.name,
                    "images": product_images,
                    "link": link
                })
    
    log("[+] Discovered {} curated outfits in MANUAL_CURATION/".format(len(outfits)))
    return outfits


# ─── TIERED PROMPT SYSTEM ───
# Each prompt is tagged with a "tier" for carousel slide positioning.
# TIER_A = Hero close-up (waist-up, garment fills 60%+ of frame)
# TIER_B = Full-body lifestyle (shows fit + context)
# TIER_C = Detail/texture macro (fabric, stitching close-up)
# TIER_D = Product-only flat lay (no model, garment on surface)
# TIER_E = Outfit styling (different ways to wear / cross-sell)

PROMPT_TIERS = {
    "TIER_A": [
        # Hero Close-Up — garment is the STAR
        (
            "Photo 1, 2 and 3 are the model (face, body and sheet). Use image 4 and 5 as the product. "
            "Put the clothing from the product images on the model. "
            "Generate a hyperrealistic photo of the model posing with another friend in a photo shoot at a professional studio. "
            "The garment MUST occupy a prominent part of the frame. Sharp focus on "
            "the garment texture. "
            "Soft natural studio lighting, warm tones. Clean neutral background. "
            "They look directly at camera with a confident, relaxed expression. "
            "Shot on 85mm lens at f/2.0, shallow depth of field on background only. "
            "Skin has visible pores, natural imperfections. Premium fashion campaign look."
        ),
        (
            "Photo 1, 2 and 3 are the model (face, body and sheet). Use image 4 and 5 as the product. "
            "Put the clothing from the product images on the model. "
            "Generate a hyperrealistic photo of the model posing with another friend in a photo shoot at a studio. "
            "The garment is the focal point, filling the center of frame. "
            "Studio setting with overhead LED lighting and backdrop. "
            "Natural skin glow, visible pores. Authentic high-end aesthetic. "
            "Slight lens flare from studio light. RAW photo quality."
        ),
        (
            "Photo 1, 2 and 3 are the model (face, body and sheet). Use image 4 and 5 as the product. "
            "Put the clothing from the product images on the model. "
            "Generate a hyperrealistic upper-body photo of the model posing with another friend in a photo shoot at a studio. "
            "Framed from head to waist, the garment dominates the composition. "
            "They are standing in a modern studio setup, "
            "golden hour style studio light hitting the fabric. "
            "Expression is candid, mid-smile. Shot on Sony A7IV, 50mm f/1.4."
        ),
    ],
    "TIER_B": [
        # Full-Body Lifestyle — shows fit in context
        (
            "Put the exact outfit from the second image on the person from the first image. "
            "Generate a hyperrealistic full-body OOTD photo. "
            "Late afternoon golden hour, urban sidewalk with clean concrete wall. "
            "Shot on 85mm at f/1.8, shallow depth of field with blurred background. "
            "Natural confident mid-stride pose. "
            "iPhone camera roll aesthetic, slight film grain."
        ),
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic lifestyle photo. She sits at a trendy minimalist cafe. "
            "Warm interior lighting, latte art on table, soft bokeh. Candid mid-laugh moment. "
            "Shot on iPhone 15 Pro Max. Natural colors, no heavy filters. "
            "Authentic UGC content creator aesthetic."
        ),
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic TikTok-style fit check photo. "
            "Full body visible, standing in a well-lit bedroom. Ring light creates catch light in "
            "eyes. Hand-on-hip pose, confident smirk. "
            "Shot on iPhone front camera. Authentic Gen-Z aesthetic. Subtle room decor in background."
        ),
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic outdoor editorial photo. "
            "Full body framing, standing in a lush green park with dappled sunlight through trees. "
            "Wind gently moving her hair. "
            "Shot on Sony A7IV, 50mm f/1.4, creamy bokeh. Relaxed editorial pose. "
            "High-fashion magazine quality but authentic and approachable."
        ),
    ],
    "TIER_C": [
        # Detail / Texture Macro — fabric close-ups
        (
            "Extreme close-up macro photography of this EXACT garment from the product "
            "reference image, being worn by a person. Focus on a 6-inch section of the "
            "fabric showing the weave, texture, stitching, and material quality. The "
            "garment color and pattern match the reference EXACTLY. Soft natural side "
            "lighting revealing fabric depth. Shot on 100mm macro lens, f/4, razor sharp "
            "focus on textile fibers. Creamy bokeh on skin visible at edges. "
            "Premium e-commerce detail shot. 8K resolution quality."
        ),
        (
            "Close-up detail photograph of this EXACT garment from the product reference "
            "being worn. Camera focuses on the collar, zipper, or button area -- showing "
            "construction quality and design details. The garment color and design match "
            "EXACTLY. Natural soft lighting, clean composition. The person's chin and "
            "neck visible at top of frame for context. Shot on 85mm at f/2.8. "
            "Premium brand photography aesthetic. Sharp focus on garment hardware."
        ),
    ],
    "TIER_D": [
        # Product-Only Flat Lay — no model, just the garment
        (
            "Professional flat lay photography of this EXACT garment from the product "
            "reference image. The garment is neatly laid out on a clean white linen bed "
            "sheet. It is styled with complementary accessories -- a watch, sunglasses, "
            "and a small potted plant nearby. Overhead bird's-eye view. Soft diffused "
            "natural daylight from a nearby window. The garment color, pattern, and design "
            "match the reference EXACTLY. Clean, minimal, aspirational lifestyle aesthetic. "
            "Instagram fit check flat lay style. Shot on iPhone 15 Pro from above."
        ),
        (
            "Professional product-only photograph of this EXACT garment from the product "
            "reference image. The garment hangs on a minimal wooden hanger against a clean "
            "cream-colored wall. Soft directional window light. The full garment is visible "
            "-- every design detail, color, and texture matches the reference EXACTLY. "
            "Clean e-commerce photography style with lifestyle warmth. No model, no "
            "distractions. The garment is the sole focus. Shot on 50mm at f/2.8."
        ),
    ],
    "TIER_E": [
        # Night Out / Special Context
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic night-out photo. "
            "Standing outside a trendy restaurant, warm ambient neon lights reflecting off wet pavement. "
            "Shot on iPhone 15 Pro night mode. Natural skin glow. Candid pose checking phone."
        ),
        (
            "Put the exact garment from the second image on the person from the first image. "
            "Generate a hyperrealistic cozy home content creator photo. "
            "Sitting casually on a cream couch in a minimalist living room, legs tucked under. "
            "Warm afternoon light from large windows. Coffee table with candles nearby. "
            "Shot on iPhone, natural warm tones. Authentic 'outfit of the day at home' aesthetic."
        ),
    ],
}

# Flatten for random selection (weighted toward hero + lifestyle)
ELITE_PROMPTS = (
    PROMPT_TIERS["TIER_A"] * 3 +   # 3x weight — hero shots most important
    PROMPT_TIERS["TIER_B"] * 2 +   # 2x weight — lifestyle context
    PROMPT_TIERS["TIER_C"] * 1 +   # 1x weight — detail shots
    PROMPT_TIERS["TIER_D"] * 1 +   # 1x weight — flat lays
    PROMPT_TIERS["TIER_E"] * 1     # 1x weight — special context
)


# ─── BROWSER SESSION (REPLACED BY CHROME EXTENSION & TOKEN BRIDGE) ───

async def fetch_fresh_tokens() -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Fetch fresh bearer, recaptcha, projectId, and authUser from the bridge.
    Retries up to 5 times if the bridge returns 503 (meaning extension is fetching).
    """
    log("[*] Querying local token bridge for active session tokens...")
    for attempt in range(1, 6):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{BRIDGE_URL}/tokens", timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    bearer = data.get("bearer")
                    recaptcha = data.get("recaptcha")
                    project_id = data.get("projectId")
                    auth_user = data.get("authUser", "0")
                    if bearer and recaptcha:
                        log(f"[BRIDGE] Retrieved active tokens (age: {data.get('age_seconds')}s)!")
                        return bearer, recaptcha, project_id, auth_user
                elif resp.status_code == 503:
                    log(f"[BRIDGE] Tokens stale/missing. Extension signaled. Waiting 2s (attempt {attempt}/5)...")
                else:
                    log(f"[BRIDGE] Bridge returned status {resp.status_code}")
        except Exception as e:
            log(f"[BRIDGE] Bridge connection error: {e}")
            break
        await asyncio.sleep(2.0)
    return None, None, None, None


# ─── SINGLE JOB ───

async def run_single_generation(model, product_paths, custom_prompt=None, campaign_folder=None, shot_name=None):
    """
    product_paths: List of file paths to products to combine into one outfit
    """
    bearer, recaptcha, project_id, auth_user = await fetch_fresh_tokens()
    if not bearer or not recaptcha:
        log("[!] Could not acquire fresh Flow tokens from bridge. Skipping generation.")
        return []
        
    if not project_id or project_id in ["NOT_FOUND", "None", "null", ""]:
        project_id = "1e47f082-dbd5-4cf3-869e-cffbf8722f1b"
        log(f"  [!] Project ID not found. Falling back to default: {project_id}")

    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "text/plain;charset=UTF-8",
        "Referer": "https://labs.google/",
        "Origin": "https://labs.google",
        "X-Goog-AuthUser": auth_user,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    }

    if isinstance(product_paths, str):
        product_paths = [product_paths]
        
    # Get a combined name for output files
    product_name = "_and_".join([Path(p).stem for p in product_paths])[:40]
    
    # Check if this item needs a simple prompt to preserve graphics
    from smart_router import detect_needs_vton
    needs_simple = detect_needs_vton(product_name, product_paths[0])
    
    prompt = custom_prompt if custom_prompt else random.choice(ELITE_PROMPTS)
    
    if needs_simple and "Ignore" not in prompt:
        # Append graphics preservation hint instead of destroying the scene director prompt
        prompt += " Preserve the exact graphics, text, and logos from the product image."
        log("  [*] Appended VTON graphic preservation hint")

    if model["gender"] == "male":
        prompt = prompt.replace("her ", "him ").replace("She ", "He ").replace("she ", "he ").replace("lady", "man")

    # Adjust prompt if multiple products
    if len(product_paths) > 1:
        prompt = prompt.replace("this EXACT garment", "these EXACT garments")
        prompt = prompt.replace("The garment", "The garments")

    log("")
    log("=" * 60)
    log("[JOB] Model: {} | Outfit Combo: {}".format(model['id'], product_name))
    log("=" * 60)

    async with httpx.AsyncClient() as client:
        try:
            # Upload model references only if a human is needed in the scene
            asset_ids = []
            skip_model = "No human" in prompt
            
            if not skip_model:
                log("  [*] Uploading {} model references...".format(len(model["references"])))
                for ref_path in model["references"]:
                    aid = await upload_image(client, ref_path, headers, project_id)
                    if aid:
                        asset_ids.append(aid)
            else:
                log("  [*] Product-only shot (Flatlay/Ghost) - Skipping model references.")
            
            # Upload all product pieces for the outfit
            for path in product_paths:
                pid = await upload_image(client, path, headers, project_id)
                if pid:
                    asset_ids.append(pid)

            if len(asset_ids) < 1:
                log("[!] Not enough uploads. Skipping.")
                return []

            # Quality gate retry loop: up to 3 attempts total (1 initial + 2 retries)
            saved = []
            for attempt in range(3):
                if attempt > 0:
                    log("  [*] Quality gate retry attempt {}/3...".format(attempt + 1))
                    bearer, recaptcha, project_id, auth_user = await fetch_fresh_tokens()
                    if not bearer or not recaptcha:
                        log("[!] Could not refresh Flow tokens from bridge. Skipping attempt.")
                        continue
                    headers["Authorization"] = f"Bearer {bearer}"
                    headers["X-Goog-AuthUser"] = auth_user
                
                log("[>>] Generating with GEM_PIX_2...")
                result = await generate_image(client, prompt, asset_ids, headers, project_id, recaptcha)

                saved = save_generated_images(result, model["id"], product_name, product_paths, campaign_folder, shot_name)
                log("[OK] Job complete! {} images saved.".format(len(saved)))
                return saved

        except httpx.HTTPStatusError as e:
            log("[!] HTTP Error {}: {}".format(e.response.status_code, e.response.text[:300]))
            return []
        except Exception as e:
            log("[!] Generation error: {}".format(e))
            traceback.print_exc()
            return []


# ─── MAIN LOOP ───

async def main():
    loop_mode = "--loop" in sys.argv

    log("")
    log("=" * 50)
    log("LOCAL 24/7 GENERATION WORKER")
    if loop_mode:
        log("Mode: CONTINUOUS LOOP")
    else:
        log("Mode: SINGLE RUN (test)")
    log("=" * 50)

    models = discover_models()
    products = discover_products()

    generation_count = 0

    try:
        while True:
            # Re-discover curated outfits each cycle
            outfits = discover_products()
            if not outfits:
                log("[!] No curated outfits found in MANUAL_CURATION/. Waiting 30s...")
                await asyncio.sleep(30)
                continue

            # Pop the first outfit to process
            outfit = outfits[0]
            selected_products = outfit["images"]
            
            if not selected_products:
                log(f"[!] Outfit {outfit['name']} has no images. Deleting folder...")
                import shutil
                shutil.rmtree(outfit["folder_path"], ignore_errors=True)
                continue

            # --- SMART MERGE LOGIC ---
            # If multiple images, treat them as a single combined outfit for the prompts
            is_combined_outfit = len(selected_products) > 1
            
            # --- CAMPAIGN MIX: 2 MALE, 1 FEMALE per drop ---
            males = [m for m in models if m["gender"] == "male"]
            females = [f for f in models if f["gender"] == "female"]
            
            # Define the targets for this specific product drop
            target_models = []
            if males:
                target_models.append(random.choice(males))
                if len(males) > 1:
                    target_models.append(random.choice([m for m in males if m != target_models[0]]))
                else:
                    target_models.append(males[0])
            if females:
                target_models.append(random.choice(females))
                
            log(f"[*] Processing '{outfit['name']}' with {len(target_models)} campaigns (Mix: 2M/1F requested)")

            overall_success = True
            for model in target_models:
                log(f"[*] Starting campaign with model: {model['id']} ({model['gender']})")

                # 5 unique prompts per product via Scene Director (randomized every cycle)
                from scene_director import build_campaign_prompts
                m_count = len(model["references"])
                p_start = m_count + 1
                p_end = m_count + len(selected_products)
                campaign_prompts = build_campaign_prompts(model, m_count, p_start, p_end, product_count=len(selected_products))
                log(f"[SCENE] Generated 5 unique shots (Editorial / Lifestyle / Urban / FlatLay / Ghost)")

                shot_types = ["01_editorial", "02_lifestyle", "03_urban", "04_flatlay", "05_ghost"]
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                campaign_folder = f"{ts}_{model['id']}_{outfit['name']}"
                
                # --- PRICING LOGIC ---
                metadata_file = Path(outfit["folder_path"]) / "metadata.json"
                outfit_meta_file = Path(outfit["folder_path"]) / "outfit_metadata.json"
                
                original_cny = 0
                size_info = "Check listing"
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        m = json.load(f)
                        original_cny = m.get("price_cny", 0)
                        size_info = m.get("size_info", "Not specified")
                elif outfit_meta_file.exists():
                    with open(outfit_meta_file, "r") as f:
                        m = json.load(f)
                        # Sum up prices and collect size info
                        original_cny = sum(item.get("price", 0) for item in m.get("items", []))
                        size_info = " | ".join([item.get("size_info", "N/A") for item in m.get("items", [])])
                
                price_data = calculate_final_price(original_cny)
                final_usd = price_data["final_usd"]
                
                # --- AUTO-GENERATE KAKOBUY CHECKOUT LINKS ---
                READY_DIR = BASE_DIR / "OUTPUT_READY_FOR_SALE"
                campaign_dir = READY_DIR / campaign_folder
                campaign_dir.mkdir(parents=True, exist_ok=True)
                links_file = campaign_dir / "checkout_links.txt"
                
                try:
                    with open(links_file, "w", encoding="utf-8") as f:
                        f.write("=== KAKOBUY AUTO-DROPSHIP LINKS ===\n")
                        f.write(f"Retail Price: ${final_usd} USD\n")
                        f.write(f"Est. Profit:  ${price_data['profit_usd']} USD\n")
                        f.write(f"Sizes/Fit:    {size_info}\n")
                        f.write("-----------------------------------\n")
                        f.write(f"Outfit Name: {outfit['name']}\n")
                        link = outfit["link"]
                        if link:
                            if "weidian.com" in link or "taobao.com" in link or "1688.com" in link or "youshop10.com" in link:
                                kako_link = f"https://www.kakobuy.com/item/details?url={link}"
                                f.write(f"Kakobuy Checkout: {kako_link}\n")
                            else:
                                f.write(f"Raw Link: {link}\n")
                        else:
                            f.write("Kakobuy Checkout: [No link provided via Discord drop]\n")
                except Exception as e:
                    log(f"  [!] Error generating checkout links: {e}")
                # --------------------------------------------

                for i, p in enumerate(campaign_prompts):
                    shot_name = shot_types[i] if i < len(shot_types) else f"0{i+1}_extra"
                    # Save into the READY directory instead of output_ugc
                    saved = await run_single_generation(model, selected_products, custom_prompt=p, campaign_folder=f"../OUTPUT_READY_FOR_SALE/{campaign_folder}", shot_name=shot_name)
                    generation_count += 1
                    log("[STATS] Total generations: {}".format(generation_count))
                    
                    if not saved:
                        log("[!] Generation failed for this shot.")
                        overall_success = False
                        break
                        
                    if p != campaign_prompts[-1]:
                        await asyncio.sleep(5)  # Short delay between the 4 shots
                
                if not overall_success:
                    break # Stop trying other models for this drop if it's failing
            
            # If successfully completed ALL models, delete the manual curation folder
            if overall_success:
                log(f"[OK] All 3 campaigns built perfectly for {outfit['name']}! Removing from queue.")
                import shutil
                shutil.rmtree(outfit["folder_path"], ignore_errors=True)

            if not loop_mode:
                log("[OK] Single run complete. Use --loop for 24/7.")
                break

            delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
            log("[WAIT] Sleeping {}s...".format(delay))
            await asyncio.sleep(delay)
    finally:
        log("[*] Shutting down worker...")


if __name__ == "__main__":
    try:
        import httpx
    except ImportError:
        print("Installing httpx...")
        os.system("pip install httpx")
        import httpx

    asyncio.run(main())
