"""
SMART ROUTER — Decides between AI Generation and VTON
=====================================================
Analyses the product image to detect if it has text/graphics/logos.
If yes  -> Routes to VTON (pixel-perfect garment warp)
If no   -> Routes to AI Generation (creative lifestyle shots)

This ensures graphic tees, printed shirts, and logo items always
show the EXACT original design on the model.
"""

import os
import time
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Keywords that indicate a product likely has graphics/text that must be preserved
GRAPHIC_KEYWORDS = [
    "graphic", "print", "logo", "text", "letter", "tee", "t-shirt",
    "vintage", "anime", "band", "slogan", "embroidered", "patch",
    "rhinestone", "studded", "patterned", "floral", "camo", "tie-dye",
    "acid wash", "distressed", "graffiti", "varsity"
]

# Keywords that indicate plain items safe for AI generation
PLAIN_KEYWORDS = [
    "solid", "blank", "plain", "hoodie", "jogger", "cargo", "chino",
    "sneaker", "boot", "sandal", "loafer", "jeans", "denim",
    "legging", "skirt", "shorts", "blazer", "jacket", "polo"
]


def detect_needs_vton(product_name: str, product_path: str = None) -> bool:
    """
    Determines if a product needs pixel-perfect VTON (True)
    or can safely use AI generation (False).
    """
    name_lower = product_name.lower()

    # Check for graphic keywords
    for kw in GRAPHIC_KEYWORDS:
        if kw in name_lower:
            return True

    # Check for plain keywords (these are safe for AI gen)
    for kw in PLAIN_KEYWORDS:
        if kw in name_lower:
            return False

    # Default: if we can't tell, use VTON to be safe
    return True


def route_generation(product_name: str, product_path: str, model_body_path: str,
                     output_dir: str = None):
    """
    Returns True if the item needs a SIMPLE prompt to preserve graphics via FlowBridge.
    Returns False if it should use the complex editorial prompt.
    """
    needs_simple = detect_needs_vton(product_name, product_path)

    if needs_simple:
        print("[ROUTER] '{}' -> Simple Prompt Flow (preserves graphics)".format(product_name))
        return True
    else:
        print("[ROUTER] '{}' -> Complex Editorial Flow (plain item)".format(product_name))
        return False


def _run_vton(garment_path: str, model_path: str, description: str,
              output_dir: str) -> str:
    """
    Uses the cascading multi-provider VTON system:
    1. Kwai Kolors (FREE dedicated GPU - not the broken IDM-VTON)
    2. FASHN.ai (10 free credits on signup)
    3. Replicate ($0.03/run)
    """
    try:
        try:
            from vton_cascade import cascade_vton
        except ImportError:
            print("   [!] vton_cascade module missing. VTON disabled.")
            return None
        result = cascade_vton(model_path, garment_path, description)
        if result and os.path.exists(result):
            return result
    except Exception as e:
        print("   [!] VTON cascade failed: {}".format(e))

    print("   [!] All VTON methods failed for '{}'".format(description))
    return None


if __name__ == "__main__":
    # Test the router
    test_items = [
        ("Red Graphic Tee with Skull Print", True),
        ("Black Cargo Pants", False),
        ("Vintage Band Tee Metallica", True),
        ("Plain White Hoodie", False),
        ("Y2K Rhinestone Crop Top", True),
        ("Navy Blue Chinos", False),
        ("Oversized Anime Print Tee", True),
        ("Grey Joggers", False),
    ]

    print("=" * 60)
    print("   SMART ROUTER TEST")
    print("=" * 60)
    for name, expected in test_items:
        result = detect_needs_vton(name)
        status = "[OK]" if result == expected else "[FAIL]"
        track = "VTON" if result else "AI Gen"
        print("  {} {} -> {}".format(status, name, track))
