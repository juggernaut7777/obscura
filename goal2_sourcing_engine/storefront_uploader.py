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

SHOE_KEYWORDS = ("shoe", "sneaker", "boot", "trainer", "jordan", "dunk")


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
    full_msg = f"[{ts}] {msg}"
    try:
        print(full_msg, flush=True)
    except UnicodeEncodeError:
        print(full_msg.encode("ascii", "replace").decode("ascii"), flush=True)


from utils import slugify


def get_uploaded_log():
    if UPLOADED_LOG.exists():
        with open(UPLOADED_LOG, "r") as f:
            return json.load(f)
    return []


def save_uploaded_log(uploaded):
    with open(UPLOADED_LOG, "w") as f:
        json.dump(uploaded, f, indent=2)


def clean_product_title(raw_title: str) -> str:
    """Clean Chinese Yupoo titles (remove prices, star censoring, size annotations)
    and output premium, editorial GENERIC fashion titles.
    RULE: Never expose real brand names (Nike, Adidas, NOCTA, etc.) on the public storefront.
    """
    if not raw_title:
        return "Premium Heavyweight Essential"
    
    title = raw_title
    # Remove price prefix like ￥113 or ¥235
    title = re.sub(r'^[￥¥]\d+\s*', '', title)
    
    # Remove seller size annotations like （im 170cm 60kg i wear size M in the phot）
    title = re.sub(r'[\（\(].*?[\）\)]', '', title)
    
    # Remove seller numeric item codes like 42061208144
    title = re.sub(r'\b\d{8,}\b', '', title)
    
    # Strip star-censored brand names and all brand references entirely
    title = re.sub(r'C[⭐\*]+OME\s*HE[⭐\*]+TS', '', title, flags=re.IGNORECASE)
    title = re.sub(r'N[⭐\*]+K[⭐\*]+', '', title, flags=re.IGNORECASE)
    title = re.sub(r'NO[⭐\*]+T[⭐\*]+', '', title, flags=re.IGNORECASE)
    # Remove known brand names entirely
    for brand in ['NOCTA', 'NIKE', 'ADIDAS', 'CHROME HEARTS', 'ESSENTIALS',
                  'FOG', 'FEAR OF GOD', 'BALENCIAGA', 'GUCCI', 'PRADA',
                  'LOUIS VUITTON', 'LV', 'DIOR', 'SUPREME', 'OFF-WHITE',
                  'STUSSY', 'JORDAN', 'YEEZY', 'NEW BALANCE']:
        title = re.sub(re.escape(brand), '', title, flags=re.IGNORECASE)
    title = title.replace("⭐", "").replace("*", "")
    
    # Clean whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Map to premium generic product names by garment type
    lower_t = title.lower()
    if "t-shirt" in lower_t or "tee" in lower_t:
        if "graphic" in lower_t:
            return "Heavyweight Graphic T-Shirt"
        elif "long sleeved" in lower_t or "long sleeve" in lower_t:
            return "Heavyweight Long Sleeve Tee"
        return "Premium Heavyweight Tee"
    elif "long sleeved" in lower_t or "long sleeve" in lower_t:
        return "Heavyweight Long Sleeve Tee"
    elif ("hoodie" in lower_t or "hooded" in lower_t) and ("trousers" in lower_t or "pants" in lower_t):
        return "Tech Fleece Hoodie & Trousers Set"
    elif "hoodie" in lower_t or "hooded" in lower_t:
        return "Premium Tech Fleece Hoodie"
    elif "jacket" in lower_t:
        if "windbreak" in lower_t or "waterproof" in lower_t or "shell" in lower_t:
            return "Tech Waterproof Shell Jacket"
        elif "puffer" in lower_t or "down" in lower_t:
            return "Premium Puffer Jacket"
        elif "varsity" in lower_t:
            return "Varsity Letterman Jacket"
        return "Premium Shell Jacket"
    elif "trousers" in lower_t or "pants" in lower_t:
        if "cargo" in lower_t:
            return "Heavyweight Cargo Trousers"
        return "Heavyweight Tech Trousers"
    elif "shorts" in lower_t:
        return "Premium Athletic Shorts"
    elif "sweater" in lower_t or "crewneck" in lower_t:
        return "Premium Knit Crewneck"
    elif "vest" in lower_t:
        return "Premium Utility Vest"
    
    # If we still have a reasonable title after brand stripping, use it
    if len(title) > 3:
        return title.title()
    return "Premium Heavyweight Essential"


