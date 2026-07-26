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
from typing import Optional
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
from prompt_library import PROMPT_TIERS, ELITE_PROMPTS
from prompt_library import get_prompts_for_product, get_flat_lay_only_prompts
from prompt_library import GHOST_MANNEQUIN_PROMPTS, HANGER_PROMPTS, SET_FLAT_LAY_PROMPTS, DETAIL_CLOSEUP_PROMPTS
from vision_evaluator import VisionEvaluator
from utils import save_generated_images

load_dotenv()

# Initialize Quality Gate Evaluator
evaluator = VisionEvaluator()

# Configuration
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output_ugc"
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_FILE = BASE_DIR / "worker_log.txt"
MODELS_DIR = BASE_DIR / "models" / "character_sheets"
INPUT_DIR = BASE_DIR / "input_sourcing"

BAD_IMAGE_KEYWORDS = ("chart", "size", "guide", "grid")

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
    products = []
    if not INPUT_DIR.exists():
        log("[!] Input dir not found: {}".format(INPUT_DIR))
        return products
    
    # Import quality validator
    try:
        from smart_sourcer import validate_product_image
        has_validator = True
    except ImportError:
        has_validator = False
    
    VALID_EXTS = ('.png', '.jpg', '.jpeg', '.webp')

    # Discover subdirectories and loose files in one pass
    try:
        with os.scandir(INPUT_DIR) as scanner:
            for entry in scanner:
                if entry.is_dir() and entry.name not in ("outfit_grid", "_rejected", "__pycache__"):
                    subdir_path = Path(entry.path)

                    # Filter/Validate images in the folder using scandir
                    valid_images = []
                    try:
                        with os.scandir(subdir_path) as sub_scanner:
                            for file_entry in sub_scanner:
                                if file_entry.is_file() and file_entry.name.lower().endswith(VALID_EXTS):
                                    name_lower = file_entry.name.lower()
                                    if any(bad in name_lower for bad in BAD_IMAGE_KEYWORDS):
                                        continue
                                    if has_validator:
                                        check = validate_product_image(file_entry.path)
                                        if check.get("valid"):
                                            valid_images.append(file_entry.path)
                                    else:
                                        if file_entry.stat().st_size >= 30000:
                                            valid_images.append(file_entry.path)
                    except OSError as e:
                        log(f"[!] Error reading subdirectory {subdir_path}: {e}")

                    if valid_images:
                        # Load metadata if exists
                        metadata = {}
                        meta_file = subdir_path / "metadata.json"
                        if meta_file.exists():
                            try:
                                with open(meta_file, "r", encoding="utf-8") as mf:
                                    metadata = json.load(mf)
                            except Exception:
                                pass

                        # Load link if exists
                        link = metadata.get("link", "")
                        link_file = subdir_path / "link.txt"
                        if not link and link_file.exists():
                            try:
                                with open(link_file, "r", encoding="utf-8") as lf:
                                    link = lf.read().strip()
                            except Exception:
                                pass

                        products.append({
                            "is_folder": True,
                            "folder_path": str(subdir_path),
                            "name": metadata.get("product_name") or entry.name,
                            "images": valid_images,
                            "link": link,
                            "metadata": metadata
                        })
                elif entry.is_file() and entry.name.lower().endswith(VALID_EXTS):
                    name_lower = entry.name.lower()
                    if any(bad in name_lower for bad in BAD_IMAGE_KEYWORDS):
                        continue
                    if has_validator:
                        check = validate_product_image(entry.path)
                        if not check.get("valid"):
                            continue
                    else:
                        if entry.stat().st_size < 30000:
                            continue

                    stem = Path(entry.name).stem
                    products.append({
                        "is_folder": False,
                        "folder_path": None,
                        "name": stem,
                        "images": [entry.path],
                        "link": "",
                        "metadata": {}
                    })
    except OSError as e:
        log(f"[!] Error reading input directory {INPUT_DIR}: {e}")
    
    log("[+] Discovered {} structured products".format(len(products)))
    return products



# ─── TIERED PROMPT SYSTEM ───
# Imported from prompt_library.py for unified prompt management.


# ─── BROWSER SESSION (kept alive for fresh reCAPTCHA) ───

