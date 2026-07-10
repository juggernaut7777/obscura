"""
AUTO-MATCHER — Fashion Outfit Intelligence Engine
==================================================
Scans MANUAL_CURATION for tagged products, finds compatible pairs,
and sends Discord recommendation cards for your approval.

Flow:
  1. Loads all style_tags.json from MANUAL_CURATION subfolders
  2. For each unmatched item, finds the best compatible partner from inventory
  3. Sends a Discord "Outfit Match" card with BOTH products
  4. You react ✅ (approve merge) or ❌ (skip)
  5. ✅ triggers creation of a merged folder for the AI worker

Usage:
  python auto_matcher.py              # Run once
  python auto_matcher.py --watch      # Check every 30 min
"""

import os
import re
import sys
import json
import time
import shutil
import logging
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

log = logging.getLogger("auto_matcher")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [MATCHER] %(message)s")

BASE_DIR = Path(__file__).parent
CURATION_DIR = BASE_DIR / "MANUAL_CURATION"
MERGED_DIR = BASE_DIR / "MANUAL_CURATION" / "_merged_outfits"
MERGED_DIR.mkdir(exist_ok=True)

DISCORD_WEBHOOK = os.environ.get("DISCORD_SCOUT_WEBHOOK", "")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")

# Match log to avoid re-suggesting the same pair
MATCH_LOG_FILE = BASE_DIR / "data" / "match_suggestions.json"
MATCH_LOG_FILE.parent.mkdir(exist_ok=True)


# ── Niche compatibility matrix ───────────────────────────────────
# Only items in compatible niches should be merged together
COMPATIBLE_NICHES = {
    "streetwear":  ["streetwear", "y2k", "basics"],
    "elegant":     ["elegant", "formal", "basics"],
    "athleisure":  ["athleisure", "basics"],
    "techwear":    ["techwear", "basics", "streetwear"],
    "y2k":         ["y2k", "streetwear", "basics"],
    "formal":      ["formal", "elegant"],
    "basics":      ["streetwear", "elegant", "athleisure", "techwear", "y2k", "formal", "basics"],
}

# Category pairing rules: which categories complete each other
PAIRING_RULES = {
    "top":       ["bottom"],
    "bottom":    ["top", "outerwear"],
    "outerwear": ["top", "bottom"],
    # These never get merged — they're always solo
    "shoes":     [],
    "accessory": [],
    "dress":     [],
    "set":       [],
}


def load_match_log() -> set:
    if MATCH_LOG_FILE.exists():
        try:
            data = json.loads(MATCH_LOG_FILE.read_text(encoding="utf-8"))
            return set(data.get("suggested_pairs", []))
        except Exception:
            pass
    return set()


def save_match_log(pairs: set):
    data = {"suggested_pairs": list(pairs), "updated_at": datetime.now().isoformat()}
    MATCH_LOG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_all_tagged_products() -> list:
    """Load all products that have been style-tagged."""
    products = []
    for folder in CURATION_DIR.iterdir():
        if not folder.is_dir() or folder.name.startswith("_"):
            continue
        tags_file = folder / "style_tags.json"
        if not tags_file.exists():
            continue
        try:
            tags = json.loads(tags_file.read_text(encoding="utf-8"))
            tags["folder_path"] = str(folder)
            tags["folder_name"] = folder.name

            # Get first product image for Discord preview
            images = [f for f in folder.glob("*") if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
                      and "size" not in f.name.lower() and "chart" not in f.name.lower()]
            tags["preview_image"] = str(images[0]) if images else ""
            products.append(tags)
        except Exception as e:
            log.warning(f"Could not load tags for {folder.name}: {e}")
    return products


