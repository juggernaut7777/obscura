"""
STOREFRONT AUTO-UPLOADER
=========================
Scans OUTPUT_READY_FOR_SALE for finished campaigns.
Reads metadata (product name, color, link) and generated images.
Merges them into the Next.js storefront's products.js data file.

COLOR VARIANT LOGIC:
  - If two campaigns share the same product_name AND purchase link,
    they are treated as color variants of the SAME product listing.
  - Each variant gets its own AI-generated image set.
  - The storefront shows color swatch bubbles to switch between them.

Usage:
  python storefront_uploader.py              # Scan and upload once
  python storefront_uploader.py --watch      # Watch for new campaigns
"""

import os
import re
import json
import shutil
import hashlib
import time
from pathlib import Path
from datetime import datetime
from pricing_engine import calculate_final_price

BASE_DIR = Path(__file__).parent
READY_DIR = BASE_DIR / "OUTPUT_READY_FOR_SALE"
STOREFRONT_DIR = BASE_DIR.parent / "storefront"
PRODUCTS_FILE = STOREFRONT_DIR / "src" / "data" / "products.js"
PUBLIC_DIR = STOREFRONT_DIR / "public" / "products"
UPLOADED_LOG = BASE_DIR / "uploaded_campaigns.json"

READY_DIR.mkdir(exist_ok=True)
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

# Private supplier mappings file — NEVER exposed to frontend customers
SUPPLIER_MAPPINGS_FILE = BASE_DIR / "supplier_mappings.json"


