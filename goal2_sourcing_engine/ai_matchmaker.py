"""
AI MATCHMAKER V2 — The Styling Brain (with Inventory Memory)
=============================================================
Analyzes ALL available products (scraped + Discord inventory)
and pairs them into high-conversion "Full Outfits."

Now supports:
- Cross-pollination from old Discord drops
- Flexible matching (Top+Bottom, Top+Shoes, Full Set)
- Re-using products in multiple outfit combos
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from inventory_manager import load_inventory, get_available_pool

# CONFIG
POOL_DIR = Path("output/scraped_products")
QUEUE_DIR = Path("MANUAL_CURATION")
CATALOG_FILE = POOL_DIR / "agent_catalog.json"

async def run_matchmaker(max_outfits=20):
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    # === SOURCE 1: Scraped Catalog ===
    scraped = []
    if CATALOG_FILE.exists():
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        scraped = data.get("products", [])
        print(f"[*] Loaded {len(scraped)} items from scraped catalog")

    # === SOURCE 2: Permanent Discord Inventory ===
    inv_pool = get_available_pool()
    inv_count = sum(len(v) for v in inv_pool.values())
    print(f"[*] Loaded {inv_count} items from Discord inventory")

    # === MERGE INTO MASTER POOL ===
    pool = {"top": [], "bottom": [], "shoes": [], "accessory": []}

    # Add scraped items
    for p in scraped:
        cat = p.get("category", "top").lower()
        if "shoe" in cat: pool["shoes"].append(p)
        elif "pant" in cat or "short" in cat or "bottom" in cat: pool["bottom"].append(p)
        elif "accessory" in cat: pool["accessory"].append(p)
        else: pool["top"].append(p)

    # Add inventory items (these can be re-used across outfits)
    for cat in pool:
        pool[cat].extend(inv_pool.get(cat, []))

    print(f"[*] Master Pool: {len(pool['top'])} tops, {len(pool['bottom'])} bottoms, {len(pool['shoes'])} shoes, {len(pool['accessory'])} accessories")

    # === MATCHING LOGIC (Priority Order) ===
    sets_created = 0
    used_combos = set()  # prevent exact duplicate outfits

    # PRIORITY 1: Full Sets (Top + Bottom + Shoes)
    for top in pool["top"]:
        if sets_created >= max_outfits: break
        for bottom in pool["bottom"]:
            if sets_created >= max_outfits: break
            for shoes in pool["shoes"]:
                combo_key = f"{top.get('productName','')}_{bottom.get('productName','')}_{shoes.get('productName','')}"
                if combo_key in used_combos: continue
                used_combos.add(combo_key)

                _create_outfit([top, bottom, shoes], sets_created, "full")
                sets_created += 1
                if sets_created >= max_outfits: break

    # PRIORITY 2: Top + Bottom (no shoes available/needed)
    if sets_created < max_outfits:
        for top in pool["top"]:
            if sets_created >= max_outfits: break
            for bottom in pool["bottom"]:
                combo_key = f"{top.get('productName','')}_{bottom.get('productName','')}"
                if combo_key in used_combos: continue
                used_combos.add(combo_key)

                _create_outfit([top, bottom], sets_created, "top_bottom")
                sets_created += 1
                if sets_created >= max_outfits: break

    # PRIORITY 3: Top + Shoes
    if sets_created < max_outfits:
        for top in pool["top"]:
            if sets_created >= max_outfits: break
            for shoes in pool["shoes"]:
                combo_key = f"{top.get('productName','')}_{shoes.get('productName','')}"
                if combo_key in used_combos: continue
                used_combos.add(combo_key)

                _create_outfit([top, shoes], sets_created, "top_shoes")
                sets_created += 1
                if sets_created >= max_outfits: break

    print(f"\n[*] Matchmaker complete. {sets_created} outfits queued for generation.")


def _create_outfit(items, index, combo_type):
    """Creates an outfit folder in the queue."""
    ts = datetime.now().strftime('%H%M%S')
    outfit_name = f"outfit_{combo_type}_{ts}_{index}"
    outfit_dir = QUEUE_DIR / outfit_name
    outfit_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "name": f"Swag Set: {items[0].get('productName', 'Unknown')[:25]}",
        "link": items[0].get("productUrl", ""),
        "combo_type": combo_type,
        "items": items
    }

    # Copy images into the folder
    for i, item in enumerate(items):
        src = item.get("localImagePath", "")
        if src and os.path.exists(src):
            ext = Path(src).suffix or ".png"
            shutil.copy(src, outfit_dir / f"item_{i}{ext}")

    # Save link.txt for the worker
    with open(outfit_dir / "link.txt", "w") as f:
        f.write(manifest["link"])

    # Save metadata
    with open(outfit_dir / "outfit_metadata.json", "w") as f:
        json.dump(manifest, f, indent=2)

    names = " + ".join([item.get('productName', '?')[:25] for item in items])
    print(f"   [+] [{combo_type}] {names}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_matchmaker())
