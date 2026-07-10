"""
VTON Photo Pipeline v3 — Powered by FlowBridge (Zero API Keys)
==============================================================
Replaces ALL paid VTON APIs (FASHN, PerfectCorp, Pixelforge) with
browser-automated Nano Banana Pro on Google AI Studio Flow.

Uses the 14-image Multi-Reference Lock for maximum consistency:
  Slots 1-5:  Character sheet (5 angles of the model)
  Slots 6-14: Product photos (multiple angles of the garment/shoe/accessory)

Cost: $0 (browser automation on free web UI)
"""
import os
import random
from typing import List, Dict, Optional

from prompt_library import (
    get_prompts_for_product,
    CLOTHING_PROMPTS,
    SHOE_PROMPTS,
    ACCESSORY_PROMPTS,
    BEAUTY_PROMPTS,
    CANDID_FILTERS,
)

# ==========================================
# CONFIGURATION
# ==========================================
CHARACTER_SHEETS_DIR = os.path.join(os.getcwd(), "models", "character_sheets")
OUTPUT_DIR = os.path.join(os.getcwd(), "output", "vton")

# 10-Model Roster — Each model has FACE sheet + BODY sheet
# Face sheet: 3 angles (front, 3/4, profile)  → locks facial identity
# Body sheet: 3 angles (front, side, back)     → locks height, weight, proportions
MODEL_ROSTER = {
    # WOMEN (6 models covering all niches)
    "female_1": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "f1_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "f1_body.png"),
        "vibe": "streetwear",      # Confident, athletic — streetwear, activewear
        "ethnicity": "mixed",
    },
    "female_2": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "f2_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "f2_body.png"),
        "vibe": "classy",          # Elegant, slim — formal, evening
        "ethnicity": "east_asian",
    },
    "female_3": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "f3_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "f3_body.png"),
        "vibe": "editorial",       # Edgy, angular — high fashion
        "ethnicity": "european",
    },
    "female_4": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "f4_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "f4_body.png"),
        "vibe": "casual",          # Curvy, warm — casual, summer
        "ethnicity": "latina",
    },
    "female_5": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "f5_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "f5_body.png"),
        "vibe": "elegant",         # Graceful, tall — modest fashion
        "ethnicity": "south_asian",
    },
    "female_6": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "f6_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "f6_body.png"),
        "vibe": "bold",            # Bold, short hair — statement pieces
        "ethnicity": "black",
    },
    # MEN (4 models)
    "male_1": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "m1_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "m1_body.png"),
        "vibe": "streetwear",      # Athletic — streetwear, sportswear
        "ethnicity": "black",
    },
    "male_2": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "m2_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "m2_body.png"),
        "vibe": "classy",          # Clean-cut — business casual
        "ethnicity": "european",
    },
    "male_3": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "m3_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "m3_body.png"),
        "vibe": "elegant",         # Strong, beard — premium, luxury
        "ethnicity": "middle_eastern",
    },
    "male_4": {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "m4_face.png"),
        "body": os.path.join(CHARACTER_SHEETS_DIR, "m4_body.png"),
        "vibe": "casual",          # Slim, youthful — K-fashion, trendy
        "ethnicity": "east_asian",
    },
}

# Map product styles to model vibes for smart matching
STYLE_TO_VIBE = {
    "sporty": "streetwear",
    "streetwear": "streetwear",
    "formal": "classy",
    "classy": "classy",
    "evening": "elegant",
    "casual": "casual",
    "editorial": "editorial",
    "bold": "bold",
    "luxury": "elegant",
    "summer": "casual",
}


def detect_product_type(product: dict) -> str:
    """
    Determines whether a product is clothing, shoes, accessories, or beauty
    based on its category or keywords in the product name/description.
    """
    name = product.get("productName", "").lower()
    category = product.get("category", "").lower()
    combined = f"{name} {category}"

    shoe_keywords = ["shoe", "sneaker", "boot", "trainer", "runner", "heel",
                     "sandal", "loafer", "canvas", "kicks"]
    accessory_keywords = ["watch", "sunglasses", "glasses", "belt", "wallet",
                          "bag", "jewelry", "necklace", "bracelet", "ring",
                          "earring", "hat", "cap", "chain"]
    beauty_keywords = ["perfume", "fragrance", "cologne", "skincare", "serum",
                       "moisturizer", "soap", "cream", "lotion"]

    if any(kw in combined for kw in shoe_keywords):
        return "shoes"
    elif any(kw in combined for kw in accessory_keywords):
        return "accessories"
    elif any(kw in combined for kw in beauty_keywords):
        return "beauty"
    else:
        return "clothing"


def pick_model(product_type: str, gender: str = "female", style: str = None) -> dict:
    """
    Picks the best model from the roster based on product type and style.
    Returns dict with 'face' and 'body' paths.
    Falls back gracefully if sheets don't exist yet.
    """
    prefix = "female" if gender == "female" else "male"
    target_vibe = STYLE_TO_VIBE.get(style, None)
    
    # Try to find a style-matched model with existing sheets
    if target_vibe:
        style_matched = [
            (k, v) for k, v in MODEL_ROSTER.items()
            if k.startswith(prefix)
            and v.get("vibe") == target_vibe
            and (os.path.exists(v["face"]) or os.path.exists(v["body"]))
        ]
        if style_matched:
            key, model = random.choice(style_matched)
            return model
    
    # Fallback: any model with existing sheets
    available = [
        (k, v) for k, v in MODEL_ROSTER.items()
        if k.startswith(prefix)
        and (os.path.exists(v["face"]) or os.path.exists(v["body"]))
    ]
    if not available:
        # Try any gender
        available = [
            (k, v) for k, v in MODEL_ROSTER.items()
            if os.path.exists(v["face"]) or os.path.exists(v["body"])
        ]
    
    if available:
        key, model = random.choice(available)
        return model
    
    # No sheets exist yet — return placeholder
    return {
        "face": os.path.join(CHARACTER_SHEETS_DIR, "primary_model.png"),
        "body": "",
    }