async def setup_browser():
    """Opens Playwright, loads Flow, captures real ya29 Bearer token.
    Returns (pw, context, page, bearer). Browser stays open for reCAPTCHA."""
    log("[*] Setting up Playwright browser session...")
    from playwright.async_api import async_playwright

    profile_dir = os.path.abspath("playwright_profile")
    captured_bearer = {"token": None}

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        channel="chrome",
    )
    page = await context.new_page()

    def on_request(request):
        url = request.url
        if "aisandbox-pa.googleapis.com" in url or "labs.google" in url:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer ya29.") and not captured_bearer["token"]:
                captured_bearer["token"] = auth_header.replace("Bearer ", "")
                log("[+] Captured REAL ya29 Bearer token from network!")

    page.on("request", on_request)

    await page.goto(
        "https://labs.google/fx/tools/flow",
        wait_until="networkidle",
        timeout=60000
    )

    # Give the user plenty of time (5 minutes) to log in manually if needed
    max_wait = 300 
    start_wait = time.time()
    while not captured_bearer["token"] and (time.time() - start_wait < max_wait):
        if page.is_closed():
            log("[!] Browser window closed by user. Stopping wait.")
            break
        await page.wait_for_timeout(2000)
        if captured_bearer["token"]:
            break

    if not captured_bearer["token"]:
        log("[*] Navigating back to Flow to ensure session is active...")
        try:
            if "labs.google/fx/tools/flow" not in page.url:
                await page.goto("https://labs.google/fx/tools/flow", wait_until="networkidle", timeout=15000)
            # Give it a few seconds to capture the token naturally via network requests
            for _ in range(5):
                await page.wait_for_timeout(1000)
                if captured_bearer["token"]:
                    break
        except Exception as e:
            log(f"[!] Navigation fallback failed: {e}")

    if not captured_bearer["token"]:
        log("[*] Trying session endpoint fallback...")
        bearer_fallback = await page.evaluate("""async () => {
            try {
                const req = await fetch('https://labs.google/fx/api/auth/session', {credentials:'include'});
                if (!req.ok) return "HTTP_" + req.status;
                const auth = await req.json();
                return auth.access_token || JSON.stringify(auth);
            } catch (err) { return "ERROR_" + err.message; }
        }""")
        if bearer_fallback and bearer_fallback.startswith("ya29."):
            captured_bearer["token"] = bearer_fallback
        else:
            log(f"[?] Session fallback result: {bearer_fallback}")

    bearer = captured_bearer["token"]
    if not bearer:
        log("[!] FATAL: Could not extract Bearer token.")
        await context.close()
        await pw.stop()
        return None, None, None, None

    log("[+] Bearer ready! Type: {}".format(
        "ya29 OAuth" if bearer.startswith("ya29.") else "session"))
    return pw, context, page, bearer


async def get_fresh_recaptcha(page):
    """Extracts a FRESH reCAPTCHA token right before a generation call."""
    try:
        site_key = os.environ.get("RECAPTCHA_SITE_KEY", "")
        recaptcha = await page.evaluate("""async (siteKey) => {
            try {
                if (typeof grecaptcha !== 'undefined' && grecaptcha.enterprise) {
                    return await grecaptcha.enterprise.execute(
                        siteKey,
                        {action: 'IMAGE_GENERATION'}
                    );
                }
                return null;
            } catch { return null; }
        }""", site_key)
        if recaptcha:
            log("[+] Fresh reCAPTCHA extracted!")
        else:
            log("[!] reCAPTCHA returned null")
        return recaptcha
    except Exception as e:
        log("[!] reCAPTCHA error: {}".format(e))
        return None


# ─── API CALLS ───

async def upload_image(client, image_path, headers, project_id):
    log("  [^] Uploading: {}".format(Path(image_path).name))
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')

    payload = {
        "clientContext": {"projectId": project_id, "tool": "PINHOLE"},
        "imageBytes": img_b64
    }

    send_headers = {k: v for k, v in headers.items()}
    response = await client.post(UPLOAD_URL, headers=send_headers, content=json.dumps(payload), timeout=60.0)
    response.raise_for_status()

    data = response.json()
    asset_id = data.get("media", {}).get("name")
    if asset_id:
        log("  [OK] Uploaded: {}...".format(asset_id[:20]))
    else:
        log("  [!] Upload unexpected format: {}".format(str(data)[:150]))
    return asset_id