def generate_luxury_specs(item_name: str, category: str, is_set: bool = False) -> dict:
    """Generate luxury specifications, fabric composition, GSM, care, fit advice, and sizing matrix.
    Ensures every product on the storefront has full luxury specs for high customer conversion."""
    name_lower = item_name.lower()
    cat_lower = (category or "").lower()

    if is_set or "set" in name_lower or "tracksuit" in name_lower or "zipset" in name_lower or ("trousers" in name_lower and "hoodie" in name_lower):
        return {
            "material": "460 GSM Ultra-Heavyweight Cotton Fleece & French Terry Co-ord",
            "care": "Machine wash cold inside out with like colors. Hang dry in shade. Do not tumble dry. Cool iron on reverse.",
            "modelInfo": "Model is 6'1\" (185cm), 165 lbs (75kg), wearing size Large top and Medium bottom for a tailored streetwear drape.",
            "weight_gsm": 460,
            "weight_kg": 1.25,
            "details": [
                "Complete 2-piece architectural uniform: hoodie/jacket & matching trousers",
                "Custom milled 460 GSM combed cotton fleece with thermal interior loopback",
                "Double-needle flatlock stitching along all stress seams for lifetime durability",
                "Elasticated waistband with custom metal-tipped elongated drawstrings",
                "Subtle tonal archival branding with vintage matte hardware"
            ],
            "sizeGuide": {
                "S": {"top_chest": "116 cm / 45.7 in", "top_length": "68 cm / 26.8 in", "waist": "74-82 cm / 29-32 in", "pants_length": "104 cm / 40.9 in"},
                "M": {"top_chest": "120 cm / 47.2 in", "top_length": "70 cm / 27.6 in", "waist": "78-86 cm / 31-34 in", "pants_length": "106 cm / 41.7 in"},
                "L": {"top_chest": "126 cm / 49.6 in", "top_length": "72 cm / 28.3 in", "waist": "82-92 cm / 32-36 in", "pants_length": "108 cm / 42.5 in"},
                "XL": {"top_chest": "132 cm / 52.0 in", "top_length": "74 cm / 29.1 in", "waist": "86-98 cm / 34-38 in", "pants_length": "110 cm / 43.3 in"},
                "2XL": {"top_chest": "138 cm / 54.3 in", "top_length": "76 cm / 29.9 in", "waist": "90-104 cm / 35-41 in", "pants_length": "112 cm / 44.1 in"}
            }
        }
    elif any(k in name_lower for k in ("pant", "sweatpant", "jogger", "trouser", "cargo", "denim", "jean")) or cat_lower in ("bottoms", "bottom"):
        return {
            "material": "420 GSM Heavyweight Dense Loopback Cotton Fleece",
            "care": "Machine wash cold delicate. Tumble dry low or hang dry. Do not iron directly on graphics.",
            "modelInfo": "Model is 6'1\" (185cm) wearing size M for a relaxed straight-leg silhouette with stacked hem.",
            "weight_gsm": 420,
            "weight_kg": 0.58,
            "details": [
                "420 GSM custom-milled high-density cotton fleece with heavy drape",
                "Elasticated waistband with elongated contrast natural cotton drawstrings",
                "Deep side slant hand pockets and rear concealed secure zip pocket",
                "Relaxed straight-leg cut engineered for ideal stacking over luxury sneakers",
                "Silkscreen printed archival graphics with vintage micro-cracking wash"
            ],
            "sizeGuide": {
                "S": {"waist": "74-82 cm / 29-32 in", "hip": "106 cm / 41.7 in", "length": "103 cm / 40.5 in", "inseam": "76 cm / 29.9 in"},
                "M": {"waist": "78-86 cm / 31-34 in", "hip": "110 cm / 43.3 in", "length": "105 cm / 41.3 in", "inseam": "77 cm / 30.3 in"},
                "L": {"waist": "82-92 cm / 32-36 in", "hip": "114 cm / 44.9 in", "length": "107 cm / 42.1 in", "inseam": "78 cm / 30.7 in"},
                "XL": {"waist": "86-98 cm / 34-38 in", "hip": "118 cm / 46.5 in", "length": "109 cm / 42.9 in", "inseam": "79 cm / 31.1 in"},
                "2XL": {"waist": "90-104 cm / 35-41 in", "hip": "122 cm / 48.0 in", "length": "111 cm / 43.7 in", "inseam": "80 cm / 31.5 in"}
            }
        }
    elif any(k in name_lower for k in ("jacket", "windbreaker", "shell", "coat", "parka", "bomber", "puffer")) or cat_lower in ("outerwear", "jackets"):
        return {
            "material": "Technical Matte Nylon Taslan (Water-Repellent DWR Finish, 100% Polyamide Shell)",
            "care": "Wipe clean with a damp microfiber cloth or professional gentle wet clean. Do not tumble dry. Do not iron.",
            "modelInfo": "Model is 6'1\" (185cm), 165 lbs (75kg), wearing size Large for an architectural boxy drape.",
            "weight_gsm": 340,
            "weight_kg": 0.85,
            "details": [
                "Water-repellent matte-finish technical nylon shell with breathable micro-mesh lining",
                "Two-way YKK waterproof front zip with ergonomic custom zipper pullers",
                "Precision contrast white piping and angular multi-panel architectural tailoring",
                "Concealed elastic storm cuffs and adjustable bungee hem cinch system",
                "Interior zippered chest pocket and deep weather-sealed hand pockets"
            ],
            "sizeGuide": {
                "S": {"chest": "118 cm / 46.5 in", "length": "67 cm / 26.4 in", "shoulder": "52 cm / 20.5 in", "sleeve": "63 cm / 24.8 in"},
                "M": {"chest": "122 cm / 48.0 in", "length": "69 cm / 27.2 in", "shoulder": "54 cm / 21.3 in", "sleeve": "64 cm / 25.2 in"},
                "L": {"chest": "128 cm / 50.4 in", "length": "71 cm / 28.0 in", "shoulder": "56 cm / 22.0 in", "sleeve": "65 cm / 25.6 in"},
                "XL": {"chest": "134 cm / 52.8 in", "length": "73 cm / 28.7 in", "shoulder": "58 cm / 22.8 in", "sleeve": "66 cm / 26.0 in"},
                "2XL": {"chest": "140 cm / 55.1 in", "length": "75 cm / 29.5 in", "shoulder": "60 cm / 23.6 in", "sleeve": "67 cm / 26.4 in"}
            }
        }
    elif any(k in name_lower for k in ("tee", "t-shirt", "shirt")) or cat_lower in ("tees", "shirts"):
        return {
            "material": "280 GSM Heavyweight 100% Combed Compact Jersey Cotton",
            "care": "Machine wash cold inside out with gentle detergent. Hang dry. Do not iron directly on print.",
            "modelInfo": "Model is 6'1\" (185cm) wearing size Large for a boxy drop-shoulder cut.",
            "weight_gsm": 280,
            "weight_kg": 0.28,
            "details": [
                "280 GSM premium compact-spun combed cotton for zero pilling",
                "Thick 1.25\" seamless ribbed crewneck collar engineered to maintain shape",
                "Relaxed drop-shoulder streetwear cut with wide, structured half-sleeves",
                "Enzyme-washed for a broken-in luxury hand feel and dimensional color depth",
                "Blind-stitched hems and reinforced neck tape for structural longevity"
            ],
            "sizeGuide": {
                "S": {"chest": "112 cm / 44.1 in", "length": "70 cm / 27.6 in", "shoulder": "52 cm / 20.5 in", "sleeve": "22 cm / 8.7 in"},
                "M": {"chest": "116 cm / 45.7 in", "length": "72 cm / 28.3 in", "shoulder": "54 cm / 21.3 in", "sleeve": "23 cm / 9.1 in"},
                "L": {"chest": "122 cm / 48.0 in", "length": "74 cm / 29.1 in", "shoulder": "56 cm / 22.0 in", "sleeve": "24 cm / 9.4 in"},
                "XL": {"chest": "128 cm / 50.4 in", "length": "76 cm / 29.9 in", "shoulder": "58 cm / 22.8 in", "sleeve": "25 cm / 9.8 in"},
                "2XL": {"chest": "134 cm / 52.8 in", "length": "78 cm / 30.7 in", "shoulder": "60 cm / 23.6 in", "sleeve": "26 cm / 10.2 in"}
            }
        }
    else:  # Default hoodie / crewneck / tops
        return {
            "material": "480 GSM Ultra-Heavyweight 100% French Terry Cotton",
            "care": "Machine wash cold inside out with like colors. Hang dry in shade. Do not bleach or tumble dry. Cool iron on reverse.",
            "modelInfo": "Model is 6'1\" (185cm), 165 lbs (75kg), wearing size Large for an oversized boxy streetwear fit.",
            "weight_gsm": 480,
            "weight_kg": 0.65,
            "details": [
                "Custom 480 GSM ultra-heavyweight combed cotton terry with loopback interior",
                "Double-layered architectural hood engineered without drawstrings for a sleek minimalist profile",
                "Pronounced drop shoulders with a wide, boxy body silhouette",
                "Heavy-gauge 2x2 ribbed cuffs and hem for lifetime shape retention",
                "Pre-shrunk vintage wash treatment for a rich textured patina"
            ],
            "sizeGuide": {
                "S": {"chest": "116 cm / 45.7 in", "length": "68 cm / 26.8 in", "shoulder": "54 cm / 21.3 in", "sleeve": "61 cm / 24.0 in"},
                "M": {"chest": "120 cm / 47.2 in", "length": "70 cm / 27.6 in", "shoulder": "56 cm / 22.0 in", "sleeve": "62 cm / 24.4 in"},
                "L": {"chest": "126 cm / 49.6 in", "length": "72 cm / 28.3 in", "shoulder": "58 cm / 22.8 in", "sleeve": "63 cm / 24.8 in"},
                "XL": {"chest": "132 cm / 52.0 in", "length": "74 cm / 29.1 in", "shoulder": "60 cm / 23.6 in", "sleeve": "64 cm / 25.2 in"},
                "2XL": {"chest": "138 cm / 54.3 in", "length": "76 cm / 29.9 in", "shoulder": "62 cm / 24.4 in", "sleeve": "65 cm / 25.6 in"}
            }
        }