def build_reference_list(
    model: dict,
    product_images: List[str],
    pose_ref: str = None,
    max_refs: int = 14
) -> List[str]:
    """
    Build the Multi-Reference Lock payload using the full 14-slot system:
    
      Slots 1-3:   FACE references (3 angles from face sheet)
      Slots 4-6:   BODY references (3 angles from body sheet)  
      Slot 7:      POSE reference (optional — specific pose to match)
      Slots 8-14:  PRODUCT photos (the actual garments/shoes/accessories)
    
    This allocation locks both facial identity AND body proportions,
    preventing the AI from hallucinating different heights/weights.
    """
    refs = []

    # Slots 1-3: Face references
    face_path = model.get("face", "") if isinstance(model, dict) else model
    if face_path and os.path.exists(face_path):
        refs.append(face_path)

    # Slots 4-6: Body references  
    body_path = model.get("body", "") if isinstance(model, dict) else ""
    if body_path and os.path.exists(body_path):
        refs.append(body_path)

    # Slot 7: Pose reference (optional)
    if pose_ref and os.path.exists(pose_ref):
        refs.append(pose_ref)

    # Slots 8-14: Product images
    for img in product_images:
        if os.path.exists(img) and len(refs) < max_refs:
            refs.append(img)

    return refs


async def generate_vton_images(
    product: dict,
    character_sheet: Optional[str] = None,
    product_images: Optional[List[str]] = None,
    num_prompts: int = 3,
    apply_candid_filter: bool = True,
) -> List[str]:
    """
    Generate VTON (Virtual Try-On) images using FlowBridge browser automation.

    Args:
        product: Product dict with productName, category, etc.
        character_sheet: Path to the 5-angle character sheet PNG
        product_images: List of product photo paths
        num_prompts: How many prompt variations to generate
        apply_candid_filter: Whether to append anti-AI-blindness filters

    Returns:
        List of generated image file paths
    """
    from flow_bridge import FlowBridge

    product_name = product.get("productName", "product")
    product_type = detect_product_type(product)
    safe_name = product_name.replace(" ", "_")[:25].lower()

    print(f"\n📸 VTON PIPELINE v3: '{product_name}'")
    print(f"   Type: {product_type.upper()}")

    # Pick a model if none specified
    if not character_sheet:
        character_sheet = pick_model(product_type)

    # Build product image list
    if not product_images:
        product_images = []
        img_path = product.get("productImage", product.get("_image_path", ""))
        if img_path and os.path.exists(img_path):
            product_images.append(img_path)

    # Build reference payload
    refs = build_reference_list(character_sheet, product_images)
    print(f"   References: {len(refs)} images ({1 if refs else 0} character + {len(refs)-1 if refs else 0} product)")

    # Get prompt set for this product type
    prompt_set = get_prompts_for_product(product_type)
    prompt_keys = list(prompt_set.keys())[:num_prompts]

    # Create output directory
    product_dir = os.path.join(OUTPUT_DIR, safe_name)
    os.makedirs(product_dir, exist_ok=True)

    # Launch browser and generate
    bridge = FlowBridge(headless=True)
    await bridge.start()

    all_images = []

    for i, key in enumerate(prompt_keys):
        prompt = prompt_set[key]

        # Append candid filter to fight AI Blindness
        if apply_candid_filter:
            prompt = f"{prompt} {CANDID_FILTERS}"

        print(f"\n   🎨 Generating [{key}] ({i+1}/{len(prompt_keys)})...")

        images = await bridge.generate_image(
            prompt=prompt,
            reference_images=refs if refs else None,
            output_prefix=f"{safe_name}_{key}",
            aspect="3:4",      # Instagram portrait
            multiplier="x4",   # 4 variations per prompt
        )

        # Move to product directory
        for img in images:
            if os.path.exists(img):
                dest = os.path.join(product_dir, os.path.basename(img))
                os.rename(img, dest)
                all_images.append(dest)

        # Reset Flow between generations
        await bridge.page.goto("https://labs.google/fx",
                               wait_until="networkidle", timeout=60000)
        import asyncio
        await asyncio.sleep(3)

    await bridge.close()

    print(f"\n   ✅ VTON complete: {len(all_images)} images → {product_dir}")
    return all_images


def generate_vton_carousel(product: dict) -> list:
    """
    Synchronous entry point for Pipeline B.
    Called by sourcing_engine.py's main orchestrator.
    """
    import asyncio
    return asyncio.run(generate_vton_images(product))


if __name__ == "__main__":
    import asyncio

    test_products = [
        {"productId": "CJ_SN_001", "productName": "Premium Chunky Sneaker Trainer",
         "productImage": "products/sneaker.png", "category": "shoes"},
        {"productId": "DH_ACC_001", "productName": "Luxury Aviator Sunglasses UV400",
         "productImage": "products/sunglasses.png", "category": "accessories"},
        {"productId": "CJ_TS_002", "productName": "Slim Fit Designer Tracksuit Set",
         "productImage": "products/tracksuit.png", "category": "clothing"},
    ]
    for p in test_products:
        images = generate_vton_carousel(p)
        print(f"   Output: {len(images)} images\n")
