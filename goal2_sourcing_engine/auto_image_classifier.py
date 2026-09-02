"""
AUTO IMAGE CLASSIFIER — VLM-Powered Product Image Intelligence
================================================================
Uses Gemini Vision (FREE via LiteLLM Router) to automatically classify
every product image in a folder:

  - angle:        front | back | side | three_quarter | flat_lay | overhead
  - content_type: product | size_chart | detail_closeup | tag_label | lifestyle | packaging | color_swatch
  - garment_type: hoodie | tee | cargo_pants | sneakers | etc.
  - color:        specific color name (sage_green, charcoal_black, cream, etc.)

After classification:
  1. Model shots and lifestyle images are DELETED (model exclusion rule)
  2. ALL remaining images are KEPT and renamed to pipeline convention
  3. Multi-color products are grouped by detected color
  4. Front/back product shots → used for AI ad/lookbook generation
  5. Detail/tag/size chart → displayed in storefront "Photos" subcategory

Usage:
  # Classify and rename all images in a product folder
  from auto_image_classifier import classify_and_rename_images
  result = classify_and_rename_images(Path("MANUAL_CURATION/my_product"))

  # CLI: Test on a folder
  python auto_image_classifier.py path/to/product_folder

  # CLI: Built-in self-test with dummy images
  python auto_image_classifier.py --test
"""

import os
import json
import base64
import shutil
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger("image_classifier")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CLASSIFIER] %(message)s")

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# MIME type mapping
MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

# ── The VLM classification prompt ──────────────────────────────────
CLASSIFICATION_PROMPT = """You are a professional fashion product photography expert.
I'm showing you {image_count} product images from a single product listing.
Analyze EACH image and classify it.

Return ONLY a valid JSON object (no markdown, no explanation) with this structure:
{{
  "images": [
    {{
      "image_index": 0,
      "angle": "front",
      "content_type": "product",
      "garment_type": "hoodie",
      "color": "black",
      "weight_grams": null,
      "confidence": 0.95
    }}
  ],
  "product_summary": {{
    "primary_color": "black",
    "secondary_colors": ["white"],
    "garment_type": "hoodie",
    "garment_description": "Heavyweight oversized hoodie with kangaroo pocket",
    "piece_weights": [],
    "total_weight_grams": 500
  }}
}}

Classification rules for each image:

ANGLE (how the garment is positioned):
- "front": You can see the FRONT of the garment — chest area, front logo, front pockets, fly area for pants
- "back": You can see the BACK of the garment — back print, rear label area, back seams
- "side": Side profile view of the garment
- "three_quarter": Angled view showing front + side (common in lifestyle/model shots)
- "flat_lay": Garment laid flat on a surface, typically overhead shot
- "overhead": Bird's eye view, similar to flat_lay but may include surrounding props

CONTENT TYPE (what kind of photo this is):
- "product": A clean product photograph (the most common type — flat lay, ghost mannequin, or on hanger)
- "size_chart": ANY measurement table, size grid, dimension diagram, or sizing guide
- "weight_scale": ANY photo showing a scale / scale readout with weight in grams (g) or kilograms (kg). If present, extract the number in "weight_grams".
- "detail_closeup": Macro/close shot of fabric texture, stitching, buttons, zippers, hardware
- "tag_label": Brand tag, care label, neck tag, wash instruction closeup
- "lifestyle": Model wearing the garment in a styled scene (NOT a plain product shot)
- "model_shot": Model wearing garment on plain background (studio shot, not lifestyle)
- "packaging": Product packaging, shipping bag, box
- "color_swatch": Multiple color options shown as circles/squares or side-by-side garments

WEIGHT RULES (CRITICAL FOR MULTI-PIECE SETS):
- If an image shows a weight scale or measurement scale, set content_type to "weight_scale" and extract the weight in grams as "weight_grams" (e.g. 520 for 520g, or 1.2kg -> 1200).
- If a set has 2 or 3 weight scale images (e.g. top + pants + package), list all individual weights in "piece_weights" and SUM them together into "total_weight_grams".

GARMENT TYPE: Be specific — "hoodie", "crewneck_sweatshirt", "cargo_pants", "low_top_sneakers", etc.


COLOR: Be specific about the PRIMARY garment color — "sage_green" not just "green",
"charcoal_black" not just "black", "cream_white" not just "white".
If a size chart or non-product image, color should be null.

{color_hint}

CRITICAL RULES:
- Analyze ALL {image_count} images. Return exactly {image_count} entries in the "images" array.
- image_index MUST match the order I showed you the images (0-based).
- Size charts are VERY distinctive — they contain tables with numbers, measurements, cm/inch marks.
- If unsure between front/back, look for: logos/graphics (usually front), plain/tag area (usually back).
- For shoes: "front" = toe box visible, "back" = heel visible, "side" = lateral profile.
"""

