"""
STYLE TAGGER — AI-Powered Fashion Intelligence
================================================
Uses Gemini Vision (FREE) to analyze product images and output structured
style tags that drive the Auto-Matcher and Scene Director.

Tags per product:
  - gender:        "men" | "women" | "unisex"
  - niche:         "streetwear" | "elegant" | "athleisure" | "techwear" | "y2k" | "basics" | "formal"
  - category:      "top" | "bottom" | "outerwear" | "shoes" | "accessory" | "set" | "dress"
  - sub_category:  "hoodie" | "tee" | "jacket" | "shorts" | "skirt" | "sneakers" | "bag" etc.
  - colors:        ["black", "cream"] 
  - compatible_with: ["skirt", "wide_leg_pants"] — what SHOULD be paired with this
  - weight_kg:     estimated shipping weight (for Kakobuy cost calculation)
  - scene_style:   "gritty_urban" | "soft_studio" | "sport_court" | "minimal_clean"
  - solo_only:     bool — true if item should NEVER be merged (e.g. accessories, shoes)
"""

import os
import re
import json
import base64
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from litellm_router import shared_router

load_dotenv(Path(__file__).parent / ".env")

log = logging.getLogger("style_tagger")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [TAGGER] %(message)s")


# ── Gemini Key Pool ─────────────────────────────────────────────
def get_gemini_keys():
    keys = []
    for k, v in os.environ.items():
        if k.startswith("GEMINI_API_KEY") and v:
            keys.append(v)
    return keys


# ── Estimated weights by sub_category (kg) ──────────────────────
# Used for Kakobuy shipping cost estimation
WEIGHT_ESTIMATES = {
    "tee":        0.25,
    "shirt":      0.30,
    "hoodie":     0.60,
    "sweatshirt": 0.55,
    "jacket":     0.90,
    "coat":       1.20,
    "puffer":     1.10,
    "vest":       0.45,
    "shorts":     0.35,
    "pants":      0.55,
    "jeans":      0.70,
    "joggers":    0.50,
    "skirt":      0.35,
    "dress":      0.55,
    "set":        0.80,
    "sneakers":   0.90,
    "boots":      1.20,
    "sandals":    0.50,
    "slides":     0.40,
    "bag":        0.60,
    "backpack":   0.80,
    "hat":        0.15,
    "cap":        0.15,
    "belt":       0.20,
    "chain":      0.15,
    "watch":      0.25,
    "sunglasses": 0.10,
    "socks":      0.10,
    "default":    0.40,
}

# ── Scene style mapping ─────────────────────────────────────────
NICHE_TO_SCENE = {
    "streetwear":  "gritty_urban",
    "techwear":    "gritty_urban",
    "y2k":         "gritty_urban",
    "elegant":     "soft_studio",
    "formal":      "soft_studio",
    "athleisure":  "sport_court",
    "basics":      "minimal_clean",
}

# Items that should NEVER be merged with other products for model shots
SOLO_ONLY_CATEGORIES = {"shoes", "accessory"}


