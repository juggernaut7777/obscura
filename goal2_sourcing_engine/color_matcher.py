"""
OBSCURA Color Matcher
----------------------
Cross-references Yupoo VLM-detected color groups with Weidian variant options.
This provides a unified mapping to link high-resolution photos to ordering options.
"""

import re
from typing import Dict, List, Optional

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        print(text.encode("ascii", errors="replace").decode(), **kwargs)

# Synonyms for mapping VLM detected colors to a standard canonical color
COLOR_SYNONYMS = {
    # Blacks
    "charcoal": "black", "jet": "black", "onyx": "black", "ebony": "black",
    "ink": "black", "midnight": "black", "coal": "black", "black": "black",
    # Whites  
    "ivory": "white", "pearl": "white", "snow": "white", "off_white": "white",
    "off-white": "white", "white": "white", "cream": "cream",
    # Greys
    "gray": "grey", "silver": "grey", "ash": "grey", "slate": "grey",
    "heather_grey": "grey", "light_grey": "grey", "dark_grey": "grey", "grey": "grey",
    # Blues
    "navy": "blue", "cobalt": "blue", "royal_blue": "blue", "sky_blue": "blue",
    "light_blue": "blue", "dark_blue": "blue", "baby_blue": "blue", "teal": "blue", "blue": "blue",
    # Greens
    "olive": "green", "sage": "green", "sage_green": "green", "forest_green": "green",
    "army_green": "green", "moss": "green", "emerald": "green", "lime": "green",
    "hunter_green": "green", "dark_green": "green", "khaki_green": "green", "green": "green",
    # Reds
    "crimson": "red", "scarlet": "red", "maroon": "red", "burgundy": "red",
    "wine": "red", "cherry": "red", "rust": "red", "brick": "red", "red": "red",
    # Browns
    "tan": "brown", "khaki": "brown", "camel": "brown", "mocha": "brown",
    "coffee": "brown", "chocolate": "brown", "tobacco": "brown", "walnut": "brown",
    "caramel": "brown", "cognac": "brown", "espresso": "brown", "brown": "brown",
    # Pinks
    "rose": "pink", "blush": "pink", "salmon": "pink", "coral": "pink",
    "magenta": "pink", "fuchsia": "pink", "hot_pink": "pink", "pink": "pink",
    # Purples
    "violet": "purple", "plum": "purple", "lavender": "purple", "lilac": "purple",
    "mauve": "purple", "eggplant": "purple", "purple": "purple",
    # Yellows
    "gold": "yellow", "mustard": "yellow", "lemon": "yellow", "amber": "yellow",
    "honey": "yellow", "yellow": "yellow",
    # Oranges
    "tangerine": "orange", "peach": "orange", "apricot": "orange", "copper": "orange", "orange": "orange",
    # Beige family
    "beige": "beige", "sand": "beige", "nude": "beige", "oatmeal": "beige",
    "stone": "beige", "ecru": "beige", "linen": "beige",
}

# Translate common Chinese Weidian color characters to canonical English names
WEIDIAN_CHINESE_TO_CANONICAL = {
    "黑": "black", "白": "white", "灰": "grey", "蓝": "blue",
    "红": "red", "绿": "green", "粉": "pink", "棕": "brown",
    "咖": "brown", "紫": "purple", "黄": "yellow", "橙": "orange",
    "米": "cream", "卡其": "khaki", "驼": "camel", "藏青": "navy",
    "酒红": "burgundy", "墨绿": "dark_green", "浅蓝": "light_blue",
    "深蓝": "dark_blue", "浅灰": "light_grey", "深灰": "dark_grey",
    "杏": "apricot", "奶": "cream", "花灰": "heather_grey",
    "军绿": "army_green", "砖红": "brick_red", "烟灰": "ash",
}

