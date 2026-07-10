"""
CAROUSEL ASSEMBLER + CAPTION BRAIN
====================================
Takes generated images and assembles them into Instagram-ready carousels.
Generates captions with hooks, hashtags, and CTAs.

Usage:
  python carousel_builder_v2.py                    # Build carousels from output_ugc/
  python carousel_builder_v2.py --product hoodie   # Filter by product name
"""

import os
import sys
import json
import random
import textwrap
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output_ugc"
CAROUSEL_DIR = BASE_DIR / "carousel_ready"
CAROUSEL_DIR.mkdir(exist_ok=True)


# ─── CAPTION BRAIN ───

HOOKS = [
    "That feeling when your outfit just HITS different",
    "POV: You finally found THE piece",
    "Not me wearing this every day this week",
    "The outfit that made my coworker ask 'where did you get that?'",
    "Fit check -- rate this look 1-10",
    "This is your sign to upgrade your wardrobe",
    "When the fit is too good not to share",
    "Main character energy starts with the right outfit",
    "Casual but make it fashion",
    "The piece I didn't know I needed",
    "Adding this to my permanent rotation",
    "Obsessed is an understatement",
    "New drop just landed and I'm not okay",
    "Style tip: let the clothes do the talking",
    "This look got me 3 compliments in one hour",
]

BODY_LINES = [
    "Premium quality you can feel. Styled for the modern you.",
    "Effortless style meets everyday comfort.",
    "The kind of piece that works for brunch, meetings, and everything in between.",
    "Designed for people who care about the details.",
    "From street to studio -- this look transitions seamlessly.",
    "Comfort first, compliments second. Both guaranteed.",
    "Your wardrobe's new MVP. Trust us on this one.",
    "Not fast fashion -- this is intentional style.",
    "Made to move with you, made to make a statement.",
    "The fit, the fabric, the feel -- all elevated.",
]

CTAS = [
    "Shop the look -- link in bio",
    "Comment 'LINK' and we'll DM you the shop page",
    "Tap to shop. Limited stock available.",
    "Save this for your next outfit inspo",
    "Link in bio -- don't sleep on this one",
    "DM us 'STYLE' for exclusive pricing",
    "Available now. Link in bio before it's gone.",
    "Share this with someone who needs this look",
]

HASHTAG_SETS = [
    "#OOTD #FashionFinds #StyleInspo #NewDrop #WardrobeEssentials",
    "#FitCheck #StreetStyle #FashionTok #DailyFit #LookOfTheDay",
    "#StyleGuide #OutfitIdeas #FashionDaily #TrendAlert #GetDressed",
    "#MinimalStyle #EverydayFashion #CleanAesthetic #ModernWardrobe",
    "#FashionContent #ContentCreator #UGCFashion #BrandStyle #ShopNow",
]


def generate_caption(product_name, price=None):
    """Generates a complete Instagram caption with hook + body + CTA + hashtags."""
    hook = random.choice(HOOKS)
    body = random.choice(BODY_LINES)
    cta = random.choice(CTAS)
    hashtags = random.choice(HASHTAG_SETS)

    # Clean up product name for display
    display_name = product_name.replace("_", " ").replace("-", " ").title()

    caption_parts = [hook]
    caption_parts.append("")
    caption_parts.append("{} -- {}".format(display_name, body))

    if price:
        caption_parts.append("")
        caption_parts.append("Starting at {}".format(price))

    caption_parts.append("")
    caption_parts.append(cta)
    caption_parts.append("")
    caption_parts.append(hashtags)

    return "\n".join(caption_parts)


# ─── CAROUSEL ASSEMBLY ───

def group_images_by_product():
    """Groups all generated images by product name."""
    grouped = defaultdict(list)

    if not OUTPUT_DIR.exists():
        print("[!] No output directory found.")
        return grouped

    for img_path in sorted(OUTPUT_DIR.glob("*.png")):
        name = img_path.stem
        # Format: modelId_productName_timestamp_index
        parts = name.split("_")
        if len(parts) >= 3:
            model_id = parts[0]
            # Product name is everything between model_id and timestamp
            # Find the timestamp part (8 digits)
            product_parts = []
            for i, part in enumerate(parts[1:], 1):
                if len(part) == 8 and part.isdigit():
                    break
                product_parts.append(part)
            product_name = "_".join(product_parts) if product_parts else "unknown"
            grouped[product_name].append({
                "path": str(img_path),
                "model": model_id,
                "product": product_name,
                "filename": img_path.name,
            })

    return grouped


def build_carousel(product_name, images, price=None):
    """Builds a carousel package: ordered images + caption + metadata."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    carousel_name = "carousel_{}_{}".format(product_name, timestamp)
    carousel_path = CAROUSEL_DIR / carousel_name
    carousel_path.mkdir(exist_ok=True)

    # The ideal carousel order:
    # 1. Hero close-up (slide 1 -- the hook)
    # 2-4. Lifestyle / different models
    # 5-6. Detail shots
    # 7-8. Product-only flat lay
    # 9. Pricing card (we'll generate a text overlay)
    # 10. CTA card

    # For now, order by variety (different models first)
    seen_models = set()
    ordered = []
    remaining = []

    for img in images:
        if img["model"] not in seen_models:
            ordered.append(img)
            seen_models.add(img["model"])
        else:
            remaining.append(img)

    ordered.extend(remaining)

    # Limit to 8 images (leave room for pricing + CTA cards)
    ordered = ordered[:8]

    # Copy images with slide numbers
    slide_manifest = []
    for i, img in enumerate(ordered, 1):
        slide_name = "slide_{:02d}_{}.png".format(i, img["model"])
        dest = carousel_path / slide_name

        # Copy the image
        import shutil
        shutil.copy2(img["path"], str(dest))

        slide_manifest.append({
            "slide": i,
            "filename": slide_name,
            "model": img["model"],
            "source": img["filename"],
        })

    # Generate caption
    caption = generate_caption(product_name, price)

    # Save caption
    caption_path = carousel_path / "caption.txt"
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(caption)

    # Save manifest
    manifest = {
        "carousel_name": carousel_name,
        "product": product_name,
        "created": timestamp,
        "total_slides": len(slide_manifest),
        "slides": slide_manifest,
        "caption": caption,
        "format": "1080x1350 (4:5 portrait)",
        "notes": "Add trending audio for Reels discovery. Use native product tags.",
    }

    manifest_path = carousel_path / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return carousel_path, manifest


def main():
    print("=" * 50)
    print("CAROUSEL ASSEMBLER + CAPTION BRAIN")
    print("=" * 50)

    # Filter by product if specified
    product_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == "--product" and i + 1 < len(sys.argv):
            product_filter = sys.argv[i + 1]

    grouped = group_images_by_product()

    if not grouped:
        print("[!] No generated images found in output_ugc/")
        print("    Run local_generation_worker.py first to generate content.")
        return

    print("[+] Found {} products with generated images:".format(len(grouped)))
    for product, images in grouped.items():
        print("    {} -- {} images".format(product, len(images)))

    for product, images in grouped.items():
        if product_filter and product_filter.lower() not in product.lower():
            continue

        if len(images) < 1:
            print("[!] Skipping {} -- not enough images".format(product))
            continue

        print("\n[*] Building carousel for: {}".format(product))
        carousel_path, manifest = build_carousel(product, images)

        print("[+] Carousel saved to: {}".format(carousel_path))
        print("[+] Slides: {}".format(manifest["total_slides"]))
        print("\n--- GENERATED CAPTION ---")
        print(manifest["caption"])
        print("--- END CAPTION ---\n")


if __name__ == "__main__":
    main()