async def generate_image(client, prompt, asset_ids, headers, project_id, recaptcha):
    generate_url = "https://aisandbox-pa.googleapis.com/v1/projects/{}/flowMedia:batchGenerateImages".format(project_id)

    image_inputs = [
        {"imageInputType": "IMAGE_INPUT_TYPE_REFERENCE", "name": aid}
        for aid in asset_ids if aid
    ]

    payload = {
        "clientContext": {
            "recaptchaContext": {
                "token": recaptcha,
                "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
            },
            "projectId": project_id,
            "tool": "PINHOLE"
        },
        "mediaGenerationContext": {"batchId": str(uuid.uuid4())},
        "useNewMedia": True,
        "requests": [{
            "clientContext": {
                "recaptchaContext": {
                    "token": recaptcha,
                    "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
                },
                "projectId": project_id,
                "tool": "PINHOLE"
            },
            "imageModelName": "GEM_PIX_2",
            "imageAspectRatio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
            "structuredPrompt": {"parts": [{"text": prompt}]},
            "seed": random.randint(1, 2147483647),
            "imageInputs": image_inputs
        }]
    }

    send_headers = {k: v for k, v in headers.items()}
    response = await client.post(generate_url, headers=send_headers, content=json.dumps(payload), timeout=120.0)
    response.raise_for_status()
    return response.json()




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
            prompt_lower = prompt.lower()
            skip_model = any(marker in prompt_lower for marker in [
                "no human", "no person", "no model", "no mannequin",
                "flat lay", "flat-lay", "ghost mannequin", "product-only",
                "floating garment", "hanger", "on-foot", "unboxing"
            ])
            
            if not skip_model:
                log("  [*] Uploading {} model references...".format(len(model["references"])))
                for ref_path in model["references"]:
                    aid = await upload_image(client, ref_path, headers, project_id)
                    if aid:
                        asset_ids.append(aid)
            else:
                log("  [*] Product-only shot — skipping model face references.")
            
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
                
                if not saved:
                    log("  [!] No images saved from generation.")
                    continue

                # Run Quality Gate
                all_passed = True
                for img_path in saved:
                    # 1. Quick local pre-filter (resolution, blur, brightness)
                    quick = evaluator.quick_quality_check(img_path)
                    if not quick["passed"]:
                        log("  ❌ Pre-filter REJECTED {}: {}".format(Path(img_path).name, quick["reason"]))
                        evaluator._delete_bad_image(img_path)
                        all_passed = False
                        break

                    # 2. Full Vision AI Quality Gate
                    eval_result = evaluator.evaluate_image(img_path)
                    if not eval_result["passed"]:
                        log("  ❌ Vision Gate REJECTED {}: {}".format(Path(img_path).name, eval_result.get("reason", "Score below threshold")))
                        evaluator._delete_bad_image(img_path)
                        all_passed = False
                        break
                
                if all_passed:
                    log("[OK] Quality Gate passed! {} images saved.".format(len(saved)))
                    return saved
                else:
                    saved = []
            
            log("[!] Quality Gate failed after 3 attempts.")
            return []

        except httpx.HTTPStatusError as e:
            log("[!] HTTP Error {}: {}".format(e.response.status_code, e.response.text[:300]))
            return []
        except Exception as e:
            log("[!] Generation error: {}".format(e))
            traceback.print_exc()
            return []


def copy_source_images(curation_dir: Path, output_dir: Path):
    """Copy original Yupoo/Weidian source photos to output alongside AI shots.
    These appear on the product page as 'Source Photos' to show the real product."""
    import shutil
    source_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    source_prefixes = ('front_angle', 'back_angle', 'side_angle', 'angle_', 'detail_close')
    
    if not curation_dir.exists():
        log(f"  [!] Source image dir not found: {curation_dir}")
        return
    
    try:
        with os.scandir(curation_dir) as scanner:
            for entry in scanner:
                if entry.is_file():
                    path_obj = Path(entry.name)
                    if path_obj.suffix.lower() in source_extensions and any(path_obj.stem.startswith(p) for p in source_prefixes):
                        dest = output_dir / f"source_{entry.name}"
                        if not dest.exists():
                            shutil.copy2(entry.path, str(dest))
                            log(f"  [+] Copied source image: {entry.name}")
    except Exception as e:
        log(f"  [!] Error copying source images: {e}")