def score_pair(item_a: dict, item_b: dict) -> int:
    """
    Score how well two items pair together (0 = incompatible, higher = better).
    """
    score = 0

    # Category must be compatible
    cat_a = item_a.get("category", "")
    cat_b = item_b.get("category", "")
    allowed_for_a = PAIRING_RULES.get(cat_a, [])
    if cat_b not in allowed_for_a:
        return 0  # Hard block — categories don't pair

    # Niche compatibility
    niche_a = item_a.get("niche", "basics")
    niche_b = item_b.get("niche", "basics")
    if niche_b in COMPATIBLE_NICHES.get(niche_a, []):
        score += 3
    else:
        return 0  # Hard block — wrong vibe (no Corteiz + elegant)

    # Gender must match (women's top must go with women's or unisex bottom)
    gender_a = item_a.get("gender", "unisex")
    gender_b = item_b.get("gender", "unisex")
    if gender_a == gender_b:
        score += 3
    elif "unisex" in (gender_a, gender_b):
        score += 1
    else:
        return 0  # Hard block — men's and women's don't mix

    # sub_category appears in compatible_with list
    sub_b = item_b.get("sub_category", "")
    if sub_b in item_a.get("compatible_with", []):
        score += 5

    # Color harmony bonus (same or neutral colors)
    colors_a = set(item_a.get("colors", []))
    colors_b = set(item_b.get("colors", []))
    neutral = {"black", "white", "cream", "beige", "grey", "gray", "navy"}
    if colors_a & colors_b:  # Shared colors
        score += 2
    if colors_a & neutral or colors_b & neutral:  # At least one neutral
        score += 1

    return score


def find_best_pairs(products: list, already_suggested: set) -> list:
    """Find all valid pairings, sorted by score."""
    pairs = []
    n = len(products)

    for i in range(n):
        for j in range(i + 1, n):
            a = products[i]
            b = products[j]

            pair_key = "_x_".join(sorted([a["folder_name"], b["folder_name"]]))
            if pair_key in already_suggested:
                continue

            score = score_pair(a, b)
            if score > 0:
                pairs.append((score, pair_key, a, b))

    pairs.sort(key=lambda x: x[0], reverse=True)
    return pairs


def send_match_card(pair_key: str, item_a: dict, item_b: dict, score: int):
    """Send a Discord card suggesting an outfit merge."""
    if not DISCORD_WEBHOOK:
        log.warning("No Discord webhook set.")
        return None

    name_a = item_a.get("product_name", item_a["folder_name"])[:40]
    name_b = item_b.get("product_name", item_b["folder_name"])[:40]

    gender = item_a.get("gender", "unisex").title()
    niche = item_a.get("niche", "").title()
    scene = item_a.get("scene_style", "").replace("_", " ").title()

    # Calculate combined weight for shipping estimate
    weight_total = item_a.get("weight_kg", 0.4) + item_b.get("weight_kg", 0.4)
    # Kakobuy weight-based shipping estimate (rough):
    # 0-0.5kg: ~$12 | 0.5-1kg: ~$18 | 1-2kg: ~$25 | 2kg+: ~$35
    if weight_total <= 0.5:
        ship_est = "$12"
    elif weight_total <= 1.0:
        ship_est = "$18"
    elif weight_total <= 2.0:
        ship_est = "$25"
    else:
        ship_est = "$35"

    embed = {
        "title": f"🎨 Outfit Match Suggestion — Score {score}/10",
        "description": (
            f"**{name_a}** × **{name_b}**\n"
            f"_{gender} · {niche} · {scene}_\n\n"
            f"Combined weight: ~{weight_total:.1f}kg → Shipping est. {ship_est}\n\n"
            f"**React ✅ to merge these into one outfit drop**\n"
            f"**React ❌ to skip this pair**"
        ),
        "color": 0x9B59B6,
        "fields": [
            {
                "name": "🔝 Item A",
                "value": f"{item_a.get('gender', '?')} · {item_a.get('sub_category', '?')} · {item_a.get('niche', '?')}",
                "inline": True
            },
            {
                "name": "👖 Item B",
                "value": f"{item_b.get('gender', '?')} · {item_b.get('sub_category', '?')} · {item_b.get('niche', '?')}",
                "inline": True
            },
            {
                "name": "🎬 AI Scene Style",
                "value": scene or "Auto-detect",
                "inline": False
            }
        ],
        "footer": {"text": f"Pair ID: {pair_key} | Auto-Matcher v1.0"}
    }

    try:
        resp = requests.post(
            DISCORD_WEBHOOK + "?wait=true",
            json={"embeds": [embed]},
            timeout=10
        )
        resp.raise_for_status()
        msg_data = resp.json()
        msg_id = msg_data.get("id")
        channel_id = msg_data.get("channel_id")

        # Add both ✅ and ❌ reactions for easy approval/rejection
        if msg_id and channel_id and DISCORD_TOKEN:
            headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
            for emoji in ["%E2%9C%85", "%E2%9D%8C"]:  # ✅ ❌
                try:
                    requests.put(
                        f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg_id}/reactions/{emoji}/@me",
                        headers=headers, timeout=5
                    )
                    time.sleep(0.3)
                except Exception:
                    pass

        log.info(f"📤 Sent match card: {name_a} × {name_b}")
        return msg_id
    except Exception as e:
        log.error(f"Discord match card failed: {e}")
        return None


