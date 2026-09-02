"""
Outfit Warehouse — Staging system for outfit assembly.

Stages front images from individual items (tops, bottoms, shoes) into a manifest.
Auto-matches items into outfit groups by brand + color family.
When a complete outfit (top + bottom, optionally + shoe) exists, marks it ready for model generation.

Usage:
    from outfit_warehouse import stage_item, find_ready_outfits, mark_outfit_generated
    
    # Stage individual items as they are processed
    stage_item("NOCTA Tech Hoodie", "NOCTA", "top", "Light Blue", "/path/to/front.jpg", {"gender": "male"})
    stage_item("NOCTA Tech Pants", "NOCTA", "bottom", "Light Blue", "/path/to/front.jpg", {"gender": "male"})
    
    # Check for complete outfits
    ready = find_ready_outfits()
    for outfit in ready:
        # Generate full outfit model shot via Flow API
        generate_outfit_shots(outfit)
        mark_outfit_generated(outfit["name"])
"""

import json
import os
from pathlib import Path
from datetime import datetime

WAREHOUSE_DIR = Path(__file__).parent / "data" / "warehouse"
MANIFEST_FILE = WAREHOUSE_DIR / "warehouse_manifest.json"


def safe_print(text):
    """Safe print for Windows cp1252 console."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))


def log(msg):
    safe_print(f"[WAREHOUSE] {msg}")


def _load_manifest() -> dict:
    """Load the warehouse manifest from disk."""
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    if MANIFEST_FILE.exists():
        try:
            return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            log(f"[!] Failed to load manifest: {e}")
    return {"items": [], "generated_outfits": [], "last_updated": ""}


def _save_manifest(manifest: dict):
    """Save the warehouse manifest to disk."""
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    manifest["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def stage_item(product_name: str, brand: str, category: str, color: str,
               front_image_path: str, metadata: dict = None):
    """Add an individual item to the warehouse manifest.
    
    Args:
        product_name: Display name of the product (e.g. "NOCTA Tech Fleece Hoodie")
        brand: Brand name (e.g. "NOCTA")
        category: One of 'top', 'bottom', 'shoe'
        color: Color variant name (e.g. "Light Blue")
        front_image_path: Absolute path to the front product image
        metadata: Optional dict with extra info (gender, folder_path, etc.)
    
    Returns:
        True if staged, False if duplicate (already exists)
    """
    if category in ("set", "tracksuit", "outfit"):
        res_top = stage_item(f"{product_name} (Top)", brand, "top", color, front_image_path, metadata)
        res_bot = stage_item(f"{product_name} (Pants)", brand, "bottom", color, front_image_path, metadata)
        return res_top or res_bot

    if category not in ("top", "bottom", "shoe"):
        log(f"[!] Invalid category '{category}'. Must be 'top', 'bottom', or 'shoe'.")
        return False

    
    manifest = _load_manifest()
    
    pid = metadata.get("product_id", "") if metadata else ""
    if pid:
        dedup_key = (pid, category)
    else:
        dedup_key = (product_name.lower().strip(), brand.lower().strip(), category, color.lower().strip())
    
    for existing in manifest["items"]:
        ex_meta = existing.get("metadata") or {}
        ex_pid = ex_meta.get("product_id", "")
        if ex_pid:
            ex_key = (ex_pid, existing["category"])
        else:
            ex_key = (existing.get("product_name", "").lower().strip(), existing["brand"].lower().strip(), existing["category"], existing["color"].lower().strip())
            
        if ex_key == dedup_key:
            log(f"[SKIP] Already staged: {product_name} ({brand} {category} in {color})")
            return False
    
    entry = {
        "product_name": product_name,
        "brand": brand,
        "category": category,
        "color": color,
        "front_image": str(front_image_path),
        "staged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metadata": metadata or {}
    }
    
    manifest["items"].append(entry)
    _save_manifest(manifest)
    log(f"[+] Staged: {brand} {category} '{color}' — {Path(front_image_path).name}")
    return True


def _normalize_color(color: str) -> str:
    """Normalize a color name for matching.
    
    Strips common qualifiers and returns the base color.
    E.g. 'Light Blue' -> 'blue', 'Army Green' -> 'green'
    """
    color = color.lower().strip()
    # Strip common prefixes
    for prefix in ("light ", "dark ", "army ", "deep ", "pale ", "bright ", "heather ", "tree ", "brown "):
        if color.startswith(prefix):
            color = color[len(prefix):]
    return color


def _colors_match(color_a: str, color_b: str) -> bool:
    """Check if two colors are compatible for outfit matching.
    
    Exact match first, then fuzzy base-color match.
    Never match fundamentally different colors.
    """
    a = color_a.lower().strip()
    b = color_b.lower().strip()
    
    # Exact match
    if a == b:
        return True
    
    norm_a = _normalize_color(a)
    norm_b = _normalize_color(b)
    
    # Hard block clashing color families (Red + Green, Pink + Green)
    red_family = {"red", "crimson", "maroon", "burgundy", "pink", "magenta"}
    green_family = {"green", "olive", "forest", "emerald", "sage", "army"}
    if (norm_a in red_family and norm_b in green_family) or (norm_a in green_family and norm_b in red_family):
        return False

    if norm_a == norm_b:
        return True
    
    # Same color family
    color_families = {
        "black": ["black", "charcoal", "graphite", "midnight"],
        "white": ["white", "cream", "ivory", "bone", "snow"],
        "blue": ["blue", "navy", "cobalt", "denim", "indigo", "slate"],
        "green": ["green", "olive", "forest", "emerald", "sage", "army", "camo"],
        "brown": ["brown", "tan", "camel", "khaki", "mocha", "coffee", "sand", "stone"],
        "grey": ["grey", "gray", "ash", "silver", "steel"],
        "red": ["red", "burgundy", "maroon", "wine", "crimson"],
    }
    
    for family, members in color_families.items():
        # Check if normalized or any constituent word belongs to the same family
        a_words = set(a.replace("-", " ").split())
        b_words = set(b.replace("-", " ").split())
        
        a_in_family = (norm_a in members) or any(w in members for w in a_words)
        b_in_family = (norm_b in members) or any(w in members for w in b_words)
        
        if a_in_family and b_in_family:
            return True
    
    return False


def _get_item_weight(item: dict) -> float:
    """Extract item weight in kg from metadata or estimate from category if absent."""
    meta = item.get("metadata") or {}
    weight = meta.get("weight_kg")
    if weight and isinstance(weight, (int, float)) and weight > 0:
        return float(weight)
    
    # Check weight_grams or detected_weight_grams
    grams = meta.get("weight_grams") or meta.get("detected_weight_grams")
    if grams and isinstance(grams, (int, float)) and grams > 0:
        return float(grams) / 1000.0
    
    # Category fallback estimates (in kg)
    cat = item.get("category", "").lower()
    if cat == "top":
        return 0.45  # Standard top/hoodie ~450g
    elif cat == "bottom":
        return 0.50  # Pants/jeans ~500g
    elif cat == "shoe":
        return 0.90  # Shoes/sneakers ~900g
    return 0.40


def _weights_compatible(top_item: dict, bottom_item: dict) -> bool:
    """Validate weight compatibility ratio between Top and Bottom.
    
    Top-to-Bottom weight ratio must satisfy 0.5 <= W_top / W_bottom <= 2.0.
    Prevents pairing heavy 600GSM winter hoodies (~0.9kg) with ultra-light summer shorts (~0.2kg).
    """
    w_top = _get_item_weight(top_item)
    w_bottom = _get_item_weight(bottom_item)
    
    if w_bottom <= 0:
        return True
    
    ratio = w_top / w_bottom
    return 0.5 <= ratio <= 2.0


def _estimate_shipping(total_weight_kg: float) -> dict:
    """Estimate international shipping tier & cost based on total outfit weight."""
    if total_weight_kg <= 0.5:
        tier, cost = "< 0.5kg (Light)", "$12"
    elif total_weight_kg <= 1.2:
        tier, cost = "0.5kg - 1.2kg (Standard)", "$18"
    elif total_weight_kg <= 2.2:
        tier, cost = "1.2kg - 2.2kg (Heavy)", "$26"
    else:
        tier, cost = "> 2.2kg (Bulky Set)", "$35"
    return {"weight_kg": round(total_weight_kg, 2), "tier": tier, "cost_estimate": cost}


def find_ready_outfits() -> list:
    """Scan the manifest for complete outfit groups ready for model generation.
    
    A complete outfit needs at minimum: 1 top + 1 bottom (same brand, compatible color & fabric weight).
    Shoes are optional but included if available (searches same brand first, then warehouse-wide).
    """
    manifest = _load_manifest()
    generated = set(manifest.get("generated_outfits", []))
    
    all_shoes = [i for i in manifest["items"] if i["category"] == "shoe"]
    
    # Group items by brand
    brand_groups = {}
    for item in manifest["items"]:
        brand = item["brand"].lower().strip()
        brand_groups.setdefault(brand, []).append(item)
    
    ready_outfits = []
    
    for brand, items in brand_groups.items():
        # Do NOT auto-merge unbranded or generic items — must have explicit matching brand
        if not brand or brand.lower().strip() in ("default", "unknown", "unbranded", "none", ""):
            continue
        tops = [i for i in items if i["category"] == "top"]
        bottoms = [i for i in items if i["category"] == "bottom"]
        same_brand_shoes = [i for i in items if i["category"] == "shoe"]
        
        # Try to match tops with bottoms by color & weight ratio
        used_bottoms = set()
        for top in tops:
            for b_idx, bottom in enumerate(bottoms):
                if b_idx in used_bottoms:
                    continue
                if _colors_match(top["color"], bottom["color"]) and _weights_compatible(top, bottom):
                    # Found a top+bottom match
                    outfit_name = f"{top['brand']} {top['color']} Outfit"
                    
                    if outfit_name in generated:
                        continue  # Already generated
                    
                    w_top = _get_item_weight(top)
                    w_bottom = _get_item_weight(bottom)
                    total_weight = w_top + w_bottom
                    
                    outfit_items = [
                        {"category": "top", "product_name": top["product_name"], "front_image": top["front_image"], "weight_kg": w_top},
                        {"category": "bottom", "product_name": bottom["product_name"], "front_image": bottom["front_image"], "weight_kg": w_bottom},
                    ]
                    all_images = [top["front_image"], bottom["front_image"]]
                    
                    # Try to find a matching shoe (same brand first, then any warehouse shoe)
                    candidate_shoes = same_brand_shoes + [s for s in all_shoes if s not in same_brand_shoes]
                    has_shoe = False
                    for shoe in candidate_shoes:
                        if _colors_match(top["color"], shoe["color"]) or shoe["color"].lower() in ("black", "white"):
                            w_shoe = _get_item_weight(shoe)
                            total_weight += w_shoe
                            outfit_items.append({"category": "shoe", "product_name": shoe["product_name"], "front_image": shoe["front_image"], "weight_kg": w_shoe})
                            all_images.append(shoe["front_image"])
                            has_shoe = True
                            log(f"[+] Paired Shoe '{shoe['product_name']}' with outfit '{outfit_name}'!")
                            break
                    
                    shipping_info = _estimate_shipping(total_weight)
                    gender = top.get("metadata", {}).get("gender") or bottom.get("metadata", {}).get("gender") or "male"
                    
                    ready_outfits.append({
                        "name": outfit_name,
                        "brand": top["brand"],
                        "color": top["color"],
                        "items": outfit_items,
                        "gender": gender,
                        "is_3piece": has_shoe,
                        "shipping_info": shipping_info,
                        "all_front_images": all_images
                    })
                    
                    used_bottoms.add(b_idx)
                    break  # Move to next top
    
    log(f"Found {len(ready_outfits)} ready outfit(s)")
    return ready_outfits



def mark_outfit_generated(outfit_name: str):
    """Mark an outfit as already generated so it won't be re-queued."""
    manifest = _load_manifest()
    if outfit_name not in manifest.get("generated_outfits", []):
        manifest.setdefault("generated_outfits", []).append(outfit_name)
        _save_manifest(manifest)
        log(f"[OK] Marked as generated: {outfit_name}")