# ── Single-image fallback prompt (if multi-image fails) ────────────
SINGLE_IMAGE_PROMPT = """You are a fashion photography expert. Analyze this single product image.

Return ONLY a valid JSON object (no markdown, no explanation):
{{
  "angle": "front | back | side | three_quarter | flat_lay | overhead",
  "content_type": "product | size_chart | detail_closeup | tag_label | lifestyle | model_shot | packaging | color_swatch",
  "garment_type": "specific garment type (hoodie, tee, cargo_pants, etc.) or null if not applicable",
  "color": "specific primary color or null if not applicable",
  "confidence": 0.0 to 1.0
}}

{color_hint}

RULES:
- "front" = front of garment visible (chest, front logo, front pockets)
- "back" = back of garment visible (back print, rear label, back seams)
- "size_chart" = any measurement table, size grid, or dimension diagram
- "detail_closeup" = macro shot of fabric, stitching, hardware
- Be specific about color: "sage_green" not "green"
"""


def safe_print(msg):
    """Windows cp1252-safe print."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode(), flush=True)


def _get_product_images(product_dir: Path) -> list:
    """Get all image files in a product directory, sorted by name."""
    images = []
    for f in sorted(product_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            # Skip any contact sheet images or classifier temp files
            if "contact_sheet" in f.name.lower() or f.name.startswith("__temp"):
                continue
            images.append(f)
    return images


def _encode_image(image_path: Path, max_size: int = 512) -> tuple:
    """Read, downscale to max_size, and base64-encode an image file. Returns (base64_str, mime_type).
    
    Downscaling high-res (10MB+) images to 512x512 JPEG reduces VLM payload size from 98MB to ~150KB,
    preventing 413 Payload Too Large errors and saving bandwidth.
    """
    try:
        from PIL import Image
        import io
        with Image.open(image_path) as raw_img:
            img = raw_img.convert("RGB")
        img.thumbnail((max_size, max_size))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        img.close()
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        return img_b64, "image/jpeg"
    except Exception:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode()
        ext = image_path.suffix.lower()
        mime = MIME_MAP.get(ext, "image/jpeg")
        return img_b64, mime



def _rgb_to_color_name(rgb: tuple) -> str:
    """Map an RGB tuple to the closest fashion color name."""
    r, g, b = rgb
    # Curated fashion color palette
    colors = {
        "black": (0, 0, 0), "charcoal": (54, 54, 54), "dark_grey": (80, 80, 80),
        "grey": (128, 128, 128), "light_grey": (192, 192, 192), "white": (255, 255, 255),
        "cream": (255, 253, 208), "beige": (245, 235, 210), "ivory": (255, 255, 240),
        "navy": (0, 0, 128), "royal_blue": (65, 105, 225), "sky_blue": (135, 206, 235),
        "baby_blue": (173, 216, 230), "teal": (0, 128, 128), "cyan": (0, 255, 255),
        "red": (255, 0, 0), "burgundy": (128, 0, 32), "wine": (114, 47, 55),
        "maroon": (128, 0, 0), "coral": (255, 127, 80), "salmon": (250, 128, 114),
        "pink": (255, 192, 203), "hot_pink": (255, 105, 180), "blush": (222, 162, 173),
        "orange": (255, 165, 0), "burnt_orange": (191, 87, 0), "rust": (183, 65, 14),
        "peach": (255, 218, 185), "tangerine": (255, 154, 0),
        "yellow": (255, 255, 0), "gold": (255, 215, 0), "mustard": (205, 185, 50),
        "green": (0, 128, 0), "forest_green": (34, 139, 34), "olive": (128, 128, 0),
        "sage_green": (188, 184, 138), "mint": (152, 255, 152), "khaki": (189, 183, 107),
        "lime": (0, 255, 0), "emerald": (80, 200, 120),
        "purple": (128, 0, 128), "lavender": (230, 230, 250), "plum": (142, 69, 133),
        "violet": (127, 0, 255), "mauve": (224, 176, 255),
        "brown": (139, 69, 19), "chocolate": (123, 63, 0), "tan": (210, 180, 140),
        "camel": (193, 154, 107), "mocha": (150, 105, 70),
    }
    min_dist = float("inf")
    closest = "unknown"
    for name, (cr, cg, cb) in colors.items():
        dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if dist < min_dist:
            min_dist = dist
            closest = name
    return closest


def _build_color_hint(weidian_data: dict = None, user_color: str = None) -> str:
    """Build a color hint string from Weidian data or user input."""
    hints = []
    if user_color:
        hints.append(f"The user specified the color as: \"{user_color}\"")
    if weidian_data:
        colors = weidian_data.get("colors", [])
        if colors:
            hints.append(f"The product listing shows these color options: {', '.join(colors)}")
        title = weidian_data.get("title", "") or weidian_data.get("product_name", "")
        if title:
            hints.append(f"Product listing title: \"{title}\"")
    if hints:
        return "COLOR HINTS (use these to validate your color detection):\n" + "\n".join(f"- {h}" for h in hints)
    return ""


def classify_images_vlm(
    image_paths: list,
    weidian_data: dict = None,
    user_color: str = None
) -> dict:
    """
    Send images to Gemini Vision for classification.
    Processes images in parallel chunks of 15 to maximize speed and prevent
    hitting rate limits or falling back to slow sequential per-image calls.
    
    Returns dict with 'images' list and 'product_summary'.
    """
    from litellm_router import shared_router

    color_hint = _build_color_hint(weidian_data, user_color)
    
    chunk_size = 20
    chunks = [image_paths[i:i + chunk_size] for i in range(0, len(image_paths), chunk_size)]
    log.info(f"Classifying {len(image_paths)} images in {len(chunks)} chunks (chunk size {chunk_size})...")
    
    def _process_chunk(chunk_tuple):
        chunk_idx, chunk = chunk_tuple
        log.info(f"Processing chunk {chunk_idx}/{len(chunks)} ({len(chunk)} images)...")
        try:
            res = _classify_batch(chunk, color_hint, shared_router)
            if not res or len(res.get("images", [])) != len(chunk):
                log.warning(f"Chunk {chunk_idx} returned wrong length. Falling back to per-image.")
                res = _classify_per_image(chunk, color_hint, shared_router)
            return chunk_idx, res
        except Exception as e:
            log.warning(f"Chunk {chunk_idx} batch call failed: {e}. Falling back to per-image.")
            return chunk_idx, _classify_per_image(chunk, color_hint, shared_router)

    all_chunk_results = {}
    with ThreadPoolExecutor(max_workers=min(len(chunks), 4)) as executor:
        for chunk_idx, res in executor.map(_process_chunk, [(idx+1, c) for idx, c in enumerate(chunks)]):
            all_chunk_results[chunk_idx] = res

    all_classified_images = []
    global_index = 0
    for idx in range(1, len(chunks) + 1):
        c_res = all_chunk_results.get(idx, {})
        for img in c_res.get("images", []):
            img["image_index"] = global_index
            all_classified_images.append(img)
            global_index += 1
            
    # Build a unified product summary across all chunks
    product_images = [r for r in all_classified_images if r.get("content_type") == "product"]
    non_product_images = [r for r in all_classified_images if r.get("content_type") != "product"]
    primary_color = None
    garment_type = None
    if product_images:
        # Use the highest confidence product image for primary data
        best = max(product_images, key=lambda x: x.get("confidence", 0))
        primary_color = best.get("color")
        garment_type = best.get("garment_type")

    # Mark the best image per angle as hero (for smart_select_images)
    angle_best = {}
    for img in product_images:
        angle = img.get("angle", "unknown")
        conf = img.get("confidence", 0)
        if angle not in angle_best or conf > angle_best[angle].get("confidence", 0):
            angle_best[angle] = img
    for img in all_classified_images:
        img["is_hero"] = (img in angle_best.values())

    # Detect which angles are available
    angles_present = set(img.get("angle") for img in product_images)

    return {
        "images": all_classified_images,
        "product_summary": {
            "primary_color": primary_color,
            "secondary_colors": list(set(
                r.get("color") for r in product_images
                if r.get("color") and r.get("color") != primary_color
            )),
            "garment_type": garment_type,
            "garment_description": None,
            "has_front": "front" in angles_present,
            "has_back": "back" in angles_present,
            "has_side": "side" in angles_present,
            "has_detail": any(r.get("content_type") == "detail_closeup" for r in all_classified_images),
            "has_size_chart": any(r.get("content_type") == "size_chart" for r in all_classified_images),
            "total_product_images": len(product_images),
            "total_non_product": len(non_product_images)
        }
    }


def _classify_batch(image_paths: list, color_hint: str, router) -> dict:
    """Send all images in a single VLM call."""
    content = []
    
    # Build the prompt
    prompt_text = CLASSIFICATION_PROMPT.format(
        image_count=len(image_paths),
        color_hint=color_hint
    )
    content.append({"type": "text", "text": prompt_text})
    
    # Add each image with a label
    for i, img_path in enumerate(image_paths):
        img_b64, mime = _encode_image(img_path)
        content.append({
            "type": "text",
            "text": f"\n--- Image {i} (filename: {img_path.name}) ---"
        })
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{img_b64}"}
        })

    messages = [{"role": "user", "content": content}]

    log.info(f"Sending {len(image_paths)} images to Gemini Vision (batch call)...")
    response = router.get_chat_completion_sync(
        messages=messages,
        primary_model="gemini-lite",
        temperature=1.0,
        max_tokens=4096,
        response_format={"type": "json_object"}
    )

    response_text = response.choices[0].message.content.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    result = json.loads(response_text)
    model_used = getattr(response, 'model', 'unknown')
    log.info(f"Batch classification complete via {model_used}")
    return result


from concurrent.futures import ThreadPoolExecutor

def _classify_single(args) -> dict:
    """Helper function to classify a single image (runs in thread with multi-provider fallback)."""
    i, img_path, color_hint, router = args
    img_b64, mime = _encode_image(img_path)
    prompt_text = SINGLE_IMAGE_PROMPT.format(color_hint=color_hint)

    # ── Attempt 1: LiteLLM Router ──
    try:
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}}
            ]
        }]

        log.info(f"Classifying image {i + 1}: {img_path.name}")
        response = router.get_chat_completion_sync(
            messages=messages,
            primary_model="gemini-flash",
            temperature=1.0,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )

        response_text = response.choices[0].message.content.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        result = json.loads(response_text)
        result["image_index"] = i
        return result

    except Exception as e:
        log.warning(f"LiteLLM classify failed for {img_path.name} ({e}), trying direct Google GenAI SDK...")

    # ── Attempt 2: Direct Google GenerativeAI SDK ──
    try:
        import google.generativeai as genai
        from PIL import Image
        import io
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_1")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            img = Image.open(image_path if isinstance(img_path, str) else str(img_path))
            res = model.generate_content([prompt_text, img])
            text = res.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            result = json.loads(text.strip())
            result["image_index"] = i
            return result
    except Exception as direct_err:
        log.error(f"Direct GenAI fallback also failed for {img_path.name}: {direct_err}")

    # Fallback only if all VLM providers failed
    return {
        "image_index": i,
        "angle": "front",
        "content_type": "product",
        "garment_type": "clothing",
        "color": None,
        "confidence": 0.5,
        "reasoning": "VLM inference unavailable"
    }


def _classify_per_image(image_paths: list, color_hint: str, router) -> dict:
    """Classify each image individually in parallel using ThreadPoolExecutor."""
    all_results = []
    
    # Pack arguments for executor map
    tasks = [(i, img_path, color_hint, router) for i, img_path in enumerate(image_paths)]
    
    log.info(f"Launching {len(image_paths)} parallel classification workers...")
    
    # Use 5 concurrent workers to avoid overloading RPM rate limits
    with ThreadPoolExecutor(max_workers=5) as executor:
        all_results = list(executor.map(_classify_single, tasks))
        
    # Sort results by image_index to preserve original order
    all_results.sort(key=lambda x: x["image_index"])

    # Build product summary from individual results
    product_images = [r for r in all_results if r.get("content_type") == "product"]
    non_product_images = [r for r in all_results if r.get("content_type") != "product"]
    primary_color = None
    garment_type = None
    if product_images:
        # Use the highest confidence product image for primary data
        best = max(product_images, key=lambda x: x.get("confidence", 0))
        primary_color = best.get("color")
        garment_type = best.get("garment_type")

    # Mark the best image per angle as hero (for smart_select_images)
    angle_best = {}
    for img in product_images:
        angle = img.get("angle", "unknown")
        conf = img.get("confidence", 0)
        if angle not in angle_best or conf > angle_best[angle].get("confidence", 0):
            angle_best[angle] = img
    for img in all_results:
        img["is_hero"] = (img in angle_best.values())

    # Detect which angles are available
    angles_present = set(img.get("angle") for img in product_images)

    return {
        "images": all_results,
        "product_summary": {
            "primary_color": primary_color,
            "secondary_colors": list(set(
                r.get("color") for r in product_images
                if r.get("color") and r.get("color") != primary_color
            )),
            "garment_type": garment_type,
            "garment_description": None,
            "has_front": "front" in angles_present,
            "has_back": "back" in angles_present,
            "has_side": "side" in angles_present,
            "has_detail": any(r.get("content_type") == "detail_closeup" for r in all_results),
            "has_size_chart": any(r.get("content_type") == "size_chart" for r in all_results),
            "total_product_images": len(product_images),
            "total_non_product": len(non_product_images)
        }
    }



def _determine_filename(classification: dict, angle_counts: dict, content_counts: dict) -> str:
    """
    Map a classification result to the pipeline's expected filename convention.
    
    Pipeline expects: front_angle, back_angle, side_angle, angle_N,
                      detail_close_N, size_chart_N
    """
    content_type = classification.get("content_type", "product")
    angle = classification.get("angle", "front")

    # Non-product images get special names
    if content_type == "size_chart":
        content_counts["size_chart"] = content_counts.get("size_chart", 0) + 1
        return f"size_chart_{content_counts['size_chart']}"

    if content_type == "weight_scale":
        content_counts["weight_scale"] = content_counts.get("weight_scale", 0) + 1
        return f"weight_scale_{content_counts['weight_scale']}"

    if content_type == "detail_closeup":
        content_counts["detail"] = content_counts.get("detail", 0) + 1
        return f"detail_close_{content_counts['detail']}"


    if content_type == "tag_label":
        content_counts["tag"] = content_counts.get("tag", 0) + 1
        return f"tag_label_{content_counts['tag']}"

    if content_type in ("packaging", "color_swatch"):
        content_counts["other"] = content_counts.get("other", 0) + 1
        return f"other_{content_counts['other']}"

    # Product images get angle-based names
    if angle == "front" and "front" not in angle_counts:
        angle_counts["front"] = True
        return "front_angle"
    elif angle == "back" and "back" not in angle_counts:
        angle_counts["back"] = True
        return "back_angle"
    elif angle == "side" and "side" not in angle_counts:
        angle_counts["side"] = True
        return "side_angle"
    else:
        # Additional angle shots get numbered names
        angle_counts["extra"] = angle_counts.get("extra", 0) + 1
        idx = angle_counts["extra"]
        # If it's a duplicate front/back, still label it descriptively
        if angle in ("front", "back", "side"):
            return f"{angle}_angle_{idx + 1}"
        elif angle in ("flat_lay", "overhead"):
            return f"flat_lay_{idx}"
        elif angle in ("three_quarter",):
            return f"angle_{idx + 3}"  # Start at 4 since 1-3 are front/back/side
        else:
            return f"angle_{idx + 3}"


def classify_and_rename_images(
    product_dir: Path,
    weidian_data: dict = None,
    user_color: str = None,
    dry_run: bool = False
) -> dict:
    """
    Main entry point. Classifies all images in a product folder and renames them
    to match the pipeline naming convention.
    
    Args:
        product_dir: Path to the product folder (e.g., MANUAL_CURATION/my_hoodie/)
        weidian_data: Optional dict with Weidian product page data (colors, title)
        user_color: Optional user-specified color string (from Discord)
        dry_run: If True, don't actually rename files, just return classification
    
    Returns:
        dict with classification results and rename mapping
    """
    product_dir = Path(product_dir)
    classification_file = product_dir / "image_classification.json"

    # Check for cached classification
    if classification_file.exists():
        cached = json.loads(classification_file.read_text(encoding="utf-8"))
        age_hours = 0
        try:
            classified_at = datetime.fromisoformat(cached.get("classified_at", ""))
            age_hours = (datetime.now() - classified_at).total_seconds() / 3600
        except Exception:
            pass
        if age_hours < 24:  # Cache valid for 24 hours
            log.info(f"Using cached classification ({age_hours:.1f}h old)")
            return cached

    # Get all images
    image_paths = _get_product_images(product_dir)
    if not image_paths:
        log.warning(f"No images found in {product_dir}")
        return {"images": [], "product_summary": {}, "renames": {}}

    log.info(f"Classifying {len(image_paths)} images in {product_dir.name}")

    # Run VLM classification
    vlm_result = classify_images_vlm(image_paths, weidian_data, user_color)

    # Map classifications to filenames
    angle_counts = {}
    content_counts = {}
    renames = {}
    enriched_images = []

    for i, img_path in enumerate(image_paths):
        # Find the matching classification
        if i < len(vlm_result.get("images", [])):
            classification = vlm_result["images"][i]
        else:
            classification = {
                "angle": "front", "content_type": "product",
                "garment_type": None, "color": None, "confidence": 0.0
            }

        # Determine new filename
        new_basename = _determine_filename(classification, angle_counts, content_counts)
        ext = img_path.suffix.lower()
        new_filename = f"{new_basename}{ext}"

        renames[img_path.name] = new_filename
        classification["original_filename"] = img_path.name
        classification["recommended_filename"] = new_filename
        enriched_images.append(classification)

    # Build product summary
    product_images = [c for c in enriched_images if c.get("content_type") == "product"]
    summary = vlm_result.get("product_summary", {})
    summary.update({
        "has_front": any(c.get("angle") == "front" for c in product_images),
        "has_back": any(c.get("angle") == "back" for c in product_images),
        "has_side": any(c.get("angle") == "side" for c in product_images),
        "has_detail": any(c.get("content_type") == "detail_closeup" for c in enriched_images),
        "has_size_chart": any(c.get("content_type") == "size_chart" for c in enriched_images),
        "total_product_images": len(product_images),
        "total_non_product": len(enriched_images) - len(product_images),
    })

    # ColorThief color extraction — secondary validation for VLM color detection
    try:
        from colorthief import ColorThief
        import io
        import gc
        # Use the first product image (front preferred) for color extraction
        front_images = [p for p in image_paths 
                       if any(c.get("angle") == "front" and c.get("original_filename") == p.name 
                             for c in enriched_images)]
        color_source = front_images[0] if front_images else (image_paths[0] if image_paths else None)
        if color_source and color_source.exists():
            with open(color_source, "rb") as f:
                img_io = io.BytesIO(f.read())
            ct = ColorThief(img_io)
            dominant_rgb = ct.get_color(quality=10)
            palette = ct.get_palette(color_count=4, quality=10)
            if hasattr(ct, "image") and ct.image:
                try:
                    ct.image.close()
                except Exception:
                    pass
            img_io.close()
            del ct
            gc.collect()
            color_name = _rgb_to_color_name(dominant_rgb)
            summary["colorthief_dominant"] = {
                "rgb": list(dominant_rgb),
                "name": color_name,
                "palette": [list(c) for c in palette]
            }
            log.info(f"ColorThief: dominant={color_name} RGB={dominant_rgb}")
    except ImportError:
        log.info("ColorThief not installed — skipping color validation (pip install colorthief)")
    except Exception as e:
        log.warning(f"ColorThief extraction failed: {e}")

    # If user specified a color, prefer it over VLM detection
    if user_color:
        summary["primary_color"] = user_color
        log.info(f"Using user-specified color: {user_color}")

    result = {
        "images": enriched_images,
        "product_summary": summary,
        "renames": renames,
        "classified_at": datetime.now().isoformat(),
        "classifier_version": "1.0"
    }

    # ── MODEL EXCLUSION: Delete ONLY model/lifestyle shots ──
    # Rule: Keep ALL product images EXCEPT ones showing a human model.
    # Front/back product shots → used for AI ad generation
    # Detail/tag/size chart → displayed in storefront "Photos" subcategory
    if not dry_run:
        model_excluded = []
        kept_images = []
        kept_renames = {}

        for img in enriched_images:
            orig_name = img["original_filename"]
            content_type = img.get("content_type", "product")

            if content_type in ("model_shot", "lifestyle"):
                # Delete images with human models — they contaminate AI generation
                file_path = product_dir / orig_name
                if file_path.exists():
                    try:
                        os.remove(file_path)
                        model_excluded.append(orig_name)
                        log.info(f"[MODEL EXCLUSION] Deleted model/lifestyle image: {orig_name}")
                    except Exception as e:
                        log.warning(f"[MODEL EXCLUSION] Failed to delete {orig_name}: {e}")
            else:
                # Keep everything else: product, detail_closeup, tag_label,
                # size_chart, packaging, color_swatch
                kept_images.append(img)
                kept_renames[orig_name] = renames[orig_name]

        enriched_images = kept_images
        renames = kept_renames

        # Update product_images list for summary counts
        product_images = [c for c in enriched_images if c.get("content_type") == "product"]
        summary.update({
            "has_front": any(c.get("angle") == "front" for c in product_images),
            "has_back": any(c.get("angle") == "back" for c in product_images),
            "has_side": any(c.get("angle") == "side" for c in product_images),
            "has_detail": any(c.get("content_type") == "detail_closeup" for c in enriched_images),
            "has_size_chart": any(c.get("content_type") == "size_chart" for c in enriched_images),
            "total_product_images": len(product_images),
            "total_non_product": len(enriched_images) - len(product_images),
            "model_shots_excluded": len(model_excluded),
        })

        result["images"] = enriched_images
        result["renames"] = renames
        result["model_excluded"] = model_excluded

        # ── COLOR GROUPING: Organize images into color subfolders ──
        # For multi-color products, group images by detected color so the
        # pipeline can generate separate AI ads per color variant and
        # display per-color photo galleries on the storefront.
        detected_colors = set()
        for img in enriched_images:
            color = img.get("color")
            if color and img.get("content_type") in ("product", "detail_closeup"):
                detected_colors.add(color)

        if len(detected_colors) > 1:
            log.info(f"[COLOR GROUPING] Multi-color product detected: {detected_colors}")
            color_groups = {}
            shared_images = []  # Images that apply to all colors (size_chart, packaging, etc.)

            for img in enriched_images:
                color = img.get("color")
                content_type = img.get("content_type", "product")

                # Size charts, packaging, color swatches are shared across all colors
                if content_type in ("size_chart", "packaging", "color_swatch"):
                    shared_images.append(img)
                elif color and color in detected_colors:
                    color_groups.setdefault(color, []).append(img)
                else:
                    # Uncolored items (tag_label with null color, etc.) go to shared
                    shared_images.append(img)

            result["color_groups"] = {
                color: [img["recommended_filename"] for img in imgs]
                for color, imgs in color_groups.items()
            }
            result["shared_images"] = [img["recommended_filename"] for img in shared_images]
            result["is_multicolor"] = True
            summary["detected_colors"] = sorted(detected_colors)
            log.info(f"[COLOR GROUPING] Groups: { {c: len(imgs) for c, imgs in color_groups.items()} }, Shared: {len(shared_images)}")
        else:
            result["is_multicolor"] = False
            if detected_colors:
                summary["detected_colors"] = sorted(detected_colors)

    # Perform renames (if not dry run)
    if not dry_run:
        _execute_renames(product_dir, renames)

    # Save classification JSON
    classification_file.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    log.info(f"Classification saved to {classification_file.name}")

    # Print summary
    safe_print(f"\n  [IMAGE CLASSIFIER] {product_dir.name}")
    safe_print(f"  Images: {len(enriched_images)} total ({len(product_images)} product, {len(enriched_images) - len(product_images)} non-product)")
    safe_print(f"  Garment: {summary.get('garment_type', '?')} | Color: {summary.get('primary_color', '?')}")
    safe_print(f"  Angles: front={'YES' if summary['has_front'] else 'NO'} | back={'YES' if summary['has_back'] else 'NO'} | side={'YES' if summary['has_side'] else 'NO'}")
    safe_print(f"  Extras: detail={'YES' if summary['has_detail'] else 'NO'} | size_chart={'YES' if summary['has_size_chart'] else 'NO'}")
    for old, new in renames.items():
        safe_print(f"    {old} -> {new}")

    return result


def _execute_renames(product_dir: Path, renames: dict):
    """
    Safely rename files in a product directory.
    Uses a two-step process to avoid name collisions:
    1. Rename all files to temporary names
    2. Rename from temporary to final names
    """
    if not renames:
        return

    import re
    def _safe_move(src: Path, dst: Path):
        import gc
        for attempt in range(5):
            try:
                shutil.move(str(src), str(dst))
                return True
            except PermissionError:
                gc.collect()
                time.sleep(0.3)
            except Exception as e:
                log.warning(f"Failed to move {src.name} -> {dst.name}: {e}")
                return False
        # Windows fallback: copy2 and remove
        try:
            shutil.copy2(str(src), str(dst))
            try:
                os.remove(str(src))
            except Exception:
                pass
            return True
        except Exception as e:
            log.error(f"Permanent move failure {src.name} -> {dst.name}: {e}")
            return False

    # Step 1: Move all to temp names to avoid collisions
    temp_renames = {}
    for old_name, new_name in renames.items():
        old_path = product_dir / old_name
        if not old_path.exists():
            log.warning(f"Source file not found for rename: {old_name}")
            continue
        # Strip any existing nested __temp_classify_* prefixes
        clean_name = re.sub(r"^(__temp_classify_[0-9]+_)+", "", old_name)
        temp_name = f"__temp_classify_{hash(clean_name) & 0xFFFFFFFF}_{clean_name}"
        temp_path = product_dir / temp_name
        if old_path != temp_path:
            _safe_move(old_path, temp_path)
        temp_renames[temp_name] = new_name

    # Step 2: Move from temp to final names
    for temp_name, final_name in temp_renames.items():
        temp_path = product_dir / temp_name
        final_path = product_dir / final_name
        if temp_path == final_path:
            continue
        # Handle collision: if final name already exists and is not our source file, add a suffix
        if final_path.exists() and final_path != temp_path:
            stem = final_path.stem
            ext = final_path.suffix
            counter = 2
            while final_path.exists() and final_path != temp_path:
                final_path = product_dir / f"{stem}_{counter}{ext}"
                counter += 1
        _safe_move(temp_path, final_path)

    log.info(f"Renamed {len(temp_renames)} files")


# ── CLI ─────────────────────────────────────────────────────────────
def _run_self_test():
    """Built-in self-test: creates dummy images and classifies them."""
    from PIL import Image
    import tempfile

    safe_print("\n" + "=" * 60)
    safe_print("  AUTO IMAGE CLASSIFIER — SELF TEST")
    safe_print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_product"
        test_dir.mkdir()

        # Create test images with different characteristics
        # Image 1: Red square (simulates a product front)
        img1 = Image.new('RGB', (800, 800), color='red')
        img1.save(test_dir / "image_1.png")

        # Image 2: Blue square (simulates a different angle)
        img2 = Image.new('RGB', (800, 800), color='blue')
        img2.save(test_dir / "image_2.png")

        # Image 3: White with grid (simulates size chart)
        img3 = Image.new('RGB', (600, 400), color='white')
        img3.save(test_dir / "image_3.png")

        # Create metadata
        meta = {
            "product_name": "Test Heavyweight Hoodie",
            "color": "black",
            "platform": "weidian"
        }
        (test_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")

        safe_print(f"\n  Created 3 test images in {test_dir}")
        safe_print("  Running VLM classification...\n")

        try:
            result = classify_and_rename_images(
                test_dir,
                user_color="black",
                dry_run=True  # Don't rename in test mode
            )

            # Validate result structure
            assert "images" in result, "Missing 'images' key"
            assert "product_summary" in result, "Missing 'product_summary' key"
            assert "renames" in result, "Missing 'renames' key"
            assert len(result["images"]) == 3, f"Expected 3 image results, got {len(result['images'])}"

            for img in result["images"]:
                assert "angle" in img, "Missing 'angle' in image result"
                assert "content_type" in img, "Missing 'content_type' in image result"
                assert "recommended_filename" in img, "Missing 'recommended_filename'"

            safe_print("\n  SELF TEST: PASSED")
            safe_print(f"  Classified {len(result['images'])} images successfully")
            safe_print(f"  Product summary: {json.dumps(result['product_summary'], indent=2)}")
            return True

        except Exception as e:
            safe_print(f"\n  SELF TEST: FAILED — {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = _run_self_test()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1:
        folder = Path(sys.argv[1])
        if not folder.is_dir():
            print(f"Error: {folder} is not a directory")
            sys.exit(1)
        result = classify_and_rename_images(folder)
        print(json.dumps(result, indent=2))
    else:
        print("Usage:")
        print("  python auto_image_classifier.py <product_folder>   # Classify a product folder")
        print("  python auto_image_classifier.py --test             # Run self-test")