# ── Tag a single product folder ─────────────────────────────────
def tag_product(product_dir: Path) -> dict:
    """
    Analyze product images in a folder using Gemini Vision.
    Returns a style_tags dict and saves it to style_tags.json.
    """
    product_dir = Path(product_dir)
    tags_file = product_dir / "style_tags.json"

    # Skip if already tagged
    if tags_file.exists():
        try:
            return json.loads(tags_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Load product metadata for context
    meta = {}
    meta_file = product_dir / "metadata.json"
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    product_name = meta.get("product_name", product_dir.name)
    price_cny = meta.get("price_cny", 0)

    # Check for pre-computed image classification (from auto_image_classifier.py)
    classification_file = product_dir / "image_classification.json"
    pre_classified = {}
    if classification_file.exists():
        try:
            cls_data = json.loads(classification_file.read_text(encoding="utf-8"))
            summary = cls_data.get("product_summary", {})
            if summary:
                pre_classified = {
                    "sub_category": summary.get("garment_type"),
                    "colors": [c for c in [summary.get("primary_color")] + summary.get("secondary_colors", []) if c],
                }
                log.info(f"  Using pre-classified data: {summary.get('garment_type')} / {summary.get('primary_color')}")
        except Exception:
            pass

    # Find product images (exclude size charts)
    images = [
        f for f in product_dir.glob("*")
        if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
        and "size" not in f.name.lower()
        and "chart" not in f.name.lower()
    ]

    # First try keyword-based tagging (fast, no API call needed)
    tags = _keyword_tag(product_name, price_cny)

    # Merge pre-classified data (from auto_image_classifier) over keyword tags
    if pre_classified:
        tags.update({k: v for k, v in pre_classified.items() if v})

    # If we have images, upgrade with vision via LiteLLM router
    # Use front_angle image if available (VLM-classified), otherwise first image
    if images:
        best_image = next(
            (f for f in images if f.name.startswith("front_angle")),
            images[0]
        )
        vision_tags = _gemini_vision_tag(best_image, product_name)
        if vision_tags:
            # Merge vision tags over keyword tags (vision is more accurate)
            tags.update({k: v for k, v in vision_tags.items() if v})

    # Derive computed fields
    tags["scene_style"] = NICHE_TO_SCENE.get(tags.get("niche", ""), "minimal_clean")
    tags["solo_only"] = tags.get("category", "") in SOLO_ONLY_CATEGORIES
    tags["weight_kg"] = WEIGHT_ESTIMATES.get(tags.get("sub_category", "default"), 0.40)
    tags["tagged_at"] = datetime.now().isoformat()
    tags["product_name"] = product_name
    tags["price_cny"] = price_cny

    # Save tags
    tags_file.write_text(json.dumps(tags, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"✅ Tagged: {product_name[:50]} → {tags.get('gender')} {tags.get('niche')} {tags.get('category')}")
    return tags


def _keyword_tag(product_name: str, price_cny: float) -> dict:
    """Fast keyword-based fallback tagger — no API needed."""
    name = product_name.lower()

    # Gender detection
    women_kw = ["women", "woman", "female", "girl", "ladies", "skirt", "dress", "blouse", "bra", "bralette", "bikini", "corset"]
    men_kw = ["men", "man", "male", "boys", "guy"]
    gender = "unisex"
    if any(k in name for k in women_kw):
        gender = "women"
    elif any(k in name for k in men_kw):
        gender = "men"

    # Category + sub_category
    cat_map = {
        "top":       ["hoodie", "tee", "t-shirt", "shirt", "sweatshirt", "sweater", "knit", "crop", "blouse", "longsleeve", "polo", "henley"],
        "bottom":    ["pants", "jeans", "shorts", "joggers", "trousers", "cargo", "skirt", "leggings", "sweatpants"],
        "outerwear": ["jacket", "coat", "puffer", "parka", "windbreaker", "bomber", "vest", "cardigan", "blazer"],
        "shoes":     ["shoe", "sneaker", "jordan", "yeezy", "dunk", "af1", "boot", "sandal", "slide", "loafer", "foam", "trainer"],
        "accessory": ["bag", "backpack", "hat", "cap", "belt", "chain", "ring", "watch", "sunglasses", "socks", "balaclava", "wallet"],
        "dress":     ["dress", "gown", "midi", "maxi", "mini dress"],
        "set":       ["set", "co-ord", "coord", "tracksuit", "matching", "tennis set", "two piece", "2 piece"],
    }
    category = "top"
    sub_category = "tee"
    for cat, keywords in cat_map.items():
        for kw in keywords:
            if kw in name:
                category = cat
                sub_category = kw.replace("-", "").replace(" ", "_")
                break
        else:
            continue
        break

    # Niche detection
    streetwear_kw = ["bape", "supreme", "corteiz", "palace", "stussy", "jordan", "nike", "adidas", "off white", "vlone", "trapstar", "essentials", "fear of god", "rhude", "amiri"]
    elegant_kw = ["silk", "satin", "lace", "blouse", "blazer", "formal", "chiffon", "pleated", "floral", "midi", "maxi", "gown"]
    athleisure_kw = ["tennis", "gym", "sport", "athletic", "yoga", "running", "workout", "compression", "racket"]
    techwear_kw = ["techwear", "tactical", "cargo", "gorpcore", "utility", "shell", "functional"]
    y2k_kw = ["y2k", "2000s", "vintage", "retro", "baggy", "flared", "denim", "low rise"]
    formal_kw = ["suit", "blazer", "dress shirt", "trousers", "formal", "office"]

    niche = "basics"
    if any(k in name for k in streetwear_kw): niche = "streetwear"
    elif any(k in name for k in elegant_kw): niche = "elegant"
    elif any(k in name for k in athleisure_kw): niche = "athleisure"
    elif any(k in name for k in techwear_kw): niche = "techwear"
    elif any(k in name for k in y2k_kw): niche = "y2k"
    elif any(k in name for k in formal_kw): niche = "formal"

    # Compatible pairings
    compatible_map = {
        "hoodie":    {"men": ["cargo_pants", "joggers", "shorts"], "women": ["joggers", "biker_shorts", "mini_skirt"], "unisex": ["cargo_pants", "joggers"]},
        "tee":       {"men": ["cargo_pants", "shorts", "jeans"], "women": ["skirt", "shorts", "jeans"], "unisex": ["cargo_pants", "shorts"]},
        "shirt":     {"men": ["trousers", "chinos", "shorts"], "women": ["skirt", "trousers"], "unisex": ["trousers"]},
        "jacket":    {"men": ["cargo_pants", "jeans", "shorts"], "women": ["skirt", "jeans", "trousers"], "unisex": ["jeans"]},
        "blouse":    {"women": ["skirt", "trousers", "wide_leg_pants"], "unisex": ["trousers"]},
        "skirt":     {"women": ["top", "blouse", "crop_top", "tee"], "unisex": ["top"]},
        "dress":     {"women": [], "unisex": []},  # Dress = solo, no merge
        "set":       {"women": [], "men": [], "unisex": []},  # Sets = solo
        "shorts":    {"men": ["tee", "hoodie", "shirt"], "women": ["tee", "crop_top", "hoodie"], "unisex": ["tee"]},
        "pants":     {"men": ["tee", "hoodie", "shirt"], "women": ["blouse", "top", "crop_top"], "unisex": ["tee"]},
    }
    compatible_with = compatible_map.get(sub_category, {}).get(gender, compatible_map.get(sub_category, {}).get("unisex", []))

    return {
        "gender":          gender,
        "niche":           niche,
        "category":        category,
        "sub_category":    sub_category,
        "colors":          [],  # will be filled from metadata
        "compatible_with": compatible_with,
        "source":          "keyword",
    }


def _gemini_vision_tag(image_path: Path, product_name: str) -> dict:
    """Use Gemini Vision via LiteLLM router to analyze a product image and return style tags."""
    try:
        prompt = f"""You are a professional fashion buyer and stylist. Analyze this product image.
Product name hint: "{product_name}"

Return ONLY a valid JSON object (no markdown, no explanation) with these exact fields:
{{
  "gender": "men" | "women" | "unisex",
  "niche": "streetwear" | "elegant" | "athleisure" | "techwear" | "y2k" | "basics" | "formal" | "gorpcore" | "vintage" | "avant_garde",
  "category": "top" | "bottom" | "outerwear" | "shoes" | "accessory" | "dress" | "set",
  "sub_category": single word like "hoodie", "tee", "skirt", "sneakers", "jacket", "shorts", etc.,
  "colors": [list of color names visible in the product, max 3],
  "compatible_with": [list of item types this pairs well with, e.g. "cargo_pants", "skirt", "tee"],
  "confidence": "high" | "medium" | "low",
  "custom_scene": "Write a highly specific 1-sentence photography scene for this item (e.g. 'standing next to a vintage Porsche 911 at dusk in the Hollywood hills' or 'seated at a Parisian cafe reading a magazine')",
  "custom_lighting": "Describe the lighting (e.g. 'golden hour backlighting with soft fill' or 'harsh paparazzi flash at night')",
  "custom_camera": "Describe the camera (e.g. 'shot on 35mm film, grainy, cinematic' or 'digital medium format, razor sharp')",
  "custom_mood": "Describe the vibe (e.g. 'effortless old money luxury' or 'gritty underground youth culture')"
}}

Rules:
- "dress" and "set" items have empty compatible_with (they're solo pieces)
- Shoes and accessories always have empty compatible_with (they're solo pieces)  
- Be specific about colors (e.g. "sage_green" not just "green")
- gender "women" for obviously feminine cuts/styles even if no text says so
- The custom fields MUST match the exact aesthetic of the clothing. If it's a techwear jacket, make the scene cyberpunk/industrial. If it's a silk skirt, make it soft/luxury."""

        # Read and downscale image to 512x512 JPEG
        try:
            from PIL import Image
            import io
            img = Image.open(image_path).convert("RGB")
            img.thumbnail((512, 512))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75)
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            mime = "image/jpeg"
        except Exception:
            with open(image_path, "rb") as f:
                img_bytes = f.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            ext = image_path.suffix.lower()
            mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")


        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{img_b64}"
                        }
                    }
                ]
            }
        ]

        response = shared_router.get_chat_completion_sync(
            messages=messages,
            primary_model="gemini-flash",
            temperature=1.0,
            response_format={"type": "json_object"}
        )
        response_text = response.choices[0].message.content.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()

        result = json.loads(response_text)
        result["source"] = f"litellm_router_{response.get('model', 'gemini')}"
        log.info(f"  🔍 Vision tagged with LiteLLM router: {result.get('gender')} {result.get('niche')} {result.get('sub_category')}")
        return result

    except Exception as e:
        log.error(f"Vision tagging error: {e}")

    return {}


# ── Batch tag all untagged products in MANUAL_CURATION ──────────
def tag_all_pending(curation_dir: Path = None):
    if curation_dir is None:
        curation_dir = Path(__file__).parent / "MANUAL_CURATION"

    # ⚡ Performance optimization
    # Why: Prevent N+1 stat calls when iterating directories
    # What: Use os.scandir instead of Path.iterdir + is_dir
    with os.scandir(curation_dir) as scanner:
        folders = [Path(e.path) for e in scanner if e.is_dir()]
    untagged = [f for f in folders if not (f / "style_tags.json").exists()]

    log.info(f"Found {len(untagged)} untagged products out of {len(folders)} total")

    for folder in untagged:
        try:
            tag_product(folder)
        except Exception as e:
            log.error(f"Failed to tag {folder.name}: {e}")

    log.info("✅ Tagging complete")


# ── CLI ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        tag_product(Path(sys.argv[1]))
    else:
        tag_all_pending()
