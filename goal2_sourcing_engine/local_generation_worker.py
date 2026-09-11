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
import httpx
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
OUTPUT_DIR = BASE_DIR / "OUTPUT_READY_FOR_SALE"
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_FILE = BASE_DIR / "worker_log.txt"
MODELS_DIR = BASE_DIR / "models" / "character_sheets"
INPUT_DIR = BASE_DIR / "MANUAL_CURATION"

BAD_IMAGE_KEYWORDS = ("chart", "size", "guide", "grid")

# ── Generation Registry (Primary dedup — replaces fragile .generated marker) ──
GENERATION_REGISTRY_FILE = BASE_DIR / "data" / "generation_registry.json"

def load_generation_registry():
    """Load the generation registry from disk."""
    if GENERATION_REGISTRY_FILE.exists():
        try:
            return json.loads(GENERATION_REGISTRY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_generation_registry(registry):
    """Save the generation registry to disk."""
    GENERATION_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    GENERATION_REGISTRY_FILE.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")

def is_already_generated(product_id, color=""):
    """Check if a product+color combo has already been generated."""
    registry = load_generation_registry()
    reg_key = f"{product_id}_{color.lower().strip()}" if color else product_id
    entry = registry.get(reg_key)
    if entry and entry.get("status") == "complete":
        return True
    return False

def register_generation(product_id, color, campaign_folder, source_folder, shots_count, video_generated=False):
    """Register a completed generation in the registry."""
    registry = load_generation_registry()
    reg_key = f"{product_id}_{color.lower().strip()}" if color else product_id
    registry[reg_key] = {
        "campaign_folder": campaign_folder,
        "generated_at": datetime.now().isoformat(),
        "status": "complete",
        "source_folder": str(source_folder),
        "shots_count": shots_count,
        "video_generated": video_generated
    }
    save_generation_registry(registry)

MIN_DELAY_SECONDS = 15
MAX_DELAY_SECONDS = 30

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
    
    # Import image classifier (lazy load)
    classifier = None
    try:
        from auto_image_classifier import classify_and_rename_images
        classifier = classify_and_rename_images
    except ImportError:
        log("[CLASSIFY] auto_image_classifier not available — using filenames as-is")
    
    # 1. Discover subdirectories (folder-grouped products)
    for subdir in INPUT_DIR.iterdir():
        if subdir.is_dir() and subdir.name not in ("outfit_grid", "_rejected", "__pycache__", "_merged_outfits"):
            # Skip MERGED folders — outfits are handled via warehouse Track 2
            if subdir.name.startswith("MERGED_"):
                continue
            
            # Skip already-generated products (marker file OR registry entry)
            generated_marker = subdir / ".generated"
            if generated_marker.exists():
                continue
            
            # Check generation registry for product_id-based dedup
            meta_file_check = subdir / "metadata.json"
            if meta_file_check.exists():
                try:
                    _meta = json.loads(meta_file_check.read_text(encoding="utf-8"))
                    _pid = _meta.get("product_id", "")
                    _color = _meta.get("color", "")
                    if _pid and is_already_generated(_pid, _color):
                        log(f"  [REGISTRY-DEDUP] Skipping '{subdir.name}' — already in generation registry")
                        continue
                except Exception:
                    pass
            
            # AUTO-CLASSIFY: Run VLM classifier on folders without classification
            classification_file = subdir / "image_classification.json"
            # Skip classification for MERGED folders (they always fail with WinError 3 on color-split)
            is_merged = subdir.name.startswith("MERGED_")
            if classifier and not classification_file.exists() and not is_merged:
                try:
                    meta = {}
                    meta_file = subdir / "metadata.json"
                    if meta_file.exists():
                        meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    
                    log(f"[CLASSIFY] Auto-classifying images in {subdir.name}...")
                    classifier(
                        subdir,
                        weidian_data={"colors": meta.get("colors", []), "title": meta.get("product_name", "")},
                        user_color=meta.get("color", "")
                    )
                except Exception as e:
                    log(f"[CLASSIFY] Classification failed for {subdir.name}: {e}")
            
            images = []
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                images.extend(list(subdir.glob(ext)))
            
            # Filter/Validate images in the folder
            valid_images = []
            for img in images:
                name_lower = img.name.lower()
                if any(bad in name_lower for bad in BAD_IMAGE_KEYWORDS):
                    continue
                if has_validator:
                    check = validate_product_image(str(img))
                    if check.get("valid"):
                        valid_images.append(str(img))
                else:
                    if img.stat().st_size >= 30000:
                        valid_images.append(str(img))
            
            if valid_images:
                # Load metadata if exists
                metadata = {}
                meta_file = subdir / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as mf:
                            metadata = json.load(mf)
                    except Exception:
                        pass
                
                # Load link if exists
                link = metadata.get("link", "")
                link_file = subdir / "link.txt"
                if not link and link_file.exists():
                    try:
                        with open(link_file, "r", encoding="utf-8") as lf:
                            link = lf.read().strip()
                    except Exception:
                        pass

                products.append({
                    "is_folder": True,
                    "folder_path": str(subdir),
                    "folder": subdir,  # Path object for smart prompt routing
                    "name": metadata.get("product_name") or subdir.name,
                    "images": valid_images,
                    "link": link,
                    "metadata": metadata
                })

    # 2. Discover loose files directly in INPUT_DIR root
    with os.scandir(INPUT_DIR) as entries:
        for entry in entries:
            if not entry.is_file():
                continue
            name_lower = entry.name.lower()
            ext = os.path.splitext(name_lower)[1]
            if ext not in ('.png', '.jpg', '.jpeg', '.webp'):
                continue

            if any(bad in name_lower for bad in BAD_IMAGE_KEYWORDS):
                continue

            # ⚡ Performance optimization
            # Why: Avoids N+1 stat calls when querying file size by using `os.scandir()` DirEntry cache
            # What: Replaced glob + pathlib `.stat().st_size` with os.scandir DirEntry
            if has_validator:
                check = validate_product_image(entry.path)
                if not check.get("valid"):
                    continue
            else:
                if entry.stat().st_size < 30000:
                    continue

            products.append({
                "is_folder": False,
                "folder_path": None,
                "name": os.path.splitext(entry.name)[0],
                "images": [entry.path],
                "link": "",
                "metadata": {}
            })
    
    log("[+] Discovered {} structured products".format(len(products)))
    return products

def smart_select_images(p_dict: dict, color_name: Optional[str] = None) -> list:
    """
    Use VLM classification or unified product record data to intelligently select 
    the best images for generation (optionally filtered by a specific color variant).
    """
    folder_path = p_dict.get("folder_path")
    if not folder_path:
        return p_dict["images"][:3]
        
    folder = Path(folder_path)
    
    # ── Color-Specific Selection Heuristics (via product_record.json) ──
    if color_name:
        record_file = folder / "product_record.json"
        if record_file.exists():
            try:
                record = json.loads(record_file.read_text(encoding="utf-8"))
                variants = record.get("variants", {}).get("colors", [])
                
                # Find matching color block
                target_variant = None
                for var in variants:
                    if var.get("english", "").lower() == color_name.lower():
                        target_variant = var
                        break
                        
                if target_variant:
                    yupoo_imgs = target_variant.get("yupoo_images", {})
                    selected_fns = list(yupoo_imgs.get("ad_images", []))
                    
                    if len(selected_fns) < 3:
                        selected_fns.extend(list(yupoo_imgs.get("detail_images", [])))
                        
                    if len(selected_fns) < 3:
                        shared = record.get("shared_assets", {})
                        for chart in shared.get("size_chart", []):
                            selected_fns.append(chart)
                        for tag in shared.get("tag_labels", []):
                            selected_fns.append(tag)
                            
                    matched_paths = []
                    for fn in selected_fns:
                        cand_path = folder / fn
                        if cand_path.exists() and str(cand_path) not in matched_paths:
                            matched_paths.append(str(cand_path))
                        if len(matched_paths) >= 3:
                            break
                            
                    if matched_paths:
                        log(f"  [AUTO-SELECT] Color '{color_name}' picked {len(matched_paths)} images: {[Path(p).name for p in matched_paths]}")
                        return matched_paths
            except Exception as e:
                log(f"  [AUTO-SELECT] Failed to select by color '{color_name}': {e}")

    classification_file = Path(folder_path) / "image_classification.json"
    
    if not classification_file.exists():
        log("  [AUTO-SELECT] No classification data — falling back to first 3 images")
        return p_dict["images"][:3]
    
    try:
        cls_data = json.loads(classification_file.read_text(encoding="utf-8"))
        images = cls_data.get("images", [])
    except Exception as e:
        log(f"  [AUTO-SELECT] Failed to read classification: {e}")
        return p_dict["images"][:3]
    
    if not images:
        return p_dict["images"][:3]
    
    # Filter: only keep product images (exclude junk)
    JUNK_CONTENT_TYPES = {"size_chart", "tag_label", "packaging", "color_swatch", "lifestyle"}
    product_imgs = [
        img for img in images
        if img.get("content_type", "product") not in JUNK_CONTENT_TYPES
    ]
    
    if not product_imgs:
        log("  [AUTO-SELECT] All images classified as non-product — falling back to first 3")
        return p_dict["images"][:3]
    
    # Sort by confidence (highest first)
    product_imgs.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    # Priority selection: pick the best image for each angle
    selected = []
    selected_filenames = set()
    
    # Priority order: front > back > side > three_quarter > detail > any remaining
    ANGLE_PRIORITY = ["front", "back", "side", "three_quarter", "detail_closeup", "flat_lay", "overhead"]
    
    for target_angle in ANGLE_PRIORITY:
        if len(selected) >= 3:
            break
        for img in product_imgs:
            angle = img.get("angle", "unknown")
            fname = img.get("recommended_filename", img.get("original_filename", ""))
            
            # Enforce that primary angles must represent a full garment view (no macro zoom details)
            if target_angle in {"front", "back", "side", "three_quarter", "flat_lay"}:
                if img.get("content_type", "product") not in {"product", "model_shot"}:
                    continue
                    
            if angle == target_angle and fname not in selected_filenames:
                selected.append(img)
                selected_filenames.add(fname)
                break
    
    # If we still have fewer than 2 images, fill with highest-confidence remaining
    if len(selected) < 2:
        for img in product_imgs:
            fname = img.get("recommended_filename", img.get("original_filename", ""))
            if fname not in selected_filenames:
                selected.append(img)
                selected_filenames.add(fname)
            if len(selected) >= 3:
                break
    
    # Map back to actual file paths
    folder = Path(folder_path)
    result_paths = []
    for img in selected:
        # Try recommended_filename first (post-rename), then original_filename
        for key in ["recommended_filename", "original_filename"]:
            candidate = img.get(key, "")
            if candidate:
                # Try with extension if not present
                candidate_path = folder / candidate
                if not candidate_path.suffix:
                    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
                        test_path = folder / (candidate + ext)
                        if test_path.exists():
                            candidate_path = test_path
                            break
                if candidate_path.exists():
                    result_paths.append(str(candidate_path))
                    break
    
    if result_paths:
        angles_selected = [img.get("angle", "?") for img in selected[:len(result_paths)]]
        confidences = [f"{img.get('confidence', 0):.2f}" for img in selected[:len(result_paths)]]
        log(f"  [AUTO-SELECT] Smart-picked {len(result_paths)} images: {angles_selected} (confidence: {confidences})")
        return result_paths
    
    # Final fallback
    log("  [AUTO-SELECT] Could not resolve file paths — falling back to first 3 images")
    return p_dict["images"][:3]

def select_front_back_images(p_dict: dict, color_name: Optional[str] = None, part: str = None) -> dict:
    """Select front and back product images for gallery flat lay display.
    
    Returns a dict with 'front' and 'back' keys pointing to image file paths.
    These images are copied directly to the output campaign folder as flat lays
    (no AI generation needed — they ARE the flat lays).
    
    Args:
        part: For sets, 'top' or 'bottom' to label the flat lay files correctly.
    """
    folder_path = p_dict.get("folder_path")
    if not folder_path:
        return {"front": None, "back": None}
    
    folder = Path(folder_path)
    front_img = None
    back_img = None
    
    # Strategy 1: Use product_record.json color-specific images
    if color_name:
        record_file = folder / "product_record.json"
        if record_file.exists():
            try:
                record = json.loads(record_file.read_text(encoding="utf-8"))
                variants = record.get("variants", {}).get("colors", [])
                for var in variants:
                    if var.get("english", "").lower() == color_name.lower():
                        yupoo_imgs = var.get("yupoo_images", {})
                        ad_imgs = yupoo_imgs.get("ad_images", [])
                        # First ad image = front, second = back
                        if len(ad_imgs) >= 1:
                            p = folder / ad_imgs[0]
                            if p.exists():
                                front_img = str(p)
                        if len(ad_imgs) >= 2:
                            p = folder / ad_imgs[1]
                            if p.exists():
                                back_img = str(p)
                        break
            except Exception as e:
                log(f"  [FLAT-LAY] Failed to read product record for front/back: {e}")
    
    # Strategy 2: Use image_classification.json angle data
    if not front_img:
        cls_file = folder / "image_classification.json"
        if cls_file.exists():
            try:
                cls_data = json.loads(cls_file.read_text(encoding="utf-8"))
                for img in cls_data.get("images", []):
                    # STRICT RULE: Must be a product photo (never size chart, tag, or packaging)
                    content_type = img.get("content_type", "").lower()
                    if content_type in ("size_chart", "tag_label", "packaging", "detail_closeup", "non_product"):
                        continue
                    if content_type and content_type != "product":
                        continue

                    angle = img.get("angle", "").lower()
                    fname = img.get("recommended_filename") or img.get("original_filename", "")
                    if not fname:
                        continue

                    # Extra safety: Never allow size, chart, tag, label in filename
                    fname_lower = fname.lower()
                    if any(bad in fname_lower for bad in ("size", "chart", "guide", "tag", "label", "grid")):
                        continue

                    fpath = folder / fname
                    if not fpath.exists():
                        # Try adding extensions
                        for ext in [".jpg", ".jpeg", ".png"]:
                            test = folder / (fname + ext)
                            if test.exists():
                                fpath = test
                                break
                    if not fpath.exists():
                        continue
                    if angle in ("front", "flat_lay") and not front_img:
                        front_img = str(fpath)
                    elif angle == "back" and not back_img:
                        back_img = str(fpath)
                    if front_img and back_img:
                        break
            except Exception:
                pass
    
    # Collect ALL front and back angle files (up to 2 each)
    fronts = []
    backs = []
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        name_lower = f.stem.lower()
        if any(bad in name_lower for bad in ("size", "chart", "guide", "tag", "label", "grid")):
            continue
        if "front_angle" in name_lower or "flat_lay_1" in name_lower:
            fronts.append(str(f))
        elif "back_angle" in name_lower or "flat_lay_2" in name_lower:
            backs.append(str(f))

    if fronts and not front_img:
        front_img = fronts[0]
    if backs and not back_img:
        back_img = backs[0]
        
    # Final fallback: use first two product images from p_dict, filtering out non-garment keywords
    clean_p_images = [
        img for img in p_dict.get("images", [])
        if not any(bad in Path(img).stem.lower() for bad in ("size", "chart", "guide", "tag", "label", "grid"))
    ]
    if not front_img and clean_p_images:
        front_img = clean_p_images[0]
        if front_img not in fronts:
            fronts.insert(0, front_img)
    if not back_img and len(clean_p_images) >= 2:
        back_img = clean_p_images[1]
        if back_img not in backs:
            backs.insert(0, back_img)
    
    log(f"  [FLAT-LAY] Fronts ({len(fronts[:2])}): {[Path(p).name for p in fronts[:2]]} | Backs ({len(backs[:2])}): {[Path(p).name for p in backs[:2]]}")
    return {"front": front_img, "fronts": fronts[:2], "back": back_img, "backs": backs[:2]}


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
            "imageAspectRatio": "IMAGE_ASPECT_RATIO_PORTRAIT",
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

async def fetch_fresh_tokens(wait_forever: bool = True) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Fetch fresh bearer, recaptcha, projectId, and authUser from the bridge.
    If wait_forever is True, smoothly pauses and polls until Flow is open in the browser
    and fresh tokens are pushed by the extension, then automatically resumes execution.
    """
    log("[*] Querying local token bridge for active session tokens...")
    poll_count = 0
    while True:
        poll_count += 1
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
                        log(f"[BRIDGE] Retrieved active tokens (age: {data.get('age_seconds', 0)}s)! Resuming queue...")
                        return bearer, recaptcha, project_id, auth_user
                elif resp.status_code == 503:
                    if poll_count % 4 == 1:
                        log(f"[QUEUE] Flow tokens stale/missing. Pausing queue and waiting for Flow tab in browser (poll #{poll_count})...")
                else:
                    if poll_count % 4 == 1:
                        log(f"[BRIDGE] Bridge returned status {resp.status_code}")
        except Exception as e:
            if poll_count % 4 == 1:
                log(f"[QUEUE] Flow bridge offline on port 9877 ({e}). Pausing queue until bridge connects...")
        
        if not wait_forever and poll_count >= 5:
            return None, None, None, None
            
        await asyncio.sleep(5.0)


# ─── SINGLE JOB ───

async def run_single_generation(model, product_paths, custom_prompt=None, campaign_folder=None, shot_name=None, on_model=True):
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
    try:
        from smart_router import detect_needs_vton
        needs_simple = detect_needs_vton(product_name, product_paths[0])
    except ImportError:
        needs_simple = False
    
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
            skip_model = (not on_model) or any(marker in prompt_lower for marker in [
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

                    # 3. Product Match Fidelity Gate (VLM verifies model wears the exact source product)
                    if product_paths and os.path.exists(str(product_paths[0])):
                        ref_img = str(product_paths[0])
                        match_result = evaluator.evaluate_vton_match(ref_img, img_path)
                        if not match_result.get("passed", True):
                            log("  ❌ Fidelity Gate REJECTED {}: Garment does not match source ({})".format(
                                Path(img_path).name, match_result.get("reason", "Garment mismatch")
                            ))
                            evaluator._delete_bad_image(img_path)
                            all_passed = False
                            break
                        else:
                            log("  ✅ Fidelity Gate PASSED: Generated photo matches source garment")
                
                if all_passed:
                    log("[OK] Quality Gate passed! {} images saved.".format(len(saved)))
                    return saved
                else:
                    saved = []
            
            log("[!] Quality Gate failed after 3 attempts.")
            return []

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            body = e.response.text[:300]
            log("[!] HTTP Error {}: {}".format(status, body))
            
            # Retry on reCAPTCHA (403) or auth (401) failures — tokens are single-use
            if status in (403, 401):
                for retry in range(1, 4):
                    wait_secs = 15 + (retry * 5)  # 20s, 25s, 30s
                    log(f"  [RETRY] Waiting {wait_secs}s for fresh token (attempt {retry}/3)...")
                    await asyncio.sleep(wait_secs)
                    
                    bearer, recaptcha, project_id, auth_user = await fetch_fresh_tokens()
                    if not bearer or not recaptcha:
                        log(f"  [RETRY] No fresh tokens available. Skipping retry {retry}.")
                        continue
                    
                    headers["Authorization"] = f"Bearer {bearer}"
                    headers["X-Goog-AuthUser"] = auth_user
                    
                    try:
                        log(f"  [RETRY] Re-generating with fresh token...")
                        result = await generate_image(client, prompt, asset_ids, headers, project_id, recaptcha)
                        saved = save_generated_images(result, model["id"], product_name, product_paths, campaign_folder, shot_name)
                        if saved:
                            log(f"  [RETRY] Success on retry {retry}! {len(saved)} images saved.")
                            return saved
                        else:
                            log(f"  [RETRY] Generation returned no images on retry {retry}.")
                    except httpx.HTTPStatusError as retry_err:
                        log(f"  [RETRY] HTTP {retry_err.response.status_code} on retry {retry}: {retry_err.response.text[:200]}")
                        continue
                    except Exception as retry_err:
                        log(f"  [RETRY] Error on retry {retry}: {retry_err}")
                        continue
                
                log("[!] All retries exhausted. Generation failed.")
            return []
        except Exception as e:
            log("[!] Generation error: {}".format(e))
            traceback.print_exc()
            return []



def copy_source_images(curation_dir: Path, output_dir: Path, front_back: dict = None, part: str = None):
    """Copy original Yupoo/Weidian source photos and metadata JSON files to output alongside AI shots.
    
    Args:
        front_back: Dict with 'front' and 'back' image paths for gallery flat lays.
        part: For sets, 'top' or 'bottom' to prefix flat lay filenames (e.g. top_front_flat_lay.jpg).
    """
    import shutil
    source_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    source_prefixes = ('front_angle', 'back_angle', 'side_angle', 'angle_', 'detail_close', 'size_chart', 'tag_label', 'flat_lay')
    
    if not curation_dir.exists():
        log(f"  [!] Source image dir not found: {curation_dir}")
        return
    
    try:
        # Copy source images
        for f in curation_dir.iterdir():
            if f.suffix.lower() in source_extensions and any(f.stem.startswith(p) for p in source_prefixes):
                dest = output_dir / f"source_{f.name}"
                if not dest.exists():
                    shutil.copy2(str(f), str(dest))
                    log(f"  [+] Copied source image: {f.name}")
                    
        # Copy metadata JSON files (critical for storefront uploader)
        for json_name in ("product_record.json", "metadata.json"):
            json_file = curation_dir / json_name
            if json_file.exists():
                shutil.copy2(str(json_file), str(output_dir / json_name))
                log(f"  [+] Copied metadata file: {json_name}")

        # Copy front/back images with gallery-ready names for storefront flat lay display
        # For sets: prefix with part name (e.g. top_front_flat_lay.jpg, bottom_back_flat_lay.jpg)
        if front_back:
            prefix = f"{part}_" if part else ""
            if front_back.get("front"):
                front_src = Path(front_back["front"])
                if front_src.exists():
                    dest = output_dir / f"{prefix}front_flat_lay{front_src.suffix}"
                    if not dest.exists():
                        shutil.copy2(str(front_src), str(dest))
                        log(f"  [+] Copied gallery flat lay {prefix.upper()}FRONT: {front_src.name}")
            if front_back.get("back"):
                back_src = Path(front_back["back"])
                if back_src.exists():
                    dest = output_dir / f"{prefix}back_flat_lay{back_src.suffix}"
                    if not dest.exists():
                        shutil.copy2(str(back_src), str(dest))
                        log(f"  [+] Copied gallery flat lay {prefix.upper()}BACK: {back_src.name}")
    except Exception as e:
        log(f"  [!] Error copying source images/metadata: {e}")


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
    # Collect ALL flat lay views (front, back, detail, angles) for each product item
    outfit_items = outfit_config.get('products') or outfit_config.get('items', [])
    all_product_paths = []
    item_views_map = []  # List of dicts: {'item': item, 'front': path, 'all_views': [paths]}

    for item_idx, item in enumerate(outfit_items):
        item_dir = None
        if 'folder_path' in item:
            item_dir = Path(item['folder_path'])
        elif 'path' in item:
            item_dir = Path(item['path'])
        elif 'front_image' in item:
            img_p = Path(item['front_image'])
            if img_p.exists():
                item_dir = img_p.parent
        
        views = []
        hero_img = None
        # Patterns to EXCLUDE from generation references (not actual product flat lays)
        _EXCLUDE_PATTERNS = {'SIZE_CHART', 'OTHER', 'OUTFIT_COMBINED', 'size_chart', 'source_'}
        if item_dir and item_dir.exists():
            for f in sorted(item_dir.iterdir()):
                if f.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
                    continue
                # Skip non-product images by name pattern (VLM classification labels in filename)
                fname_upper = f.name.upper()
                if any(pat.upper() in fname_upper for pat in _EXCLUDE_PATTERNS):
                    log(f"  [OUTFIT-FILTER] Skipping non-product image: {f.name}")
                    continue
                views.append(str(f))
                if not hero_img and ('front' in f.name.lower() or 'flat_lay' in f.name.lower()):
                    hero_img = str(f)
            if not hero_img and views:
                hero_img = views[0]
        elif 'front_image' in item and os.path.isfile(item['front_image']):
            hero_img = str(item['front_image'])
            views = [hero_img]
        
        if hero_img:
            # Deduplicate: if this hero is already in all_product_paths (e.g. set top+bottom share same image),
            # still add it so item count is correct, but log a warning
            if hero_img in all_product_paths:
                log(f"  [OUTFIT-DEDUP] Hero image '{os.path.basename(hero_img)}' already in product paths (set sharing same image)")
            all_product_paths.append(hero_img)
            item_views_map.append({'item': item, 'hero': hero_img, 'views': views})
    
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
    
    # Copy ALL source flat lay image views (front, back, detail, side) to outfit folder
    import shutil
    for idx, v_info in enumerate(item_views_map):
        cat_label = "top" if idx == 0 else ("bottom" if idx == 1 else f"item_{idx+1}")
        for view_path in v_info['views']:
            v_name = Path(view_path).name
            dest_name = f"00_source_{cat_label}_{v_name}"
            try:
                shutil.copy2(view_path, str(outfit_dir / dest_name))
                log(f"  [OUTFIT-SOURCE] Copied {cat_label} view: {v_name}")
            except Exception as copy_err:
                log(f"  [OUTFIT] Error copying source view {view_path}: {copy_err}")
    
    # Use FULL_OUTFIT_PROMPTS — explicitly references Top (ref 2) AND Bottom (ref 3) together
    from prompt_library import FULL_OUTFIT_PROMPTS
    
    outfit_prompts_to_use = {}
    for k, p in list(FULL_OUTFIT_PROMPTS.items())[:3]:
        adapted = p
        if gender == 'male':
            adapted = adapted.replace("of her wearing", "of him wearing").replace("her wearing", "him wearing").replace("She ", "He ").replace("her ", "his ")
        # Append strict anti-hallucination directive
        adapted += " IMPORTANT: Do NOT add any third-party logos, trefoils, swooshes, or brand trademarks not present in the reference images. Replicate the EXACT color, patterns, and logo-free design from the reference images."
        outfit_prompts_to_use[k] = adapted
    
    results = []
    for shot_idx, (shot_name, prompt) in enumerate(outfit_prompts_to_use.items()):
        saved = await run_single_generation(
            model, all_product_paths, 
            custom_prompt=prompt, 
            campaign_folder=str(outfit_dir),
            shot_name=f"outfit_{shot_name}"
        )
        results.extend(saved)
        if shot_idx < 2:
            await asyncio.sleep(1)

    # ── 1 OMNI FLASH 10s UGC VIDEO FOR MERGED OUTFIT ──
    try:
        log(f"  [OUTFIT-VIDEO] Generating 10s Omni Flash UGC video for merged outfit...")
        
        # Build a product-aware prompt from the actual outfit items instead of generic branding
        top_name = ""
        bottom_name = ""
        for item in outfit_items:
            cat = item.get("category", "").lower()
            pname = item.get("product_name", "")
            if cat == "top" and pname:
                top_name = pname
            elif cat == "bottom" and pname:
                bottom_name = pname
        
        # Describe what the garments actually are from the metadata
        if top_name and bottom_name:
            garment_desc = f"the {top_name} on top and the {bottom_name} on the bottom"
        elif top_name:
            garment_desc = f"the {top_name} with matching bottoms"
        elif bottom_name:
            garment_desc = f"a matching top with the {bottom_name}"
        else:
            garment_desc = "the complete top and bottom outfit"
        
        outfit_video_prompt = (
            f"Vertical 9:16 full-length mirror selfie video of a model wearing this exact complete outfit from the reference images — {garment_desc} shown together as one coordinated look. "
            "The model steps back slowly to reveal the full silhouette from head to toe, then adjusts the collar and touches the fabric to show the texture and weight of both garments. "
            f"Speaking directly to camera: 'This outfit combination is actually perfect... look at how the top and bottom just work together, the fit is so clean.' "
            "10-second organic TikTok Reels UGC video, clear native voiceover with synchronized lip movement, authentic room lighting, raw 2026 UGC aesthetic."
        )
        
        from generation_router import GenerationRouter
        router = GenerationRouter()
        video_result = await router.generate_video(
            prompt=outfit_video_prompt,
            ref_image_paths=all_product_paths,
            aspect="9:16",
            output_prefix=f"outfit_{outfit_name}_ugc",
            video_model="omni_flash"
        )
        if video_result:
            import shutil
            video_src = video_result if isinstance(video_result, str) else video_result[0]
            video_dest = outfit_dir / "02_outfit_ugc_video.mp4"
            if os.path.exists(video_src):
                shutil.copy2(video_src, str(video_dest))
                log(f"  [OUTFIT-VIDEO] Omni Flash UGC outfit video saved: {video_dest.name}")
            else:
                log(f"  [OUTFIT-VIDEO] Video source file not found: {video_src}")
        else:
            log(f"  [OUTFIT-VIDEO] Omni Flash UGC outfit video generation failed.")
    except Exception as vid_err:
        log(f"  [OUTFIT-VIDEO] Error generating outfit video: {vid_err}")
    
    return results

async def process_product(p_dict: dict, model: dict, generation_count: int, video_done_item_ids: set = None) -> int:
    """Helper function to run the full ad generation sequence for a single product."""
    # ── GUARDRAIL GATE: Verify product exists before any generation ──
    try:
        from generation_guardrails import guardrails
        folder_path = p_dict.get("folder_path", "")
        if folder_path:
            exists_ok, exists_violations = guardrails.validate_product_exists(
                product_name=p_dict.get("name", "unknown"),
                product_folder=folder_path
            )
            if not exists_ok:
                for v in exists_violations:
                    log(f"  [!] GUARDRAIL BLOCKED: {v}")
                return 0
    except ImportError:
        pass  # Guardrails module not yet available

    # Check if unified product record exists
    record_file = Path(p_dict.get("folder_path", "")) / "product_record.json"
    colors_to_process = [None] # Default: single run without color name
    if record_file.exists():
        try:
            record_data = json.loads(record_file.read_text(encoding="utf-8"))
            color_variants = record_data.get("variants", {}).get("colors", [])
            if color_variants:
                colors_to_process = [c.get("english") for c in color_variants if c.get("english")]
        except Exception as e:
            log(f"  [COLOR-GEN] Failed to read product record colors: {e}")

    # ── VIDEO CREDIT OPTIMIZATION ──
    # Only 1 UGC video per product (videos cost credits, images are free)
    # User can set video_color in metadata via Discord; otherwise prefer black/green
    video_generated = False
    # Check if another color variant of this product already got a video this cycle
    item_id = (p_dict.get("metadata") or {}).get("item_id", "")
    if video_done_item_ids and item_id and item_id in video_done_item_ids:
        video_generated = True  # Skip video — already done for another color of same product
        log(f"  [VIDEO-PLAN] Skipping video — already generated for item_id {item_id}")
    metadata = p_dict.get("metadata", {})
    video_color_pref = metadata.get("video_color", "").lower().strip()
    if not video_color_pref:
        # Auto-pick: prefer black, then green, then first available
        preferred = ["black", "green", "dark"]
        for pref in preferred:
            for c in colors_to_process:
                if c and pref in c.lower():
                    video_color_pref = c.lower()
                    break
            if video_color_pref:
                break
        if not video_color_pref and colors_to_process:
            video_color_pref = (colors_to_process[0] or "default").lower()
    log(f"  [VIDEO-PLAN] Video color: '{video_color_pref}' (1 video per product to save credits)")

    for target_color in colors_to_process:
        if target_color:
            log(f"  [COLOR-GEN] Starting campaign generation for color: '{target_color}'")
        
        selected_products = smart_select_images(p_dict, color_name=target_color)  # VLM-powered smart selection (color-aware!)
        
        # Select front/back images for gallery flat lay display (no AI generation needed)
        # For sets, detect part (top/bottom) for proper file labeling
        product_part = (p_dict.get("metadata", {}).get("part") or "").lower() or None
        front_back = select_front_back_images(p_dict, color_name=target_color, part=product_part)
        
        # For model_front shots, prefer ALL front product images (up to 2) as Flow references
        # (e.g. 1 full garment view + 1 close-up for text/logo precision!)
        front_refs = front_back.get("fronts", [])
        if front_refs:
            selected_products = front_refs
            log(f"  [MODEL] Using {len(selected_products)} front image(s) as Flow reference: {[Path(p).name for p in selected_products]}")
        elif front_back.get("front"):
            selected_products = [front_back["front"]]
            
        selected_products_dicts = [p_dict]
        base_product_name = p_dict["name"].split(".")[0]
        distinct_product_count = 1
        
        # Determine product category for shot plan
        metadata = p_dict.get("metadata", {})
        category = (metadata.get("category") or metadata.get("product_category") or "").lower()

        # Check image classification garment_type and product folder name
        cls_garment_type = ""
        classification_file = Path(p_dict.get("folder", "")) / "image_classification.json"
        if classification_file.exists():
            try:
                cls_data = json.loads(classification_file.read_text(encoding="utf-8"))
                cls_garment_type = (cls_data.get("product_summary", {}).get("garment_type") or "").lower()
            except Exception:
                pass

        combined_cat_text = f"{category} {cls_garment_type} {base_product_name.lower()}".lower()
        is_set_flag = metadata.get("is_set", False) or category == "set"
        # Also detect sets from product name (e.g. "NOCTA HOODIE TROUSERS", "Tracksuit")
        if not is_set_flag:
            name_lower = base_product_name.lower()
            set_patterns = [
                ("hoodie", "trouser"), ("hoodie", "pant"), ("hoodie", "jogger"),
                ("jacket", "trouser"), ("jacket", "pant"), ("jacket", "jogger"),
                ("top", "bottom"), ("sweater", "pant"), ("fleece", "pant"),
            ]
            for a, b in set_patterns:
                if a in name_lower and b in name_lower:
                    is_set_flag = True
                    log(f"  [SET-DETECT] Detected set from name: '{base_product_name}' (matched {a}+{b})")
                    break
            if not is_set_flag and any(kw in name_lower for kw in ["tracksuit", "set ", " set", "outfit"]):
                is_set_flag = True
                log(f"  [SET-DETECT] Detected set from keyword in name: '{base_product_name}'")
        
        # Map common category names to shot plan keys
        if any(k in combined_cat_text for k in ["shoe", "sneaker", "boot", "trainer", "dunk", "jordan", "runner", "bapesta", "yeezy", "slide", "loaf", "footwear"]):
            shot_category = "shoes"
        elif any(k in combined_cat_text for k in ["top", "hoodie", "jacket", "tee", "shirt", "sweater", "cardigan", "crewneck", "fleece", "knit"]):
            shot_category = "tops"
        elif any(k in combined_cat_text for k in ["bottom", "pant", "trouser", "jogger", "short", "denim", "jean", "sweatpant"]):
            shot_category = "bottoms"
        elif any(k in combined_cat_text for k in ["bag", "backpack", "tote", "duffle"]):
            shot_category = "bags"
        elif any(k in combined_cat_text for k in ["accessory", "watch", "chain", "ring", "sunglasses", "glasses", "necklace", "belt", "hat", "cap", "beanie"]):
            shot_category = "accessories"
        elif any(k in combined_cat_text for k in ["beauty", "fragrance", "skincare", "perfume"]):
            shot_category = "beauty"
        else:
            shot_category = "clothing"  # Default fallback
        
        shot_plan = get_prompts_for_product(shot_category, is_set=is_set_flag)
        
        log(f"  [ROUTE] Category: {shot_category} (detected from '{combined_cat_text[:40]}...') | Is Set: {is_set_flag} | On-Model: {shot_plan['on_model']}")

        # SMART PROMPT ROUTING: Read image classification to match prompts with available angles
        classification_file = Path(p_dict.get("folder", "")) / "image_classification.json"
        has_back = True  # Default: assume all angles available
        has_detail = False
        has_front = True
        if classification_file.exists():
            try:
                cls_data = json.loads(classification_file.read_text(encoding="utf-8"))
                cls_summary = cls_data.get("product_summary", {})
                has_front = cls_summary.get("has_front", True)
                has_back = cls_summary.get("has_back", False)
                has_detail = cls_summary.get("has_detail", False)
                log(f"  [SMART] Image classification found: front={has_front} back={has_back} detail={has_detail}")
            except Exception:
                pass

        # Filter shot plan based on available image angles
        filtered_shots = []
        for prompt_dict, shot_key in shot_plan["product_shots"]:
            # Skip ghost mannequin back-view if no back image exists
            if shot_key == "ghost_mannequin" and not has_back:
                # Only include front-facing ghost mannequin prompts
                front_only = {k: v for k, v in prompt_dict.items() if "back" not in k.lower()}
                if front_only:
                    filtered_shots.append((front_only, shot_key))
                else:
                    filtered_shots.append((prompt_dict, shot_key))
            # Include detail closeup only if we have detail source images
            elif shot_key == "detail" and not has_detail:
                log(f"  [SMART] Skipping detail closeup (no detail source images)")
                continue
            else:
                filtered_shots.append((prompt_dict, shot_key))

        log(f"  [ROUTE] Shot plan: {len(filtered_shots)} shots (filtered from {len(shot_plan['product_shots'])})")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize base_product_name to be a safe folder name
        import re as _re
        safe_product_name = _re.sub(r'[^\w\s-]', '', base_product_name).strip().replace(' ', '_')
        color_suffix = f"_{target_color.lower().strip().replace(' ', '_')}" if target_color else ""
        
        # Include product_id for deterministic pipeline tracking
        product_id = metadata.get("product_id", "")
        pid_suffix = f"_{product_id}" if product_id else ""
        campaign_folder = f"{ts}_{model['id']}_{safe_product_name[:30]}{pid_suffix}{color_suffix}"
        
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

        if not filtered_shots:
            log(f"  [ROUTE] No AI generation needed — source flat lays only for '{base_product_name}'")
            # Skip AI generation, just copy source images with gallery-ready flat lays
            folder_path = p_dict.get("folder_path")
            if folder_path:
                copy_source_images(Path(folder_path), campaign_dir, front_back=front_back, part=product_part)
            
            # Stage front image in warehouse for outfit assembly (top/bottom only)
            if front_back.get("front") and shot_category in ("tops", "bottoms", "shoes"):
                try:
                    from outfit_warehouse import stage_item
                    warehouse_cat = {"tops": "top", "bottoms": "bottom", "shoes": "shoe"}.get(shot_category, shot_category)
                    brand_name = metadata.get("brand_name") or metadata.get("brand") or "Unknown"
                    if brand_name.lower() in ("unknown", "n/a", ""):
                        brand_name = base_product_name.split("_")[0]  # Best guess from product name
                    stage_item(
                        product_name=base_product_name,
                        brand=brand_name,
                        category=warehouse_cat,
                        color=target_color or "Default",
                        front_image_path=front_back["front"],
                        metadata={"gender": model.get("gender", "male"), "folder_path": str(folder_path)}
                    )
                except Exception as e:
                    log(f"  [WAREHOUSE] Failed to stage item: {e}")
            
            # ── MULTI-STYLE ON-MODEL EDITORIAL SUITE (Photos are 100% Free on Flow!) ──
            # Generate 3 distinct editorial lookbook styles for EVERY color variant
            if shot_category in ("tops", "bottoms", "clothing") and front_back.get("front"):
                try:
                    from prompt_library import CLOTHING_PROMPTS, MALE_UGC_PROMPTS
                    on_model_prompts = MALE_UGC_PROMPTS if model.get("gender") == "male" else CLOTHING_PROMPTS
                    
                    # Pool of 45+ premium lifestyle & editorial scenes — 6 shots per color (images are FREE!)
                    excluded_flatlay_keys = {"flat_lay_editorial_dark", "flat_lay_street_culture", "simple_vton_grwm", "simple_vton_mirror", "simple_vton_street"}
                    available_keys = [
                        k for k in CLOTHING_PROMPTS.keys()
                        if k not in excluded_flatlay_keys and isinstance(CLOTHING_PROMPTS[k], str) and len(CLOTHING_PROMPTS[k]) > 50
                    ]
                    if "mirror_selfie" in available_keys:
                        available_keys.remove("mirror_selfie")
                    
                    # Always include mirror_selfie (proven winner), then 5 random picks from the 45+ scene pool
                    selected_keys = ["mirror_selfie"] + random.sample(available_keys, min(5, len(available_keys)))
                    styles_to_run = [
                        (key, f"{idx+1:02d}_on_model_{key}")
                        for idx, key in enumerate(selected_keys)
                    ]
                    
                    for prompt_key, shot_name in styles_to_run:
                        if prompt_key in on_model_prompts:
                            prompt_text = on_model_prompts[prompt_key]
                        elif prompt_key in CLOTHING_PROMPTS:
                            prompt_text = CLOTHING_PROMPTS[prompt_key]
                        else:
                            prompt_text = random.choice(list(on_model_prompts.values()))
                            
                        log(f"  [ON-MODEL-SUITE] Generating on-model shot ({prompt_key}) for color '{target_color or 'default'}'...")
                        saved = await run_single_generation(
                            model, [front_back["front"]],
                            custom_prompt=prompt_text,
                            campaign_folder=campaign_folder,
                            shot_name=shot_name,
                            on_model=True
                        )
                        generation_count += 1
                        if saved:
                            log(f"  [ON-MODEL-SUITE] Saved: {[Path(s).name for s in saved]}")
                        else:
                            log(f"  [ON-MODEL-SUITE] Failed for {prompt_key}.")
                        await asyncio.sleep(1)
                except Exception as onm_err:
                    log(f"  [ON-MODEL-SUITE] Error generating on-model suite: {onm_err}")
            
            # ── OMNI FLASH UGC SELFIE VIDEO (Track 2 — No-Shots Path) ──
            # Only 1 video per product — check if this is the designated video color
            target_lower = (target_color or "default").lower()
            is_video_color = (not video_generated) and (video_color_pref in target_lower or target_lower in video_color_pref or not target_color)
            if shot_category in ("tops", "bottoms", "clothing") and front_back.get("front") and is_video_color:
                try:
                    from prompt_library import OBSCURA_SELFIE_UGC_AD_PROMPTS
                    category_prompt_map = {
                        "tops": ["selfie_fit_check_speech", "fabric_quality_test", "restock_car_unboxing"],
                        "bottoms": ["pants_cargo_stack_pov", "outfit_3way_transition"],
                        "clothing": ["selfie_fit_check_speech", "fabric_quality_test", "restock_car_unboxing"],
                    }
                    valid_keys = [k for k in category_prompt_map.get(shot_category, ["selfie_fit_check_speech"])
                                  if k in OBSCURA_SELFIE_UGC_AD_PROMPTS]
                    if not valid_keys:
                        valid_keys = list(OBSCURA_SELFIE_UGC_AD_PROMPTS.keys())
                    
                    ugc_key = random.choice(valid_keys)
                    ugc_prompt = OBSCURA_SELFIE_UGC_AD_PROMPTS[ugc_key]
                    
                    log(f"  [UGC-VIDEO] Generating 10s Omni Flash UGC selfie video ({ugc_key})...")
                    
                    from generation_router import GenerationRouter
                    router = GenerationRouter()
                    video_result = await router.generate_video(
                        prompt=ugc_prompt,
                        ref_image_paths=[front_back["front"]],
                        aspect="9:16",
                        output_prefix=f"{safe_product_name}_ugc",
                        video_model="omni_flash"
                    )
                    
                    if video_result:
                        import shutil
                        video_src = video_result if isinstance(video_result, str) else video_result[0]
                        video_dest = campaign_dir / f"02_ugc_selfie_{ugc_key}.mp4"
                        if os.path.exists(video_src):
                            shutil.copy2(video_src, str(video_dest))
                            log(f"  [UGC-VIDEO] Omni Flash UGC video saved: {video_dest.name}")
                        else:
                            log(f"  [UGC-VIDEO] Video source file not found: {video_src}")
                    else:
                        log(f"  [UGC-VIDEO] Omni Flash UGC video generation failed.")
                    video_generated = True  # Only attempt once per product
                    if video_done_item_ids is not None and item_id:
                        video_done_item_ids.add(item_id)
                except Exception as ugc_err:
                    log(f"  [UGC-VIDEO] Error generating UGC video: {ugc_err}")
            
            continue

        # Build prompts from the filtered shot plan
        campaign_prompts = []
        shot_types = []
        for prompt_dict, shot_key in filtered_shots:
            # For model_front shots, swap to male-specific prompts if model is male
            if shot_key == "model_front" and model.get("gender") == "male":
                from prompt_library import MALE_MODEL_FRONT_PROMPTS
                prompt_dict = MALE_MODEL_FRONT_PROMPTS
            # Pick a random prompt from each dict
            prompt_key = random.choice(list(prompt_dict.keys()))
            prompt_text = prompt_dict[prompt_key]
            campaign_prompts.append(prompt_text)
            shot_types.append(f"{len(shot_types)+1:02d}_{shot_key}")

        log(f"  [*] Product-only generation: {len(campaign_prompts)} shots for '{base_product_name}'")

        for i, prompt in enumerate(campaign_prompts):
            shot_name = shot_types[i] if i < len(shot_types) else f"{i+1:02d}_extra"
            saved = await run_single_generation(model, selected_products, custom_prompt=prompt, campaign_folder=campaign_folder, shot_name=shot_name, on_model=shot_plan["on_model"])
            generation_count += 1
            log("[STATS] Total generations: {}".format(generation_count))
            
            if not saved:
                log("[!] Generation failed. Breaking campaign sequence.")
                break
                
            if i < len(campaign_prompts) - 1:
                await asyncio.sleep(1)  # Minimal delay between shots
        
        # ── SINGULAR EDITORIAL SHOT RULES ──
        # Bottoms / Pants / Cargos: NO ON-MODEL. Creative architectural flat lay only.
        # Tops / Hoodies / Jackets: Tight close-range waist-up crop focusing on collar/drape.
        if shot_category == "bottoms" and not is_set_flag:
            try:
                from prompt_library import BOTTOMS_CREATIVE_FLAT_LAY_PROMPTS
                flat_key = random.choice(list(BOTTOMS_CREATIVE_FLAT_LAY_PROMPTS.keys()))
                flat_prompt = BOTTOMS_CREATIVE_FLAT_LAY_PROMPTS[flat_key]
                log(f"  [BOTTOMS-FLAT-LAY] Generating creative luxury flat lay ({flat_key})...")
                saved = await run_single_generation(
                    model, selected_products,
                    custom_prompt=flat_prompt,
                    campaign_folder=campaign_folder,
                    shot_name=f"01_creative_flat_lay_{flat_key}",
                    on_model=False
                )
                generation_count += 1
                if saved:
                    log(f"  [BOTTOMS-FLAT-LAY] Creative flat lay saved: {[Path(s).name for s in saved]}")
                else:
                    log(f"  [BOTTOMS-FLAT-LAY] Creative flat lay failed.")
            except Exception as b_err:
                log(f"  [BOTTOMS-FLAT-LAY] Error generating bottoms flat lay: {b_err}")
                
        elif shot_category in ("tops", "clothing") and not is_set_flag:
            try:
                from prompt_library import TOPS_CLOSE_RANGE_PROMPTS
                top_key = random.choice(list(TOPS_CLOSE_RANGE_PROMPTS.keys()))
                top_prompt = TOPS_CLOSE_RANGE_PROMPTS[top_key]
                is_on_model = "flat_lay" not in top_key
                log(f"  [TOP-SHOT] Generating close-range editorial shot ({top_key}, on_model={is_on_model})...")
                saved = await run_single_generation(
                    model, selected_products,
                    custom_prompt=top_prompt,
                    campaign_folder=campaign_folder,
                    shot_name=f"01_top_close_{top_key}",
                    on_model=is_on_model
                )
                generation_count += 1
                if saved:
                    log(f"  [TOP-SHOT] Top close shot saved: {[Path(s).name for s in saved]}")
                else:
                    log(f"  [TOP-SHOT] Top close shot failed.")
            except Exception as top_err:
                log(f"  [TOP-SHOT] Error generating top close shot: {top_err}")
        
        # ── OMNI FLASH UGC SELFIE VIDEO (Track 2) ──
        # Only 1 video per product — check if this is the designated video color
        target_lower = (target_color or "default").lower()
        is_video_color = (not video_generated) and (video_color_pref in target_lower or target_lower in video_color_pref or not target_color)
        if shot_category in ("tops", "bottoms", "clothing", "shoes") and front_back.get("front") and is_video_color:
            try:
                from prompt_library import OBSCURA_SELFIE_UGC_AD_PROMPTS
                # Pick a category-appropriate UGC prompt
                category_prompt_map = {
                    "tops": ["selfie_fit_check_speech", "fabric_quality_test", "restock_car_unboxing"],
                    "bottoms": ["pants_cargo_stack_pov", "outfit_3way_transition"],
                    "shoes": ["sneaker_onfoot_unboxing"],
                    "clothing": ["selfie_fit_check_speech", "fabric_quality_test", "restock_car_unboxing"],
                }
                valid_keys = [k for k in category_prompt_map.get(shot_category, ["selfie_fit_check_speech"])
                              if k in OBSCURA_SELFIE_UGC_AD_PROMPTS]
                if not valid_keys:
                    valid_keys = list(OBSCURA_SELFIE_UGC_AD_PROMPTS.keys())
                
                ugc_key = random.choice(valid_keys)
                ugc_prompt = OBSCURA_SELFIE_UGC_AD_PROMPTS[ugc_key]
                
                log(f"  [UGC-VIDEO] Generating 10s Omni Flash UGC selfie video ({ugc_key})...")
                
                from generation_router import GenerationRouter
                router = GenerationRouter()
                video_result = await router.generate_video(
                    prompt=ugc_prompt,
                    ref_image_paths=[front_back["front"]],
                    aspect="9:16",
                    output_prefix=f"{safe_product_name}_ugc",
                    video_model="omni_flash"
                )
                
                if video_result:
                    # Copy video to campaign folder
                    import shutil
                    video_src = video_result if isinstance(video_result, str) else video_result[0]
                    video_dest = campaign_dir / f"{len(campaign_prompts)+2:02d}_ugc_selfie_{ugc_key}.mp4"
                    if os.path.exists(video_src):
                        shutil.copy2(video_src, str(video_dest))
                        log(f"  [UGC-VIDEO] Omni Flash UGC video saved: {video_dest.name}")
                    else:
                        log(f"  [UGC-VIDEO] Video source file not found: {video_src}")
                else:
                    log(f"  [UGC-VIDEO] Omni Flash UGC video generation failed.")
                video_generated = True  # Only attempt once per product
                if video_done_item_ids is not None and item_id:
                    video_done_item_ids.add(item_id)
            except Exception as ugc_err:
                log(f"  [UGC-VIDEO] Error generating UGC video: {ugc_err}")

        # Copy original source images AND gallery-ready front/back flat lays to output
        folder_path = p_dict.get("folder_path")
        if folder_path:
            copy_source_images(Path(folder_path), campaign_dir, front_back=front_back, part=product_part)
            
    # Mark product as generated so it won't be re-processed next cycle
    folder_path = p_dict.get("folder_path")
    if folder_path:
        # 1. Legacy marker file (backward compat)
        marker = Path(folder_path) / ".generated"
        try:
            marker.write_text(datetime.now().isoformat(), encoding="utf-8")
            log(f"  [DONE] Marked '{p_dict['name']}' as generated")
        except Exception:
            pass
        
        # 2. Update metadata.json generation_status
        meta_update_path = Path(folder_path) / "metadata.json"
        if meta_update_path.exists():
            try:
                meta_data = json.loads(meta_update_path.read_text(encoding="utf-8"))
                meta_data["generation_status"] = "complete"
                meta_data["generation_timestamp"] = datetime.now().isoformat()
                meta_data["campaign_folder"] = campaign_folder
                meta_update_path.write_text(json.dumps(meta_data, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
        
        # 3. Register in generation registry (primary dedup source of truth)
        product_id = metadata.get("product_id", "")
        target_color_final = p_dict.get("color") or ""
        if product_id:
            register_generation(
                product_id=product_id,
                color=target_color_final,
                campaign_folder=campaign_folder,
                source_folder=folder_path,
                shots_count=generation_count,
                video_generated=video_generated if 'video_generated' in dir() else False
            )
            log(f"  [REGISTRY] Registered generation: {product_id}_{target_color_final}")
            
    return generation_count


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
    if not products and not loop_mode:
        log("[!] No products found. Single run mode exiting. Run with --loop to keep worker active.")
        return

    generation_count = 0

    try:
        while True:
            # Re-discover products each cycle (new ones may have been added)
            products = discover_products()
            if not products:
                log("[i] No products in queue. Waiting for new items via Discord pipeline...")
                log("[i] Drop a Weidian/1688/Taobao link in Discord, or add images to MANUAL_CURATION/")
                await asyncio.sleep(120)
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

            # ── DUAL-TRACK GENERATION ROUTING ──
            # Track 1: Individual products get product-only shots + singular on-model + UGC video
            # Track 2: Full outfits (from warehouse) get multi-item on-model shots
            
            # If not in loop mode, process all matched products sequentially
            products_list = matched_products  # Process ALL products every cycle (optimized)
            video_done_ids = set()  # Track item_ids that already got a video this cycle
            for p in products_list:
                generation_count = await process_product(p, model, generation_count, video_done_item_ids=video_done_ids)

            # ── AUTO-GENERATE OUTFIT MODEL SHOTS ──
            # Check warehouse for ready outfits (top + bottom + optional shoe)
            try:
                from outfit_warehouse import find_ready_outfits, mark_outfit_generated
                ready_outfits = find_ready_outfits()
                if ready_outfits:
                    log(f"[OUTFIT] Found {len(ready_outfits)} ready outfit(s) in warehouse")
                    for outfit in ready_outfits:
                        outfit_name = outfit.get("name", "Unknown Outfit")
                        log(f"[OUTFIT] Generating model shot: {outfit_name}")
                        try:
                            results = await generate_outfit_shots(outfit, models)
                            if results:
                                log(f"[OUTFIT] Generated {len(results)} shots for '{outfit_name}'")
                                mark_outfit_generated(outfit_name)
                                
                                # Create composite flat lay (top + bottom merged in 1 image)
                                try:
                                    from composite_builder import create_outfit_composite
                                    outfit_output_dir = results[0].parent if results else None
                                    outfit_pieces = outfit.get("products") or outfit.get("items", [])
                                    if outfit_output_dir:
                                        composite = create_outfit_composite(
                                            outfit_dir=str(outfit_output_dir),
                                            top_dir=next((p.get("path") or p.get("front_image") for p in outfit_pieces if p["category"] == "top"), None),
                                            bottom_dir=next((p.get("path") or p.get("front_image") for p in outfit_pieces if p["category"] == "bottom"), None),
                                            shoe_dir=next((p.get("path") or p.get("front_image") for p in outfit_pieces if p["category"] == "shoe"), None)
                                        )
                                        if composite:
                                            log(f"[OUTFIT] Composite flat lay: {composite}")
                                except Exception as comp_err:
                                    log(f"[OUTFIT] Composite flat lay failed: {comp_err}")
                            else:
                                log(f"[OUTFIT] No shots generated for '{outfit_name}'")
                        except Exception as gen_err:
                            log(f"[OUTFIT] Generation error for '{outfit_name}': {gen_err}")
            except ImportError:
                pass  # outfit_warehouse not available
            except Exception as wh_err:
                log(f"[OUTFIT] Warehouse scan error: {wh_err}")

            if not loop_mode:
                log("[OK] Single run complete. Use --loop for 24/7.")
                break

            delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
            log("[WAIT] Sleeping {}s...".format(delay))
            await asyncio.sleep(delay)
    finally:
        log("[*] Shutting down worker...")


if __name__ == "__main__":
    asyncio.run(main())