def load_supplier_mappings():
    if SUPPLIER_MAPPINGS_FILE.exists():
        with open(SUPPLIER_MAPPINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_supplier_mappings(mappings):
    with open(SUPPLIER_MAPPINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


from utils import slugify


def get_uploaded_log():
    if UPLOADED_LOG.exists():
        with open(UPLOADED_LOG, "r") as f:
            return json.load(f)
    return []


def save_uploaded_log(uploaded):
    with open(UPLOADED_LOG, "w") as f:
        json.dump(uploaded, f, indent=2)


def load_current_products():
    """Parse the current products.js file and return the product list."""
    if not PRODUCTS_FILE.exists():
        return [], "[]", "[]"
    
    content = PRODUCTS_FILE.read_text(encoding="utf-8")
    
    # Extract DEMO_PRODUCTS array using json evaluation if possible, 
    # but since it's a JS file, we'll extract the raw array string.
    match = re.search(r'export const DEMO_PRODUCTS = (\[[\s\S]*?\]);', content)
    existing_products_raw = match.group(1) if match else "[]"
    
    # Safely parse the existing JSON array of products
    try:
        existing_products = json.loads(existing_products_raw)
    except json.JSONDecodeError:
        existing_products = []
    
    # Extract COLLECTIONS array
    coll_match = re.search(r'export const COLLECTIONS = (\[[\s\S]*?\]);', content)
    collections_raw = coll_match.group(1) if coll_match else "[]"
    
    # Extract DEMO_OUTFITS array
    outfits_match = re.search(r'export const DEMO_OUTFITS = (\[[\s\S]*?\]);', content)
    outfits_raw = outfits_match.group(1) if outfits_match else "[]"
    
    return existing_products, collections_raw, outfits_raw


def extract_metadata_from_campaign(campaign_dir):
    """
    Extract product metadata from a campaign folder.
    Looks for metadata.json files inside the MANUAL_CURATION source images.
    Falls back to parsing the checkout_links.txt.
    """
    metadata = {
        "product_name": None,
        "color": None,
        "part": None,
        "is_set": False,
        "set_partner": None,
        "link": "",
        "images": [],
        "size_info": None,
        "size_charts": 0
    }
    
    # Check for metadata.json (from Discord bot / staging copy)
    for f in campaign_dir.iterdir():
        if f.suffix == ".json" and f.name != "checkout_links.json" and f.name != "outfit_metadata.json":
            try:
                with open(f, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
                    metadata["product_name"] = meta.get("product_name") or meta.get("name")
                    metadata["color"] = meta.get("color")
                    metadata["part"] = meta.get("part")  # "top", "bottom", or None
                    metadata["is_set"] = meta.get("is_set", False)
                    metadata["set_partner"] = meta.get("set_partner")
                    metadata["link"] = meta.get("link", "") or meta.get("url", "")
                    metadata["price"] = meta.get("price_cny") or meta.get("price") or 0
                    metadata["category"] = meta.get("category", "")
                    metadata["currency"] = meta.get("currency") or ("USD" if "$" in str(metadata["price"]) else "CNY")
                    metadata["size_info"] = meta.get("size_info")
                    metadata["size_charts"] = meta.get("size_charts", 0)
                    # Enriched fields from Phase 1 scraper
                    metadata["material"] = meta.get("material", "")
                    metadata["weight_gsm"] = meta.get("weight_gsm", 0)
                    metadata["measurements"] = meta.get("measurements", {})
                    metadata["model_info"] = meta.get("model_info", "")
                    metadata["care_instructions"] = meta.get("care_instructions", "")
                    metadata["brand_name"] = meta.get("brand_name", "")
                    metadata["product_category"] = meta.get("product_category", "")
                    metadata["variant_mappings"] = meta.get("variant_mappings", {})
                    metadata["item_id"] = meta.get("item_id", "")
                    metadata["platform"] = meta.get("platform", "")
                    metadata["seller"] = meta.get("seller", {})
                    metadata["stock_status"] = meta.get("stock_status", {})
                    metadata["description"] = meta.get("description", "")
            except Exception:
                pass
    
    # Check checkout_links.txt for the link
    checkout_file = campaign_dir / "checkout_links.txt"
    if checkout_file.exists() and not metadata["link"]:
        content = checkout_file.read_text(encoding="utf-8")
        link_match = re.search(r'(?:Kakobuy Checkout|Raw Link): (https?://\S+)', content)
        if link_match:
            metadata["link"] = link_match.group(1)
    
    # Collect generated images (the AI shots, not the source product photos)
    for f in sorted(campaign_dir.iterdir()):
        if f.suffix in [".png", ".jpg", ".jpeg", ".webp"]:
            # Only include generated shots (01_editorial, 02_lifestyle, etc.)
            if any(tag in f.name for tag in ["editorial", "lifestyle", "flatlay", "ghost", "fallback",
                                              "flat_lay", "mannequin", "hanger", "detail", "hero",
                                              "on_foot", "unboxing", "set_flat", "product_"]):
                metadata["images"].append(f)
    
    # Collect original source images (Yupoo/Weidian scraped photos)
    metadata["source_images"] = []
    source_prefixes = ("front_angle", "back_angle", "side_angle", "angle_", "source_")
    for f in sorted(campaign_dir.iterdir()):
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            if f.stem.startswith(source_prefixes):
                metadata["source_images"].append(f)
    
    return metadata


def copy_size_charts_to_public(campaign_dir, product_slug):
    """Find size chart images in the campaign folder and copy them to public/products/<slug>/."""
    product_dir = PUBLIC_DIR / product_slug
    product_dir.mkdir(parents=True, exist_ok=True)
    
    web_paths = []
    for f in campaign_dir.iterdir():
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            if any(k in f.name.lower() for k in ["chart", "size", "guide"]):
                # Clean or preserve name
                dest_name = f"size_guide_{f.name}"
                dest_path = product_dir / dest_name
                try:
                    shutil.copy(str(f), str(dest_path))
                    web_paths.append(f"/products/{product_slug}/{dest_name}")
                except Exception as e:
                    log(f"  [!] Error copying size chart {f.name}: {e}")
    return web_paths


def parse_sizes_from_info(size_info):
    """Extract standard sizes (S, M, L, XL, etc.) or numbers from size_info string."""
    if not size_info or "not specified" in size_info.lower() or "could not read" in size_info.lower():
        return ["S", "M", "L", "XL"]
    
    # Try to find something like "Sizes: S, M, L" or "Sizes: [S, M, L]"
    match = re.search(r'(?:sizes|size)\s*:\s*([^|]+)', size_info, re.IGNORECASE)
    if match:
        sizes_str = match.group(1).strip()
        # Clean brackets, quotes, etc.
        sizes_str = re.sub(r'[\[\]\'"]', '', sizes_str)
        sizes = [s.strip() for s in sizes_str.split(",") if s.strip()]
        if sizes:
            return sizes
            
    # Fallback: find any capitalized letter sizes (S, M, L, XL, XXL, etc.) or numbers
    # separated by commas or spaces
    sizes = re.findall(r'\b(S|M|L|XL|XXL|XXXL|OS|ONE SIZE|\d+)\b', size_info.upper())
    if sizes:
        # Deduplicate while preserving order
        seen = set()
        return [x for x in sizes if not (x in seen or seen.add(x))]
        
    return ["S", "M", "L", "XL"]


def copy_images_to_public(images, product_slug, color_slug):
    """Copy generated images to the Next.js public/products/ directory."""
    product_img_dir = PUBLIC_DIR / product_slug / color_slug
    product_img_dir.mkdir(parents=True, exist_ok=True)
    
    web_paths = []
    for i, img_path in enumerate(images):
        ext = img_path.suffix
        dest_name = f"{color_slug}_{i+1}{ext}"
        dest_path = product_img_dir / dest_name
        shutil.copy(str(img_path), str(dest_path))
        # Return the web-accessible path
        web_paths.append(f"/products/{product_slug}/{color_slug}/{dest_name}")
    
    return web_paths


def copy_source_images_to_public(source_images, product_slug):
    """Copy original Yupoo/Weidian scraped photos to public/products/<slug>/source/.
    These appear on product pages alongside AI shots to show the real product."""
    if not source_images:
        return []
    
    source_dir = PUBLIC_DIR / product_slug / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    
    web_paths = []
    for i, img_path in enumerate(source_images):
        ext = img_path.suffix
        dest_name = f"source_{i+1}{ext}"
        dest_path = source_dir / dest_name
        if not dest_path.exists():
            shutil.copy(str(img_path), str(dest_path))
        web_paths.append(f"/products/{product_slug}/source/{dest_name}")
    
    return web_paths


COLOR_HEX_MAP = {
    "black": "#000000", "white": "#FFFFFF", "red": "#C41E3A",
    "blue": "#2563EB", "green": "#16A34A", "grey": "#6B7280",
    "gray": "#6B7280", "navy": "#1E3A5F", "beige": "#D4C5A9",
    "cream": "#FFFDD0", "brown": "#8B4513", "khaki": "#C3B091",
    "pink": "#EC4899", "purple": "#7C3AED", "orange": "#EA580C",
    "yellow": "#EAB308", "olive": "#6B8E23", "burgundy": "#800020",
    "maroon": "#800000", "tan": "#D2B48C", "camel": "#C19A6B",
    "ivory": "#FFFFF0", "charcoal": "#36454F", "teal": "#008080",
    "coral": "#FF6F61", "mint": "#98FB98", "lavender": "#E6E6FA",
    "wine": "#722F37", "sand": "#C2B280", "mocha": "#967969",
    "coffee": "#6F4E37", "apricot": "#FBCEB1",
}


DEFAULT_OUTFITS = [
  {
    "id": "outfit-urban-phantom",
    "name": "The Urban Phantom Look",
    "description": "A complete tech-noir streetwear ensemble. Features the Phantom Tech Cargo paired with the Alcatraz Oversized Hoodie.",
    "price": 161,
    "image": "/products/product-2fbeb9ad/default/default_1.png",
    "images": [
      "/products/product-2fbeb9ad/default/default_1.png",
      "/products/product-2fbeb9ad/default/default_2.png",
      "/products/product-2fbeb9ad/default/default_3.png"
    ],
    "products": ["obs-alcatraz-hoodie", "obs-phantom-cargo"],
    "tags": ["Tech Noir", "Streetwear", "Winter Layering"]
  },
  {
    "id": "outfit-street-ritual",
    "name": "The Street Ritual Uniform",
    "description": "A premium, heavy cotton streetwear uniform. Paired with our washed distressed tee and heavyweight drop shoulder hoodie.",
    "price": 134,
    "image": "/products/product-1f32da21/default/default_1.png",
    "images": [
      "/products/product-1f32da21/default/default_1.png",
      "/products/product-1f32da21/default/default_2.png",
      "/products/product-1f32da21/default/default_3.png"
    ],
    "products": ["obs-alcatraz-hoodie", "obs-void-tee"],
    "tags": ["Urban Ritual", "Everyday Uniform", "Heavyweight"]
  },
  {
    "id": "outfit-deconstructed-noir",
    "name": "Deconstructed Tech Noir Set",
    "description": "Utilitarian tech cargo pants layered with a weathered vintage tee. A futuristic deconstructed look.",
    "price": 117,
    "image": "/products/product-2fbeb9ad/default/default_4.png",
    "images": [
      "/products/product-2fbeb9ad/default/default_4.png",
      "/products/product-1f32da21/default/default_4.png"
    ],
    "products": ["obs-phantom-cargo", "obs-void-tee"],
    "tags": ["Tech Noir", "Deconstructed", "Archival"]
  }
]


def build_products_js(products, collections_raw, outfits_raw):
    """Generate the products.js file content from our product list."""
    # If outfits_raw is empty or represents empty list, use defaults
    if not outfits_raw or outfits_raw.strip() == "[]":
        outfits_raw = json.dumps(DEFAULT_OUTFITS, indent=2)
        
    lines = [
        "/**",
        " * Product catalog — Auto-generated by storefront_uploader.py",
        f" * Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        " */",
        "",
        "export const DEMO_PRODUCTS = " + json.dumps(products, indent=2) + ";",
        "",
        f"export const COLLECTIONS = {collections_raw};",
        "",
        f"export const DEMO_OUTFITS = {outfits_raw};",
        "",
    ]
    return "\n".join(lines)


def check_and_register_outfit(campaign_dir, final_products):
    """
    Check if the campaign directory represents a complete outfit bundle,
    and return an outfit dictionary to be added to DEMO_OUTFITS.
    """
    outfit_meta_file = campaign_dir / "outfit_metadata.json"
    meta_file = campaign_dir / "metadata.json"
    
    is_outfit = False
    outfit_data = None
    
    # Try to load outfit metadata
    if outfit_meta_file.exists():
        try:
            with open(outfit_meta_file, "r", encoding="utf-8") as f:
                outfit_data = json.load(f)
                is_outfit = True
        except:
            pass
    elif meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                m = json.load(f)
                if m.get("is_set") or m.get("category") == "set":
                    is_outfit = True
                    outfit_data = {
                        "name": m.get("product_name") or campaign_dir.name,
                        "description": m.get("description") or f"Curated outfit set: {m.get('product_name')}.",
                        "items": [{"name": m.get("product_name"), "price": m.get("price", 89)}]
                    }
        except:
            pass
            
    # Also check if campaign folder name contains "_and_"
    if not is_outfit and "_and_" in campaign_dir.name:
        is_outfit = True
        # Extract names from folder name parts
        # e.g., "20260625_120000_m1_alcatraz-hoodie_and_phantom-cargo"
        parts = campaign_dir.name.split("_")
        name_part = parts[-1] if len(parts) > 1 else campaign_dir.name
        product_names = name_part.split("_and_")
        outfit_data = {
            "name": " ".join([p.replace("-", " ").title() for p in product_names]) + " Look",
            "description": f"Curated outfit styled with matching items.",
            "items": [{"name": p.replace("-", " ").title()} for p in product_names]
        }
        
    if not is_outfit or not outfit_data:
        return None
        
    # Build list of products in the outfit
    linked_products = []
    # Find matching products in final_products
    for item in outfit_data.get("items", []):
        item_name = item.get("name", "").lower()
        # Find product by name similarity
        matched_product = None
        for p in final_products:
            p_name = p.get("name", "").lower()
            if p_name in item_name or item_name in p_name or slugify(p_name) in slugify(item_name):
                matched_product = p
                break
        if matched_product:
            linked_products.append(matched_product["id"])
            
    # If we couldn't match any products from the final_products list, let's try matching from the slug names
    if not linked_products and "_and_" in campaign_dir.name:
        parts = campaign_dir.name.split("_")
        name_part = parts[-1] if len(parts) > 1 else campaign_dir.name
        product_slugs = name_part.split("_and_")
        for ps in product_slugs:
            # Clean numeric suffixes or prefixes
            clean_slug = re.sub(r'^\d+_|_\d+$', '', ps).strip()
            # Look for product that contains this slug
            for p in final_products:
                if clean_slug in p["id"] or p["id"] in clean_slug:
                    linked_products.append(p["id"])
                    break
                    
    # Ensure distinct products
    linked_products = list(set(linked_products))
    if not linked_products:
        # Fallback: link to the top 2 products in the catalog
        if len(final_products) >= 2:
            linked_products = [final_products[0]["id"], final_products[1]["id"]]
        else:
            return None
            
    # Determine the lookbook image for the outfit (first editorial image)
    outfit_images = []
    for f in sorted(campaign_dir.iterdir()):
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            if any(t in f.name.lower() for t in ["editorial", "lifestyle", "urban"]):
                # Copy to public
                dest_dir = PUBLIC_DIR / "outfits"
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / f.name
                try:
                    shutil.copy(str(f), str(dest_path))
                    outfit_images.append(f"/products/outfits/{f.name}")
                except:
                    pass
                    
    primary_image = outfit_images[0] if outfit_images else "https://images.unsplash.com/photo-1523398002811-999ca8dec234?w=800&h=1000&fit=crop"
    
    # Calculate price as the sum of linked products
    total_price = 0
    for p_id in linked_products:
        p = next((prod for prod in final_products if prod["id"] == p_id), None)
        if p:
            total_price += p.get("price", 89)
            
    outfit_id = f"outfit-{slugify(outfit_data['name'])}"
    
    return {
        "id": outfit_id,
        "name": outfit_data.get("name"),
        "description": outfit_data.get("description"),
        "price": total_price if total_price > 0 else 160,
        "image": primary_image,
        "images": outfit_images if outfit_images else [primary_image],
        "products": linked_products,
        "tags": ["Curated Look", "Streetwear", "Styled Bundle"]
    }


def scan_and_upload():
    """Main function: scan OUTPUT_READY_FOR_SALE and upload to storefront."""
    if not READY_DIR.exists():
        log("No OUTPUT_READY_FOR_SALE directory found.")
        return
    
    campaigns = [d for d in READY_DIR.iterdir() if d.is_dir()]
    if not campaigns:
        log("No campaigns to upload.")
        return
    
    uploaded = get_uploaded_log()
    uploaded_names = set(uploaded)
    
    # Load existing products from storefront
    existing_products, collections_raw, outfits_raw = load_current_products()
    
    # Group campaigns by product identity (name + link)
    new_items = []
    for campaign_dir in campaigns:
        if campaign_dir.name in uploaded_names:
            continue
        
        meta = extract_metadata_from_campaign(campaign_dir)
        if not meta["images"]:
            log(f"  [SKIP] {campaign_dir.name} — no generated images found")
            continue
        
        new_items.append((campaign_dir, meta))
    
    if not new_items:
        log("No new campaigns to upload.")
        return
    
    log(f"Found {len(new_items)} new campaigns to upload.")
    
    # Group by product identity: same product_name = ONE listing
    # Sets (tracksuit top+bottom) merge into ONE listing — sold together
    # Same name + different color = color variants of ONE product
    # Same name + different part (top/bottom) = same product, images combined per color
    product_groups = {}
    for campaign_dir, meta in new_items:
        # Identity key: use product_name if available, otherwise use the link
        name = meta["product_name"] or campaign_dir.name
        link = meta["link"] or ""
        part = meta.get("part")  # "top", "bottom", or None
        
        # Group key is ALWAYS the base product name — sets stay as one listing
        if meta["product_name"]:
            group_key = slugify(meta["product_name"])
        else:
            group_key = f"product-{hashlib.md5(campaign_dir.name.encode()).hexdigest()[:8]}"
        
        if group_key not in product_groups:
            product_groups[group_key] = {
                "name": meta["product_name"] or f"Product {len(product_groups) + 1}",
                "slug": group_key,
                "link": link,
                "is_set": meta.get("is_set", False),
                "set_partner": meta.get("set_partner"),
                "variants": []
            }
        
        # If ANY variant is a set, mark the whole group as a set
        if meta.get("is_set"):
            product_groups[group_key]["is_set"] = True
        
        product_groups[group_key]["variants"].append((campaign_dir, meta))
    
    # Build product entries
    final_products = list(existing_products)  # Start with existing products
    
    product_id_to_idx = {p["id"]: i for i, p in enumerate(final_products)}
    new_inserts_count = 0

    for group_key, group in product_groups.items():
        # Check if product already exists
        original_idx = product_id_to_idx.get(group["slug"])
        existing_idx = original_idx + new_inserts_count if original_idx is not None else None
        
        product_slug = group["slug"]
        
        colors = []
        all_images = []
        
        # We need the first meta to extract category/price/sizes
        first_meta = group["variants"][0][1]
        raw_price = first_meta.get("price", 0)
        currency = first_meta.get("currency", "CNY")
        
        try:
            # If price is a string like '¥189' or '$45', extract the number/float
            if isinstance(raw_price, str):
                cleaned_price = re.search(r'\d+(?:\.\d+)?', raw_price)
                if cleaned_price:
                    raw_price = float(cleaned_price.group())
                else:
                    raw_price = 0.0
            else:
                raw_price = float(raw_price)
        except Exception:
            raw_price = 0.0
            
        # ── PERCENTAGE-BASED PRICING ENGINE ──
        if raw_price > 0:
            price_res = calculate_final_price(raw_price, currency)
            sell_price = round(price_res["final_usd"])
            
            # Floor: never sell below $29 (accessories/hats), T-shirts are $31 minimum, Jackets are exactly $89
            category_str = (first_meta.get("category") or "").lower()
            name_str = (first_meta.get("product_name") or group["name"] or "").lower()
            is_tshirt = "tee" in name_str or "t-shirt" in name_str or "shirt" in name_str or "t恤" in name_str or "top" in category_str
            is_jacket = "jacket" in name_str or "coat" in name_str or "puffer" in name_str or "outerwear" in category_str
            
            if is_jacket:
                sell_price = 89
            elif is_tshirt and not any(k in name_str for k in ["hoodie", "sweatshirt", "jacket", "coat", "puffer"]):
                sell_price = max(sell_price, 31)
            else:
                sell_price = max(sell_price, 29)
        else:
            sell_price = 89  # Default when no price is known
        
        # Map category to new aesthetic collections
        cat_lower = (first_meta.get("category") or "").lower()
        if "shoe" in cat_lower:
            ui_category = "Archive"
        elif "bottom" in cat_lower or "pant" in cat_lower:
            ui_category = "Tech Noir"
        else:
            ui_category = "Urban Ritual"
            
        size_chart_paths = []
        
        # For sets: merge top+bottom images of the SAME color into one swatch
        # E.g., black top (3 images) + black bottom (3 images) = one "Black" swatch with 6 images
        # Non-sets: each variant is its own color swatch (existing behavior)
        color_buckets = {}  # color_name -> {"images": [], "hex": str}
        
        for campaign_dir, meta in group["variants"]:
            color_name = meta["color"] or "Default"
            color_slug = slugify(color_name)
            color_hex = COLOR_HEX_MAP.get(color_name.lower(), "#888888")
            part = meta.get("part")
            
            # Copy images to public dir
            # For sets with parts, include part in the subfolder to avoid overwriting
            if part and group.get("is_set"):
                img_subfolder = f"{color_slug}_{part}"
            else:
                img_subfolder = color_slug
            web_paths = copy_images_to_public(meta["images"], product_slug, img_subfolder)
            
            # Copy size charts if any
            charts = copy_size_charts_to_public(campaign_dir, product_slug)
            if charts:
                size_chart_paths.extend(charts)
            
            # Merge images by color — top images first, then bottom
            if color_name not in color_buckets:
                color_buckets[color_name] = {"images": [], "hex": color_hex, "parts": []}
            
            # Sort order: top images come before bottom images
            if part and part.lower() == "top":
                color_buckets[color_name]["images"] = web_paths + color_buckets[color_name]["images"]
                color_buckets[color_name]["parts"].insert(0, "top")
            else:
                color_buckets[color_name]["images"].extend(web_paths)
                if part:
                    color_buckets[color_name]["parts"].append(part)
            
            if not all_images:
                all_images = web_paths
            
            # Mark as uploaded
            uploaded.append(campaign_dir.name)
        
        # Build final colors list from merged buckets
        for color_name, bucket in color_buckets.items():
            colors.append({
                "name": color_name,
                "hex": bucket["hex"],
                "images": bucket["images"]
            })
            
        size_chart_image = size_chart_paths[0] if size_chart_paths else None
        size_info = first_meta.get("size_info") or "Sizes: S, M, L, XL | Fit: True to size"
        parsed_sizes = parse_sizes_from_info(size_info)
        
        # Copy source images (Yupoo/Weidian scraped photos) for ALL variants
        all_source_web_paths = []
        for campaign_dir, meta in group["variants"]:
            source_imgs = meta.get("source_images", [])
            if source_imgs:
                src_paths = copy_source_images_to_public(source_imgs, product_slug)
                all_source_web_paths.extend(src_paths)
        
        if existing_idx is not None:
            # Merge into existing product (add new colors/images)
            for new_c in colors:
                if not any(c["name"] == new_c["name"] for c in final_products[existing_idx].get("colors", [])):
                    final_products[existing_idx].setdefault("colors", []).append(new_c)
            # If it only had default images before, update the main image array
            if not final_products[existing_idx].get("images") and all_images:
                 final_products[existing_idx]["images"] = all_images
                 
            # Update sizing and charts if available in new metadata
            if first_meta.get("size_info"):
                final_products[existing_idx]["size_info"] = size_info
                final_products[existing_idx]["sizes"] = parsed_sizes
            if size_chart_image:
                final_products[existing_idx]["size_chart_image"] = size_chart_image
            # Merge source images if available
            if all_source_web_paths:
                existing_sources = final_products[existing_idx].get("sourceImages", [])
                for sp in all_source_web_paths:
                    if sp not in existing_sources:
                        existing_sources.append(sp)
                final_products[existing_idx]["sourceImages"] = existing_sources
                
            log(f"  [+] Updated existing product {group['name']} with new colors & size charts")
        else:
            # Build new product entry
            product_entry = {
                "id": product_slug,
                "name": group["name"],
                "price": sell_price,
                "comparePrice": round(sell_price * 1.30),  # 30% higher "was" price for sale urgency
                "category": ui_category,
                "badge": "Set" if group.get("is_set") else "New Drop",
                "isSet": group.get("is_set", False),
                "description": first_meta.get("description") or f"Curated piece: {group['name']}. Heavyweight construction, deconstructed silhouette.",
                "material": first_meta.get("material", ""),
                "care": first_meta.get("care_instructions", ""),
                "modelInfo": first_meta.get("model_info", ""),
                "brand": first_meta.get("brand_name", ""),
                "sizes": parsed_sizes,
                "sizeGuide": first_meta.get("measurements", {}),
                "images": all_images,
                "colors": colors if len(colors) > 1 or (len(colors) == 1 and colors[0]["name"] != "Default") else [],
                "details": [
                    "Premium construction",
                    "Limited drop",
                    "Ships from curated warehouse"
                ],
                # NO supplierLink exposed to customers
                "size_info": size_info,
                "size_chart_image": size_chart_image,
                "sourceImages": all_source_web_paths,  # Original Yupoo/Weidian photos
                "stock_status": first_meta.get("stock_status", {})
            }
            final_products.insert(0, product_entry) # Put new items at the top
            new_inserts_count += 1
            
            # ── PHASE 4B: Save supplier mapping to PRIVATE file ──
            supplier_mappings = load_supplier_mappings()
            supplier_mappings[product_slug] = {
                "source_url": group["link"],
                "platform": first_meta.get("platform", ""),
                "item_id": first_meta.get("item_id", ""),
                "variant_mappings": first_meta.get("variant_mappings", {}),
                "seller": first_meta.get("seller", {}),
                "cost_cny": raw_price,
                "currency": currency,
                "stock_status": first_meta.get("stock_status", {}),
                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_supplier_mappings(supplier_mappings)
            
            log(f"  [+] New item {group['name']} — {len(colors)} color(s), {sum(len(c['images']) for c in colors)} images")
            
    # Re-build and auto-register outfits
    try:
        existing_outfits = json.loads(outfits_raw)
        # Ensure all default outfits are present
        for df in DEFAULT_OUTFITS:
            if not any(o["id"] == df["id"] for o in existing_outfits):
                existing_outfits.append(df)
    except:
        existing_outfits = list(DEFAULT_OUTFITS)
        
    # Phase A: Explicit set registration (from campaign metadata)
    for campaign_dir in campaigns:
        new_outfit = check_and_register_outfit(campaign_dir, final_products)
        if new_outfit:
            # Check if outfit already exists
            if not any(o["id"] == new_outfit["id"] for o in existing_outfits):
                existing_outfits.insert(0, new_outfit)
                log(f"  [+] Registered new outfit bundle: {new_outfit['name']}")
    
    # Phase B: For set items — auto-pair with shoes to complete the outfit
    # A tracksuit set is already ONE product. Add matching shoes to make a full outfit.
    for group_key, group in product_groups.items():
        if group.get("is_set"):
            this_product = next((p for p in final_products if p["id"] == group["slug"]), None)
            if not this_product:
                continue
            
            outfit_id = f"outfit-{group['slug']}-complete"
            if any(o["id"] == outfit_id for o in existing_outfits):
                continue
            
            # Find matching shoes in the catalog
            matching_shoe = None
            set_color = (this_product.get("colors", [{}])[0].get("name", "") if this_product.get("colors") else "").lower()
            
            for p in final_products:
                p_cat = (p.get("category", "") or "").lower()
                p_name = (p.get("name", "") or "").lower()
                if p["id"] == this_product["id"]:
                    continue
                # Check if it's a shoe/sneaker
                if any(kw in p_cat or kw in p_name for kw in ["shoe", "sneaker", "boot", "trainer", "jordan", "dunk"]):
                    # Prefer color-matched shoes
                    shoe_colors = [c.get("name", "").lower() for c in p.get("colors", [])]
                    if set_color and set_color in shoe_colors:
                        matching_shoe = p
                        break
                    elif not matching_shoe:
                        matching_shoe = p  # Fallback: any shoe
            
            if matching_shoe:
                total_price = this_product.get("price", 0) + matching_shoe.get("price", 0)
                outfit_entry = {
                    "id": outfit_id,
                    "name": f"{group['name']} Complete Look",
                    "description": f"Full styled outfit — {group['name']} set paired with matching kicks. Shop each piece individually or add the whole look to cart.",
                    "price": total_price,
                    "image": this_product.get("images", [""])[0],
                    "images": (this_product.get("images", [])[:3] + matching_shoe.get("images", [])[:1])[:4],
                    "products": [this_product["id"], matching_shoe["id"]],
                    "tags": ["Complete Look", "Styled Outfit", "Shop The Look"]
                }
                existing_outfits.insert(0, outfit_entry)
                log(f"  [+] Complete outfit: {outfit_entry['name']} (${total_price})")
    
    # Phase C: Smart style matching via outfit_assembler (for non-set products)
    try:
        from outfit_assembler import OutfitAssembler
        assembler = OutfitAssembler()
        # Only attempt if we have enough products and not too many outfits already
        if len(final_products) >= 3 and len(existing_outfits) < 20:
            for product in final_products[:10]:  # Check top 10 products
                try:
                    suggestion = assembler.build_outfit(product)
                    if suggestion and suggestion.get("products"):
                        outfit_id = f"outfit-{slugify(suggestion.get('name', 'styled'))}"
                        if not any(o["id"] == outfit_id for o in existing_outfits):
                            existing_outfits.append(suggestion)
                            log(f"  [+] Smart-matched outfit: {suggestion['name']}")
                except Exception:
                    pass  # Don't let assembler errors break the upload
    except ImportError:
        pass  # outfit_assembler not available
                
    outfits_raw = json.dumps(existing_outfits, indent=2)
    
    # Write updated products.js
    products_content = build_products_js(final_products, collections_raw, outfits_raw)
    PRODUCTS_FILE.write_text(products_content, encoding="utf-8")
    log(f"[OK] Updated {PRODUCTS_FILE} with {len(final_products)} products")
    
    # Save upload log
    save_uploaded_log(uploaded)
    log(f"[OK] Upload log saved. {len(uploaded)} total campaigns processed.")


if __name__ == "__main__":
    import sys
    
    if "--watch" in sys.argv:
        log("Watching OUTPUT_READY_FOR_SALE for new campaigns...")
        while True:
            scan_and_upload()
            time.sleep(30)
    else:
        scan_and_upload()
