import os
import re
import json
import uuid
import shutil
import logging
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Set up paths and base dir
BASE_DIR = Path(__file__).parent.resolve()
INPUT_DIR = BASE_DIR / "input_sourcing"
CURATION_DIR = BASE_DIR / "MANUAL_CURATION"
REJECTED_DIR = INPUT_DIR / "_rejected"

load_dotenv(BASE_DIR / ".env")

# Configure logging
log_file = BASE_DIR / "worker_log.txt"
logging.basicConfig(level=logging.INFO, format="%(asctime)s [BRIDGE] %(message)s")
logger = logging.getLogger("pipeline_bridge")

# Import helpers from project
from utils import safe_print, log, slugify
from vision_evaluator import VisionEvaluator
from style_tagger import tag_product

def parse_price(price_val) -> float:
    """Safely extract float price from various input formats."""
    if isinstance(price_val, (int, float)):
        return float(price_val)
    if not price_val:
        return 0.0
    # Strip everything except digits and dots
    cleaned = re.sub(r'[^\d\.]', '', str(price_val))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def promote_all(dry_run=False):
    """
    Automated promotion of products from input_sourcing/ to MANUAL_CURATION/.
    Validates images, updates metadata format, generates style tags, and moves them.
    """
    log("🔄 Starting Pipeline Bridge promotion run...")
    if not INPUT_DIR.exists():
        log(f"[!] Input directory {INPUT_DIR} does not exist.")
        return

    CURATION_DIR.mkdir(exist_ok=True)
    REJECTED_DIR.mkdir(exist_ok=True)

    # Initialize evaluator
    evaluator = VisionEvaluator()

    total_checked = 0
    total_promoted = 0
    total_rejected = 0
    promoted_details = []

    # Iterate through input_sourcing subfolders
    for subdir in sorted(list(INPUT_DIR.iterdir())):
        if not subdir.is_dir():
            continue
        if subdir.name in ("_rejected", "__pycache__", "outfit_grid"):
            continue

        total_checked += 1
        log(f"Processing staging product folder: {subdir.name}")

        meta_file = subdir / "metadata.json"
        if not meta_file.exists():
            log(f"   ⚠️ Skipping {subdir.name}: missing metadata.json")
            continue

        # Load metadata
        try:
            with open(meta_file, "r", encoding="utf-8") as mf:
                metadata = json.load(mf)
        except Exception as e:
            log(f"   ❌ Error reading metadata in {subdir.name}: {e}")
            continue

        # Identify all images in directory
        images = []
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            images.extend(list(subdir.glob(ext)))

        # Validate images with quick_quality_check
        valid_images = []
        for img in images:
            if any(bad in img.name.lower() for bad in ("size", "chart", "guide", "grid")):
                # Keep size charts in the folder but don't count them as product photos
                continue
            
            check = evaluator.quick_quality_check(str(img))
            if check["passed"]:
                valid_images.append(img)
            else:
                log(f"   🗑 Rejecting blurry/low-res image {img.name}: {check['reason']}")
                if not dry_run:
                    try:
                        os.remove(img)
                    except Exception as e:
                        log(f"   ⚠️ Failed to delete rejected image: {e}")

        # Check if we have any valid images left
        if not valid_images:
            log(f"   ❌ No valid product images in {subdir.name}. Moving to _rejected/")
            total_rejected += 1
            if not dry_run:
                try:
                    shutil.move(str(subdir), str(REJECTED_DIR / subdir.name))
                except Exception as e:
                    log(f"   ⚠️ Error moving folder to rejected: {e}")
            continue

        # Map metadata fields to target curated format
        product_name = metadata.get("product_name") or metadata.get("name") or subdir.name
        color = metadata.get("color") or "default"
        price_val = metadata.get("price") or metadata.get("price_cny") or metadata.get("price_string") or 0.0
        price_cny = parse_price(price_val)
        link = metadata.get("link") or metadata.get("url") or ""
        timestamp = metadata.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        source = metadata.get("source") or "shopify_direct"
        author = metadata.get("author") or "autonomous_sourcer"
        description = metadata.get("description") or ""

        # Normalize metadata keys
        curated_meta = {
            "product_name": product_name,
            "color": color,
            "price_cny": price_cny,
            "link": link,
            "timestamp": timestamp,
            "source": source,
            "author": author,
            "image_count": len(valid_images),
            "description": description
        }

        # Save back the normalized metadata.json
        if not dry_run:
            try:
                with open(meta_file, "w", encoding="utf-8") as mf:
                    json.dump(curated_meta, mf, indent=2, ensure_ascii=False)
            except Exception as e:
                log(f"   ⚠️ Could not write normalized metadata: {e}")

        # Run style_tagger
        log(f"   🎨 Running style tagger for {product_name}...")
        style_tags = {}
        if not dry_run:
            try:
                style_tags = tag_product(subdir)
            except Exception as e:
                log(f"   ⚠️ Style tagger failed: {e}")

        # Generate target folder name
        # ts format from timestamp or current time, let's keep it safe
        ts_clean = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:4]
        slug = slugify(product_name)
        new_folder_name = f"{slug}_{color.lower()}_{ts_clean}_{uid}"
        target_path = CURATION_DIR / new_folder_name

        log(f"   ✅ Promoting {subdir.name} → MANUAL_CURATION/{new_folder_name}")
        total_promoted += 1
        promoted_details.append({
            "name": product_name,
            "color": color,
            "price": price_cny,
            "gender": style_tags.get("gender", "unisex"),
            "category": style_tags.get("category", "unknown")
        })

        if not dry_run:
            try:
                shutil.move(str(subdir), str(target_path))
            except Exception as e:
                log(f"   ❌ Failed to move to curation queue: {e}")

    log(f"📊 Promotion complete. Staging checked: {total_checked}, Promoted: {total_promoted}, Rejected: {total_rejected}")

    # Send Discord Webhook Summary
    webhook_url = os.getenv("DISCORD_SCOUT_WEBHOOK")
    if webhook_url and total_promoted > 0:
        try:
            fields = [
                {"name": "📁 Checked Staging", "value": str(total_checked), "inline": True},
                {"name": "✅ Promoted to Curation", "value": str(total_promoted), "inline": True},
                {"name": "❌ Rejected (Invalid/Blurry)", "value": str(total_rejected), "inline": True}
            ]
            
            # Show top 5 promoted products in the embed description
            desc_lines = ["**Promoted Items:**"]
            for idx, p in enumerate(promoted_details[:5]):
                desc_lines.append(f"• {p['name']} ({p['color']}) - ¥{p['price']} | _{p['gender']} {p['category']}_")
            if len(promoted_details) > 5:
                desc_lines.append(f"_...and {len(promoted_details) - 5} more items_")

            payload = {
                "embeds": [{
                    "title": "🔄 Sourcing Pipeline Bridge — Promoted Staged Products",
                    "description": "\n".join(desc_lines),
                    "color": 0x2ECC71,
                    "fields": fields,
                    "footer": {"text": "OBSCURA Sourcing Pipeline"}
                }]
            }
            resp = requests.post(webhook_url, json=payload, timeout=10)
            if resp.status_code == 204 or resp.status_code == 200:
                log("[+] Posted promotion summary to Discord.")
            else:
                log(f"[!] Discord webhook returned status code {resp.status_code}")
        except Exception as e:
            log(f"[!] Failed to send Discord webhook summary: {e}")

if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    promote_all(dry_run=dry_run)