async def generate_outfit_shots(outfit_config: dict, models: list):
    """Generate on-model shots for a curated outfit.
    
    This is the ONLY path that puts products on a model.
    Every visible item must be from the store.
    
    outfit_config: {
        'name': str,
        'products': [{'path': Path, 'category': str}, ...],
        'gender': 'male' or 'female'
    }
    """
    # Collect hero images from all items in the outfit
    all_product_paths = []
    for item in outfit_config['products']:
        item_dir = Path(item['path'])
        for f in sorted(item_dir.iterdir()):
            if f.suffix.lower() in {'.jpg', '.jpeg', '.png'} and not f.name.startswith('size_chart'):
                all_product_paths.append(str(f))
                break  # Just the hero image from each product
    
    if len(all_product_paths) < 2:
        log(f"[!] Outfit '{outfit_config['name']}' needs at least 2 products. Skipping.")
        return []
    
    # Pick a gender-matched model
    gender = outfit_config.get('gender', 'male')
    gender_models = [m for m in models if m['gender'] == gender]
    model = random.choice(gender_models) if gender_models else random.choice(models)
    
    # Create outfit output directory
    from utils import slugify
    outfit_name = slugify(outfit_config['name'])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfit_dir = OUTPUT_DIR / f"{ts}_{model['id']}_outfit_{outfit_name}"
    outfit_dir.mkdir(parents=True, exist_ok=True)
    
    # Use on-model prompts — these are appropriate when the FULL outfit is provided
    from prompt_library import CLOTHING_PROMPTS, MALE_UGC_PROMPTS
    on_model_prompts = MALE_UGC_PROMPTS if gender == 'male' else CLOTHING_PROMPTS
    
    results = []
    for shot_idx, (shot_name, prompt) in enumerate(list(on_model_prompts.items())[:3]):
        saved = await run_single_generation(
            model, all_product_paths, 
            custom_prompt=prompt, 
            campaign_folder=str(outfit_dir),
            shot_name=f"outfit_{shot_name}"
        )
        results.extend(saved)
        if shot_idx < 2:
            await asyncio.sleep(5)
    
    log(f"[OK] Outfit '{outfit_config['name']}' generated {len(results)} shots.")
    return results


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

    if not models:
        log("[!] No models found in models/character_sheets/.")
        return
    if not products:
        log("[!] No products found in input_sourcing/. Checking test_products/ fallback...")
        test_dir = BASE_DIR / "test_products"
        if test_dir.exists():
            import shutil
            for f in test_dir.glob("*"):
                if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp') and f.stat().st_size > 30000:
                    shutil.copy(f, INPUT_DIR / f.name)
                    log(f"  [+] Copied fallback product: {f.name}")
            products = discover_products()
        if not products:
            log("[!] No products anywhere. Drop images into input_sourcing/ and restart.")
            return

    generation_count = 0

    try:
        while True:
            # Re-discover products each cycle (new ones may have been added)
            products = discover_products()
            if not products:
                log("[!] No products found in input_sourcing/. Launching VLM Autonomous Sourcer...")
                try:
                    from vlm_product_sourcer import VLMSourcer, SELLERS
                    sourcer = VLMSourcer(headless=True)
                    await sourcer.start()
                    for seller in SELLERS:
                        for cat_id, cat_url in seller["categories"].items():
                            await sourcer.scrape_category(cat_url, cat_id, max_items=2)
                    await sourcer.close()
                    log("[+] VLM Sourcing cycle complete. Reloading products...")
                    products = discover_products()
                    if not products:
                        log("[!] VLM Sourcing yielded no new products. Waiting 60s...")
                        await asyncio.sleep(60)
                        continue
                except Exception as e:
                    log(f"[!] VLM Sourcing failed: {e}")
                    await asyncio.sleep(60)
                    continue

            model = random.choice(models)
            
            # Filter products based on gender match to prevent cross-dressing unless requested
            matched_products = []
            for p in products:
                name_to_check = p["name"].lower()
                
                if model["gender"] == "female" and ("female" in name_to_check or "wmns" in name_to_check or "women" in name_to_check):
                    matched_products.append(p)
                elif model["gender"] == "male" and (("male" in name_to_check and "female" not in name_to_check) or ("men" in name_to_check and "women" not in name_to_check)):
                    matched_products.append(p)
                elif "unisex" in name_to_check:
                    matched_products.append(p)
                elif not ("female" in name_to_check or "wmns" in name_to_check or "women" in name_to_check or "male" in name_to_check or "men" in name_to_check):
                    matched_products.append(p)
                    
            if not matched_products:
                log("[!] No gender-matched products found. Falling back to all products.")
                matched_products = products

            # ── CATEGORY-BASED GENERATION ROUTING ──
            # Individual products get product-only shots (no on-model)
            # On-model is ONLY for curated outfits via generate_outfit_shots()
            
            p_dict = random.choice(matched_products)
            selected_products = p_dict["images"][:3]
            selected_products_dicts = [p_dict]
            base_product_name = p_dict["name"].split(".")[0]
            distinct_product_count = 1
            
            # Determine product category for shot plan
            metadata = p_dict.get("metadata", {})
            category = (metadata.get("category") or metadata.get("product_category") or "clothing").lower()
            is_set_flag = metadata.get("is_set", False) or category == "set"
            
            # Map common category names to shot plan keys
            if any(k in category for k in ["shoe", "sneaker", "boot", "trainer"]):
                shot_category = "shoes"
            elif any(k in category for k in ["top", "hoodie", "jacket", "tee", "shirt", "sweater"]):
                shot_category = "tops"
            elif any(k in category for k in ["bottom", "pant", "trouser", "jogger", "short"]):
                shot_category = "bottoms"
            elif any(k in category for k in ["bag", "backpack"]):
                shot_category = "bags"
            elif any(k in category for k in ["accessory", "watch", "chain", "ring", "sunglasses"]):
                shot_category = "accessories"
            elif any(k in category for k in ["beauty", "fragrance", "skincare"]):
                shot_category = "beauty"
            else:
                shot_category = "clothing"  # Default fallback
            
            shot_plan = get_prompts_for_product(shot_category, is_set=is_set_flag)
            
            log(f"  [ROUTE] Category: {shot_category} | Is Set: {is_set_flag} | On-Model: {shot_plan['on_model']}")
            log(f"  [ROUTE] Shot plan: {len(shot_plan['product_shots'])} product-only shots")

            # Build prompts from the shot plan
            campaign_prompts = []
            shot_types = []
            for prompt_dict, shot_key in shot_plan["product_shots"]:
                # Pick a random prompt from each dict
                prompt_key = random.choice(list(prompt_dict.keys()))
                prompt_text = prompt_dict[prompt_key]
                # Ensure product-only prompts don't create model shots
                if "No human" not in prompt_text and "person" not in prompt_text.lower()[:50]:
                    prompt_text = prompt_text  # Flat lays / ghost mannequin already don't use models
                campaign_prompts.append(prompt_text)
                shot_types.append(f"{len(shot_types)+1:02d}_{shot_key}")

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Sanitize base_product_name to be a safe folder name
            import re as _re
            safe_product_name = _re.sub(r'[^\w\s-]', '', base_product_name).strip().replace(' ', '_')
            campaign_folder = f"{ts}_{model['id']}_{safe_product_name}"
            
            # --- AUTO-GENERATE KAKOBUY CHECKOUT LINKS ---
            campaign_dir = OUTPUT_DIR / campaign_folder
            campaign_dir.mkdir(parents=True, exist_ok=True)
            links_file = campaign_dir / "checkout_links.txt"
            
            try:
                with open(links_file, "w", encoding="utf-8") as f:
                    f.write("=== DROPSHIP & FULFILLMENT LINKS ===\n")
                    f.write("Supports: CJ Dropshipping, Kakobuy, Original Chinese Brands, Yupoo Reps\n\n")
                    for p_dict in selected_products_dicts:
                        metadata = p_dict.get("metadata") or {}
                        f.write(f"Item: {p_dict['name']}\n")
                        link = p_dict.get("link")
                        if link:
                            if "weidian.com" in link or "taobao.com" in link or "1688.com" in link or "youshop10.com" in link:
                                kako_link = f"https://www.kakobuy.com/item/details?url={link}"
                                f.write(f"Kakobuy/Agent Link: {kako_link}\n")
                            elif "cjdropshipping.com" in link:
                                f.write(f"CJ Dropshipping Link: {link}\n")
                            else:
                                f.write(f"Original/Direct Link: {link}\n")
                        else:
                            f.write("Fulfillment: [No direct link found. If CJ Dropshipping, search by title. If Yupoo, contact seller via WhatsApp.]\n")
                        f.write("\n")
            except Exception as e:
                log(f"  [!] Error generating checkout links: {e}")
            # --------------------------------------------

            log(f"  [*] Product-only generation: {len(campaign_prompts)} shots for '{base_product_name}'")

            for i, prompt in enumerate(campaign_prompts):
                shot_name = shot_types[i] if i < len(shot_types) else f"{i+1:02d}_extra"
                saved = await run_single_generation(model, selected_products, custom_prompt=prompt, campaign_folder=campaign_folder, shot_name=shot_name)
                generation_count += 1
                log("[STATS] Total generations: {}".format(generation_count))
                
                if not saved:
                    log("[!] Generation failed. Breaking campaign sequence.")
                    break
                    
                if i < len(campaign_prompts) - 1:
                    await asyncio.sleep(5)  # Short delay between shots
            
            # Copy original source images to output for storefront display
            folder_path = p_dict.get("folder_path")
            if folder_path:
                copy_source_images(Path(folder_path), campaign_dir)

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
