import os
import sys
import re
import json
from typing import Optional
from datetime import datetime
from pathlib import Path

# Common Paths
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output_ugc"
INPUT_DIR = BASE_DIR / "input_sourcing"
MODELS_DIR = BASE_DIR / "models" / "character_sheets"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

def safe_print(msg: str):
    """Safely print messages on Windows to avoid UnicodeEncodeErrors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding, errors='replace'))
        except Exception:
            print("[Print Error] Unable to encode output print message.")

def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text

def log(msg: str, log_file_path: Optional[str] = None):
    """Logs message with timestamp to console and log file."""
    if log_file_path is None:
        log_file_path = str(BASE_DIR / "worker_log.txt")
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    safe_print(line)
    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def detect_category(product_name: str, context_text: str = "") -> tuple:
    """
    Detects product category and whether it is a set based on keywords.
    Returns: (detected_category, is_set)
    """
    name_lower = product_name.lower()
    text_lower = context_text.lower()
    
    bottom_kw = ["pant", "short", "jogger", "trouser", "jeans", "cargo", "bottom"]
    shoe_kw = ["shoe", "sneaker", "boot", "jordan", "yeezy", "af1", "dunk", "trainer", "slide", "foam"]
    acc_kw = ["bag", "belt", "chain", "ring", "watch", "hat", "cap", "sunglasses", "balaclava"]
    set_kw = ["set", "suit", "tracksuit", "sweatsuit"]
    
    is_set = False
    detected_cat = "top"
    
    if any(k in name_lower for k in set_kw) or any(k in text_lower for k in set_kw):
        detected_cat = "set"
        is_set = True
    elif any(k in name_lower for k in shoe_kw):
        detected_cat = "shoes"
    elif any(k in name_lower for k in bottom_kw):
        detected_cat = "bottom"
    elif any(k in name_lower for k in acc_kw):
        detected_cat = "accessory"
        
    return detected_cat, is_set

def save_generated_images(result: dict, model_id: str, product_name: str, source_products: list, campaign_folder: str, shot_name: str) -> list:
    """
    Saves generated images into a dedicated campaign folder.
    Also copies the source product images, metadata, and size charts into the same folder.
    """
    import shutil
    import base64
    campaign_dir = OUTPUT_DIR / campaign_folder
    campaign_dir.mkdir(parents=True, exist_ok=True)

    # Copy source products first
    for sp in source_products:
        try:
            shutil.copy(sp, campaign_dir / Path(sp).name)
        except OSError:
            pass

    # Copy metadata.json, outfit_metadata.json, link.txt and size charts from the source folder
    if source_products:
        src_dir = Path(source_products[0]).parent

        # Copy metadata
        for meta_name in ["metadata.json", "outfit_metadata.json", "link.txt"]:
            meta_file = src_dir / meta_name
            if meta_file.exists():
                try:
                    shutil.copy(str(meta_file), str(campaign_dir / meta_name))
                except OSError:
                    pass

        # Copy size charts
        for f in src_dir.iterdir():
            if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                if any(k in f.name.lower() for k in ["chart", "size", "guide"]):
                    try:
                        shutil.copy(str(f), str(campaign_dir / f.name))
                    except OSError:
                        pass

    saved = []

    # 1. Check for CDN URLs (fifeUrl)
    media_list = result.get("media", [])
    for i, media_item in enumerate(media_list):
        gen_image = media_item.get("image", {}).get("generatedImage", {})
        fife_url = gen_image.get("fifeUrl", "")
        if fife_url:
            filename = f"{shot_name}_{i}.png"
            filepath = campaign_dir / filename
            success = False
            for attempt in range(3):
                try:
                    import httpx as httpx_sync
                    with httpx_sync.Client() as dl_client:
                        img_response = dl_client.get(fife_url, timeout=60.0)
                        img_response.raise_for_status()
                        with open(filepath, "wb") as f:
                            f.write(img_response.content)
                        saved.append(str(filepath))
                        log(f"  [SAVED] {campaign_folder}/{filename} ({len(img_response.content) // 1024} KB)")
                        success = True
                        break
                except Exception as e:
                    log(f"  [!] Download attempt {attempt+1} failed: {e}")
                    import time
                    time.sleep(2)
            if not success:
                log(f"  [!] Failed to download image after 3 attempts.")

    # 2. Check for base64-encoded images (fallback)
    images = result.get("generatedImages", result.get("images", []))
    if not images and "responses" in result:
        for resp in result["responses"]:
            images.extend(resp.get("generatedImages", []))

    for i, img_data in enumerate(images):
        img_bytes = img_data.get("encodedImage", img_data.get("imageBytes", ""))
        if img_bytes:
            filename = f"{shot_name}_fallback_{i}.png"
            filepath = campaign_dir / filename
            try:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(img_bytes))
                saved.append(str(filepath))
                log(f"  [SAVED] {campaign_folder}/{filename}")
            except Exception as e:
                log(f"  [!] Failed to save base64: {e}")

    return saved