def get_manifest() -> dict:
    """Return the full manifest dict."""
    return _load_manifest()


def clear_manifest():
    """Reset the manifest (for testing)."""
    _save_manifest({"items": [], "generated_outfits": [], "last_updated": ""})
    log("[!] Manifest cleared")


def get_warehouse_stats() -> dict:
    """Return a summary of warehouse contents."""
    manifest = _load_manifest()
    items = manifest.get("items", [])
    stats = {
        "total_items": len(items),
        "tops": len([i for i in items if i["category"] == "top"]),
        "bottoms": len([i for i in items if i["category"] == "bottom"]),
        "shoes": len([i for i in items if i["category"] == "shoe"]),
        "brands": list(set(i["brand"] for i in items)),
        "generated_outfits": len(manifest.get("generated_outfits", [])),
    }
    return stats


if __name__ == "__main__":
    # CLI mode: show warehouse stats and ready outfits
    stats = get_warehouse_stats()
    log(f"Warehouse Stats:")
    log(f"  Total items: {stats['total_items']}")
    log(f"  Tops: {stats['tops']} | Bottoms: {stats['bottoms']} | Shoes: {stats['shoes']}")
    log(f"  Brands: {', '.join(stats['brands']) if stats['brands'] else 'None'}")
    log(f"  Generated outfits: {stats['generated_outfits']}")
    log("")
    
    ready = find_ready_outfits()
    if ready:
        log(f"Ready outfits:")
        for outfit in ready:
            items_str = ", ".join(f"{i['category']}: {i['product_name']}" for i in outfit["items"])
            log(f"  {outfit['name']} ({outfit['gender']}) — {items_str}")
    else:
        log("No complete outfits ready for generation.")