def clean_product_description(raw_desc: str, item_name: str) -> str:
    """Clean Chinese descriptions and ensure luxury editorial copy.
    Rule 16: Never expose Chinese prices, yuan symbols, or supplier text on storefront.
    """
    if not raw_desc:
        return f"Curated piece: {item_name}. Heavyweight construction, deconstructed silhouette."
    # If contains Chinese, currency symbols, or seller codes
    if re.search(r'[\u4e00-\u9fff\uffe5¥￥]|\b\d+\s*(?:yuan|rmb|cny|@cn)\b|item\.html', raw_desc, re.IGNORECASE) or len(raw_desc.strip()) < 15:
        return f"Curated luxury essential: {item_name}. Heavyweight architectural construction, premium drape, and deconstructed brutalist aesthetic."
    # Strip any leaked supplier links or prices
    clean = re.sub(r'https?://\S+', '', raw_desc)
    clean = re.sub(r'[￥¥]\d+', '', clean).strip()
    return clean or f"Curated piece: {item_name}. Heavyweight construction, deconstructed silhouette."


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
    
    # Check for JSON metadata files
    for f in campaign_dir.iterdir():
        if f.suffix == ".json" and f.name not in ("checkout_links.json", "outfit_metadata.json"):
            try:
                with open(f, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
                    
                    # Detect if this is the new unified product_record.json schema
                    is_unified_record = "variants" in meta and isinstance(meta["variants"], dict) and "colors" in meta["variants"]
                    
                    if is_unified_record:
                        # Parse new unified schema
                        metadata["product_name"] = meta.get("product_name")
                        
                        # Extract color variant from campaign folder suffix
                        # Reverse-match against known colors (handles multi-word like Light_Blue)
                        folder_lower = campaign_dir.name.lower()
                        color_found = "Default"
                        # Sort by longest name first to match 'multi_color' before 'color'
                        sorted_colors = sorted(meta["variants"]["colors"], key=lambda c: len(c.get("english", "")), reverse=True)
                        for v in sorted_colors:
                            color_key = v["english"].lower().replace(" ", "_")
                            if folder_lower.endswith("_" + color_key):
                                color_found = v["english"]
                                break
                        # Normalize color names (e.g. Camouflage_Brown -> Camo Brown, Light_Blue -> Light Blue)
                        if color_found and color_found != "Default":
                            color_found = color_found.replace("_", " ").title()
                            color_found = color_found.replace("Camouflage", "Camo")
                        metadata["color"] = color_found
                        
                        metadata["part"] = meta.get("part")
                        metadata["is_set"] = meta.get("is_set", False)
                        metadata["set_partner"] = meta.get("set_partner")
                        
                        ordering = meta.get("ordering", {})
                        metadata["link"] = ordering.get("weidian_url", "")
                        metadata["platform"] = ordering.get("platform", "")
                        metadata["item_id"] = ordering.get("item_id", "")
                        metadata["seller"] = ordering.get("seller", {})
                        
                        pricing = meta.get("pricing", {})
                        metadata["price"] = pricing.get("cost_cny", 0)
                        metadata["currency"] = "CNY"
                        
                        metadata["category"] = meta.get("category", "")
                        
                        # Reconstruct variant mappings for storefront compatibility
                        colors_map = {c["english"]: c["chinese"] for c in meta["variants"]["colors"] if "english" in c}
                        sizes_map = meta["variants"].get("size_mappings", {})
                        metadata["variant_mappings"] = {
                            "colors": colors_map,
                            "sizes": sizes_map
                        }
                        
                        if sizes_map:
                            metadata["size_info"] = "Sizes: " + ", ".join(sizes_map.keys())
                        
                        metadata["material"] = meta.get("material", "")
                        metadata["weight_gsm"] = meta.get("weight_gsm", 0)
                        metadata["measurements"] = meta.get("measurements", {})
                        metadata["model_info"] = meta.get("model_info", "")
                        metadata["care_instructions"] = meta.get("care", "")
                        metadata["brand_name"] = meta.get("brand", "")
                        metadata["product_category"] = meta.get("category", "")
                        
                        # Reconstruct stock status
                        stock_status = {}
                        for c in meta["variants"]["colors"]:
                            c_en = c["english"].replace("_", " ").title().replace("Camouflage", "Camo")
                            for sz, instock in c.get("stock", {}).items():
                                stock_status[f"{c_en}-{sz}"] = instock
                        metadata["stock_status"] = stock_status
                        metadata["description"] = meta.get("description", "")
                    else:
                        # Parse old metadata.json schema
                        metadata["product_name"] = meta.get("product_name") or meta.get("name")
                        metadata["color"] = meta.get("color")
                        metadata["part"] = meta.get("part")
                        metadata["is_set"] = meta.get("is_set", False)
                        metadata["set_partner"] = meta.get("set_partner")
                        metadata["link"] = meta.get("link", "") or meta.get("url", "")
                        metadata["price"] = meta.get("price_cny") or meta.get("price") or 0
                        metadata["category"] = meta.get("category", "")
                        metadata["currency"] = meta.get("currency") or ("USD" if "$" in str(metadata["price"]) else "CNY")
                        metadata["size_info"] = meta.get("size_info")
                        metadata["size_charts"] = meta.get("size_charts", 0)
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
    
    # Collect images for the main product gallery:
    # 1. AI-generated model shots (01_model_front_0.png etc.)
    # 2. Gallery-ready flat lay images (front_flat_lay.jpg, back_flat_lay.jpg)
    # These are the actual downloaded source photos used directly as flat lays.
    gallery_names = ("front_flat_lay", "back_flat_lay", "top_front_flat_lay", "top_back_flat_lay", "bottom_front_flat_lay", "bottom_back_flat_lay", "front_angle_1", "back_angle_1", "front_angle_2", "back_angle_2")
    for f in sorted(campaign_dir.iterdir()):
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            # Include AI generated model shots or scraped product shots
            if f.name.startswith(("01_", "02_", "03_", "04_", "05_", "angle_", "img_", "product_")) or any(t in f.name.lower() for t in ("editorial", "lifestyle", "ghost", "hero", "angle")):
                metadata["images"].append(f)
            # Include gallery-ready flat lay images (downloaded source photos)
            elif f.stem.lower() in gallery_names:
                metadata["images"].append(f)
    
    # Fallback: if no specific image pattern matched, include all image files in the directory
    if not metadata["images"]:
        for f in sorted(campaign_dir.iterdir()):
            if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                metadata["images"].append(f)
    
    # Collect remaining source images for the secondary details/photos tab
    metadata["source_images"] = []
    source_prefixes = ("source_", "detail_close_")
    for f in sorted(campaign_dir.iterdir()):
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            if f.stem.startswith(source_prefixes):
                metadata["source_images"].append(f)
    
    return metadata


def copy_size_charts_to_public(campaign_dir, product_slug):
    """Find size chart images in the campaign folder (or parent product directory) and copy them to public/products/<slug>/."""
    product_dir = PUBLIC_DIR / product_slug
    product_dir.mkdir(parents=True, exist_ok=True)
    
    dirs_to_check = [campaign_dir]
    if campaign_dir.parent and campaign_dir.parent.exists() and campaign_dir.parent.name not in ("MANUAL_CURATION", "OUTPUT_READY_FOR_SALE", "goal2_sourcing_engine"):
        dirs_to_check.append(campaign_dir.parent)
        
    web_paths = []
    seen_names = set()
    for d in dirs_to_check:
        for f in d.iterdir():
            if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                if any(k in f.name.lower() for k in ("chart", "size", "guide")) and f.name not in seen_names:
                    seen_names.add(f.name)
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
    """Copy generated images and flat lay photos to the Next.js public/products/ directory.
    Handles mixed file extensions (.png for AI model shots, .jpg for source flat lays)."""
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
    "black": "#111111", "white": "#FFFFFF", "red": "#C41E3A",
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
    "light blue": "#60A5FA", "emerald green": "#50C878", "emerald": "#50C878",
    "tree camo": "#4A5D23", "camo brown": "#8B7355", "camo": "#556B2F",
    "forest": "#228B22", "slate": "#708090", "steel": "#71797E",
    "midnight": "#191970", "ash": "#B2BEB5", "graphite": "#41424C",
    "silver": "#C0C0C0", "bone": "#E3DAC9", "stone": "#928E85",
    "army green": "#4B5320", "army_green": "#4B5320",
    "dark blue": "#0F172A", "dark_blue": "#0F172A", "navy blue": "#1E3A8A", "navy_blue": "#1E3A8A",
    "dark gray": "#334155", "dark_gray": "#334155", "dark grey": "#334155", "dark_grey": "#334155",
    "deep red": "#800020", "deep_red": "#800020",
    "wine red": "#701A75", "wine_red": "#701A75",
    "tangerine red": "#EA580C", "tangerine_red": "#EA580C",
    "off-white": "#F8FAFC", "off_white": "#F8FAFC", "offwhite": "#F8FAFC",
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
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            if any(t in f.name.lower() for t in ("editorial", "lifestyle", "urban")):
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
    """Main function: scan OUTPUT_READY_FOR_SALE and MANUAL_CURATION and upload to storefront."""
    campaigns = []
    if READY_DIR.exists():
        # ⚡ Performance optimization
        # Why: Prevent N+1 stat calls when iterating directories
        # What: Use os.scandir instead of Path.iterdir + is_dir
        with os.scandir(READY_DIR) as scanner:
            campaigns.extend([Path(e.path) for e in scanner if e.is_dir()])
    
    if not campaigns:
        log("No campaigns to upload.")
        return
    
    uploaded = get_uploaded_log()
    
    uploaded_names = set()
    uploaded_product_ids = set()
    for item in uploaded:
        if isinstance(item, dict):
            if "name" in item:
                uploaded_names.add(item["name"])
            if "product_id" in item:
                uploaded_product_ids.add(item["product_id"])
        else:
            uploaded_names.add(item)
            c_dir = READY_DIR / item
            if c_dir.exists():
                c_info = c_dir / "campaign_info.json"
                if c_info.exists():
                    try:
                        ci = json.loads(c_info.read_text(encoding="utf-8"))
                        pid = ci.get("product_id")
                        if pid:
                            uploaded_product_ids.add(pid)
                    except Exception:
                        pass
    
    # Load existing products from storefront
    existing_products, collections_raw, outfits_raw = load_current_products()
    
    # Group campaigns by product identity (name + link)
    new_items = []
    for campaign_dir in campaigns:
        if campaign_dir.name in uploaded_names:
            continue
            
        campaign_info_file = campaign_dir / "campaign_info.json"
        if campaign_info_file.exists():
            try:
                ci = json.loads(campaign_info_file.read_text(encoding="utf-8"))
                pid = ci.get("product_id", "")
                if pid and pid in uploaded_product_ids:
                    continue
            except Exception:
                pass
        
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
        
        # Group key uses the RAW name for internal grouping (so same raw product = same group)
        if meta["product_name"]:
            raw_group_key = slugify(meta["product_name"])
        else:
            raw_group_key = f"product-{hashlib.md5(campaign_dir.name.encode()).hexdigest()[:8]}"
        
        if raw_group_key not in product_groups:
            clean_name = clean_product_title(meta["product_name"])
            # Public slug uses CLEAN name + hash to prevent brand leaks in URLs
            hash_suffix = hashlib.md5(raw_group_key.encode()).hexdigest()[:6]
            public_slug = f"{slugify(clean_name)}-{hash_suffix}"
            product_groups[raw_group_key] = {
                "name": clean_name,
                "slug": public_slug,
                "link": link,
                "is_set": meta.get("is_set", False),
                "set_partner": meta.get("set_partner"),
                "variants": []
            }
        
        # If ANY variant is a set, mark the whole group as a set
        if meta.get("is_set"):
            product_groups[raw_group_key]["is_set"] = True
        
        # Keyword-based set detection from product name
        set_keywords = ["hoodie trousers", "hoodie & trousers", "hoodie and trousers",
                        "hoodie pants", "tracksuit", "top bottom", "jacket pants",
                        "sweatshirt trousers", "hoodie jogger", "hoodie cargo", "hoodie short", "set"]
        name_lower = (product_groups[raw_group_key]["name"] or "").lower()
        if any(kw in name_lower for kw in set_keywords):
            product_groups[raw_group_key]["is_set"] = True
        
        product_groups[raw_group_key]["variants"].append((campaign_dir, meta))
    
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
        raw_price = first_meta.get("price_cny") or first_meta.get("price", 0)
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
            
            # Floor prices only — prevent selling at a loss, but NEVER override upward
            category_str = (first_meta.get("category") or "").lower()
            name_str = (first_meta.get("product_name") or group["name"] or "").lower()
            is_tshirt = "tee" in name_str or "t-shirt" in name_str or "shirt" in name_str or "t恤" in name_str or "top" in category_str
            is_jacket = "jacket" in name_str or "coat" in name_str or "puffer" in name_str or "outerwear" in category_str
            is_set = group.get("is_set", False)
            
            if is_set:
                sell_price = max(sell_price, 69)   # Sets floor: $69
            elif is_jacket:
                sell_price = max(sell_price, 59)   # Jacket floor: $59
            elif is_tshirt and not any(k in name_str for k in ("hoodie", "sweatshirt", "jacket", "coat", "puffer")):
                sell_price = max(sell_price, 39)   # Tee floor: $39
            else:
                sell_price = max(sell_price, 29)   # Accessories/other floor: $29
        else:
            # No source price available — estimate based on garment type
            name_str = (first_meta.get("product_name") or group["name"] or "").lower()
            if group.get("is_set", False) or ("hoodie" in name_str and ("trousers" in name_str or "pants" in name_str)):
                sell_price = 129  # Sets default
            elif "jacket" in name_str or "coat" in name_str:
                sell_price = 109  # Jackets default
            elif "hoodie" in name_str or "sweatshirt" in name_str:
                sell_price = 79   # Hoodies default
            elif "tee" in name_str or "t-shirt" in name_str or "shirt" in name_str:
                sell_price = 49   # Tees default
            else:
                sell_price = 69   # General default
        
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
        
        NON_COLOR_KEYS = {"group_shots", "group shots", "size_chart", "size_charts", "details", "detail"}
        for campaign_dir, meta in group["variants"]:
            color_name = meta["color"] or "Default"
            color_clean = color_name.replace("_", " ").strip()
            
            # Skip non-color buckets from becoming a color swatch option
            is_non_color = color_clean.lower() in NON_COLOR_KEYS
            
            color_slug = slugify(color_name)
            color_hex = COLOR_HEX_MAP.get(color_clean.lower(), "#888888")
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
            
            if is_non_color:
                if web_paths:
                    all_images.extend(web_paths)
                pid = meta.get("product_id", "")
                if pid:
                    uploaded.append({"name": campaign_dir.name, "product_id": pid})
                else:
                    uploaded.append(campaign_dir.name)
                continue

            # Merge images by color — top images first, then bottom
            if color_clean not in color_buckets:
                color_buckets[color_clean] = {"images": [], "hex": color_hex, "parts": []}
            
            # Sort order: top images come before bottom images
            if part and part.lower() == "top":
                color_buckets[color_clean]["images"] = web_paths + color_buckets[color_clean]["images"]
                color_buckets[color_clean]["parts"].insert(0, "top")
            else:
                color_buckets[color_clean]["images"].extend(web_paths)
                if part:
                    color_buckets[color_clean]["parts"].append(part)
            
            if not all_images:
                all_images = web_paths
            
            # Mark as uploaded
            pid = meta.get("product_id", "")
            if pid:
                uploaded.append({"name": campaign_dir.name, "product_id": pid})
            else:
                uploaded.append(campaign_dir.name)
        
        # Build final colors list from merged buckets
        for color_name, bucket in color_buckets.items():
            colors.append({
                "name": color_name.title(),
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
            # Update product colors with fresh campaign color swatches
            if colors:
                final_products[existing_idx]["colors"] = colors
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
            # Build new product entry with rich luxury specs
            specs = generate_luxury_specs(group["name"], ui_category, is_set=group.get("is_set", False))
            product_entry = {
                "id": product_slug,
                "name": group["name"],
                "price": sell_price,
                "comparePrice": round(sell_price * 1.30),  # 30% higher "was" price for sale urgency
                "category": ui_category,
                "badge": "Co-ord Set" if group.get("is_set") else "New Drop",
                "isSet": group.get("is_set", False),
                "description": clean_product_description(first_meta.get("description", ""), group["name"]),
                "material": first_meta.get("material") or specs["material"],
                "care": first_meta.get("care_instructions") or specs["care"],
                "modelInfo": first_meta.get("model_info") or specs["modelInfo"],
                "weightGsm": first_meta.get("weight_gsm") or specs["weight_gsm"],
                "weightKg": specs["weight_kg"],
                "brand": "OBSCURA",  # Always use our brand on storefront — never expose supplier brands
                "sizes": parsed_sizes,
                "sizeGuide": first_meta.get("measurements") or specs["sizeGuide"],
                "images": all_images,
                "colors": colors if len(colors) > 1 or (len(colors) == 1 and colors[0]["name"] != "Default") else [],
                "details": first_meta.get("details") or specs["details"],
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
                "weight_kg": specs["weight_kg"],
                "category": ui_category,
                "is_set": group.get("is_set", False),
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
    final_products_by_id = {p["id"]: p for p in final_products}
    for group_key, group in product_groups.items():
        if group.get("is_set"):
            this_product = final_products_by_id.get(group["slug"])
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
                if any(kw in p_cat or kw in p_name for kw in SHOE_KEYWORDS):
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