def create_merged_folder(item_a: dict, item_b: dict) -> Path:
    """
    Create a merged outfit folder that the AI worker can process.
    Copies images from both product folders into a single combined folder.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_a = re.sub(r'[^a-z0-9-]', '-', item_a.get("product_name", "item-a").lower())[:20]
    name_b = re.sub(r'[^a-z0-9-]', '-', item_b.get("product_name", "item-b").lower())[:20]
    folder_name = f"MERGED_{name_a}_{name_b}_{ts}"

    merged_folder = CURATION_DIR / folder_name
    merged_folder.mkdir(exist_ok=True)

    # Copy product images from both folders
    for item in [item_a, item_b]:
        src = Path(item["folder_path"])
        images = [f for f in src.glob("*") if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
                  and "size" not in f.name.lower() and "chart" not in f.name.lower()]
        for img in images[:3]:  # Max 3 images per product
            shutil.copy(str(img), str(merged_folder / f"{item['folder_name']}_{img.name}"))

    # Copy size charts too
    for item in [item_a, item_b]:
        src = Path(item["folder_path"])
        size_imgs = [f for f in src.glob("*") if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
                     and ("size" in f.name.lower() or "chart" in f.name.lower())]
        for img in size_imgs[:1]:
            shutil.copy(str(img), str(merged_folder / f"size_{item['folder_name']}_{img.name}"))

    # Build merged metadata
    meta_a = {}
    meta_b = {}
    for item, meta in [(item_a, meta_a), (item_b, meta_b)]:
        mf = Path(item["folder_path"]) / "metadata.json"
        if mf.exists():
            try:
                meta.update(json.loads(mf.read_text(encoding="utf-8")))
            except Exception:
                pass

    combined_meta = {
        "is_merged_outfit": True,
        "product_name": f"{item_a.get('product_name', 'Item A')} + {item_b.get('product_name', 'Item B')}",
        "items": [
            {
                "product_name": item_a.get("product_name", ""),
                "price": meta_a.get("price_cny", 0),
                "link": meta_a.get("link", ""),
                "size_info": meta_a.get("size_info", ""),
                "pipeline": meta_a.get("pipeline", "kakobuy"),
                "folder": item_a["folder_name"],
            },
            {
                "product_name": item_b.get("product_name", ""),
                "price": meta_b.get("price_cny", 0),
                "link": meta_b.get("link", ""),
                "size_info": meta_b.get("size_info", ""),
                "pipeline": meta_b.get("pipeline", "kakobuy"),
                "folder": item_b["folder_name"],
            }
        ],
        "niche": item_a.get("niche", "basics"),
        "gender": item_a.get("gender", "unisex"),
        "scene_style": item_a.get("scene_style", "minimal_clean"),
        "weight_kg": item_a.get("weight_kg", 0.4) + item_b.get("weight_kg", 0.4),
        "created_at": datetime.now().isoformat()
    }

    (merged_folder / "outfit_metadata.json").write_text(
        json.dumps(combined_meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    log.info(f"✅ Merged folder created: {folder_name}")
    return merged_folder


def run(max_suggestions: int = 10):
    """Main matching loop."""
    log.info("🔍 Loading tagged products...")
    products = load_all_tagged_products()

    if len(products) < 2:
        log.info(f"Only {len(products)} tagged product(s) — need at least 2 to match.")
        return

    log.info(f"Loaded {len(products)} tagged products. Finding matches...")

    already_suggested = load_match_log()
    pairs = find_best_pairs(products, already_suggested)

    if not pairs:
        log.info("No new pairs found.")
        return

    log.info(f"Found {len(pairs)} possible pairs. Sending top {min(max_suggestions, len(pairs))} to Discord...")

    sent = 0
    for score, pair_key, item_a, item_b in pairs[:max_suggestions]:
        send_match_card(pair_key, item_a, item_b, score)
        already_suggested.add(pair_key)
        sent += 1
        time.sleep(2)  # Rate limit

    save_match_log(already_suggested)
    log.info(f"✅ Sent {sent} outfit match suggestions to Discord.")


if __name__ == "__main__":
    if "--watch" in sys.argv:
        log.info("Auto-Matcher in watch mode — checking every 30 minutes...")
        while True:
            run()
            time.sleep(1800)
    else:
        run()