# Swatch hex colors for the storefront website
COLOR_HEX_MAP = {
    "black": "#1A1A1A",
    "white": "#F9F9F9",
    "grey": "#808080",
    "blue": "#1E3A8A",
    "green": "#14532D",
    "red": "#7F1D1D",
    "pink": "#F472B6",
    "brown": "#78350F",
    "purple": "#581C87",
    "yellow": "#FBBF24",
    "orange": "#EA580C",
    "cream": "#FFFDD0",
    "khaki": "#C3B091",
    "camel": "#C19A6B",
    "navy": "#0B3C5D",
    "burgundy": "#800020",
    "dark_green": "#013220",
    "light_blue": "#ADD8E6",
    "dark_blue": "#00008B",
    "light_grey": "#D3D3D3",
    "dark_grey": "#A9A9A9",
    "apricot": "#FBCEB1",
    "heather_grey": "#9CA3AF",
    "army_green": "#4B5320",
    "brick_red": "#CB4154",
    "ash": "#5A5F62",
    "beige": "#F5F5DC",
}

def _normalize(color_name: str) -> str:
    """Normalize color name to canonical form."""
    c = color_name.lower().strip().replace("-", "_").replace(" ", "_")
    return COLOR_SYNONYMS.get(c, c)

def _normalize_weidian(english_name: str, chinese_name: str) -> str:
    """Normalize Weidian color option using English name first, falling back to Chinese heuristics."""
    canonical = _normalize(english_name)
    # If the normalized English name didn't resolve to a known synonym, try parsing Chinese chars
    raw_slug = english_name.lower().strip().replace("-", "_").replace(" ", "_")
    if canonical == raw_slug:
        for char, canon in WEIDIAN_CHINESE_TO_CANONICAL.items():
            if char in chinese_name:
                return canon
    return canonical

def get_color_hex(color_name: str) -> str:
    """Return hex color code for a color name."""
    canon = _normalize(color_name)
    return COLOR_HEX_MAP.get(canon, "#D1D5DB")  # Default to light gray

def match_colors(
    yupoo_color_groups: dict,
    weidian_variant_mappings: dict,
    shared_images: list = None
) -> dict:
    """Matches VLM-derived color groups with Weidian variant options.
    
    Args:
        yupoo_color_groups: {"black": ["yupoo_01.jpg", ...], "cream": [...]}
        weidian_variant_mappings: {"colors": {"Black": "黑色", "Cream": "杏色"}, "sizes": ...}
        shared_images: ["size_chart_1.png", ...]
        
    Returns:
        Dict with matched_colors, unmatched_yupoo_colors, unmatched_weidian_colors, shared_images, confidence
    """
    if shared_images is None:
        shared_images = []

    matched_colors = {}
    unmatched_yupoo_colors = list(yupoo_color_groups.keys())
    
    weidian_colors = weidian_variant_mappings.get("colors", {})
    unmatched_weidian_colors = list(weidian_colors.keys())

    # Build canonical maps
    yupoo_canonical = {col: _normalize(col) for col in yupoo_color_groups.keys()}
    weidian_canonical = {col_en: _normalize_weidian(col_en, col_zh) for col_en, col_zh in weidian_colors.items()}

    # Try exact or synonym matching
    for yupoo_orig, yupoo_canon in yupoo_canonical.items():
        found_en = None
        for weidian_orig, weidian_canon in weidian_canonical.items():
            if yupoo_canon == weidian_canon:
                found_en = weidian_orig
                break
        
        if found_en:
            # We found a match!
            yupoo_files = yupoo_color_groups[yupoo_orig]
            has_front = any(f.startswith("front_") or f.startswith("flat_lay_") for f in yupoo_files)
            has_back = any(f.startswith("back_") for f in yupoo_files)
            
            matched_colors[yupoo_orig] = {
                "yupoo_images": yupoo_files,
                "weidian_english": found_en,
                "weidian_chinese": weidian_colors[found_en],
                "has_front": has_front,
                "has_back": has_back
            }
            
            if yupoo_orig in unmatched_yupoo_colors:
                unmatched_yupoo_colors.remove(yupoo_orig)
            if found_en in unmatched_weidian_colors:
                unmatched_weidian_colors.remove(found_en)

    # Calculate match confidence
    total_needed = max(len(yupoo_color_groups), len(weidian_colors))
    if total_needed == 0:
        confidence = 1.0
    else:
        confidence = len(matched_colors) / total_needed

    return {
        "matched_colors": matched_colors,
        "unmatched_yupoo_colors": unmatched_yupoo_colors,
        "unmatched_weidian_colors": unmatched_weidian_colors,
        "shared_images": shared_images,
        "match_confidence": confidence
    }
