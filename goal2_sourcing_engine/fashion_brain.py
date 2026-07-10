"""
Fashion Brain — Style Understanding & Outfit Coordination
=========================================================
Gives the AI agent fashion intelligence:
- Outfit coordination rules (what goes with what)
- Color theory for fashion
- Trend awareness by season
- Product category expertise
- Size/proportion understanding

This is used by the agent to:
1. Pick matching outfits from different sources
2. Know which products pair together
3. Generate better prompts for FlowBridge
4. Understand what "looks good" for ad content
"""
from typing import Dict, List, Optional

# ==========================================
# STYLE PROFILES
# ==========================================
STYLE_PROFILES = {
    "streetwear": {
        "description": "Urban, oversized, bold graphics, hype culture",
        "staples": ["oversized hoodie", "cargo pants", "chunky sneakers", "beanie", "crossbody bag"],
        "colors": ["black", "grey", "earth tones", "muted pastels", "white"],
        "avoid": ["formal shoes", "slim fit blazers", "bright neon"],
        "brands_reference": ["sp5der", "essentials", "off-white", "bape", "stussy"],
        "fit": "oversized/relaxed",
    },
    "athleisure": {
        "description": "Athletic meets casual, gym-to-street, clean lines",
        "staples": ["joggers", "sports bra", "zip-up jacket", "running sneakers", "compression wear"],
        "colors": ["black", "white", "grey", "navy", "sage green"],
        "avoid": ["jeans", "dress shoes", "heavy jewelry"],
        "brands_reference": ["nike", "lululemon", "gymshark", "alo yoga"],
        "fit": "fitted/tapered",
    },
    "luxury_casual": {
        "description": "Expensive-looking daily wear, quality fabrics, understated logos",
        "staples": ["cashmere sweater", "tailored trousers", "clean sneakers", "minimal watch", "leather bag"],
        "colors": ["camel", "cream", "navy", "burgundy", "olive", "black"],
        "avoid": ["loud graphics", "distressed denim", "cartoon prints"],
        "brands_reference": ["loro piana", "stone island", "moncler", "ami paris"],
        "fit": "tailored/slim",
    },
    "minimalist": {
        "description": "Clean, monochrome, quality over quantity, capsule wardrobe",
        "staples": ["plain tee", "straight leg pants", "clean white sneakers", "simple necklace"],
        "colors": ["black", "white", "grey", "navy", "beige"],
        "avoid": ["loud patterns", "multiple logos", "chunky accessories"],
        "brands_reference": ["cos", "uniqlo", "arket", "muji"],
        "fit": "regular/relaxed",
    },
    "y2k": {
        "description": "Early 2000s revival, low rise, butterfly clips, chunky platforms",
        "staples": ["baby tee", "low-rise jeans", "platform shoes", "mini bag", "tinted sunglasses"],
        "colors": ["pink", "baby blue", "lavender", "silver", "white"],
        "avoid": ["earth tones", "oversized fits", "dark colors"],
        "brands_reference": ["juicy couture", "von dutch", "fendi baguette"],
        "fit": "fitted/cropped",
    },
    "dark_aesthetic": {
        "description": "All-black, gothic influence, silver hardware, moody",
        "staples": ["black leather jacket", "black boots", "silver chain", "black skinny jeans", "dark sunglasses"],
        "colors": ["black", "charcoal", "dark grey", "silver accents"],
        "avoid": ["bright colors", "pastels", "floral prints"],
        "brands_reference": ["chrome hearts", "rick owens", "balenciaga"],
        "fit": "slim/structured",
    },
}

# ==========================================
# OUTFIT COORDINATION RULES
# ==========================================
COORDINATION_RULES = {
    # What pairs with shoes
    "chunky_sneakers": {
        "tops": ["oversized hoodie", "graphic tee", "crop top", "varsity jacket"],
        "bottoms": ["cargo pants", "wide-leg jeans", "joggers", "mini skirt"],
        "accessories": ["crossbody bag", "cap", "chain necklace"],
        "styles": ["streetwear", "athleisure", "y2k"],
    },
    "clean_white_sneakers": {
        "tops": ["plain tee", "button-up shirt", "knit sweater", "blazer"],
        "bottoms": ["straight jeans", "chinos", "tailored trousers", "midi skirt"],
        "accessories": ["minimal watch", "tote bag", "small earrings"],
        "styles": ["minimalist", "luxury_casual"],
    },
    "boots": {
        "tops": ["leather jacket", "turtleneck", "oversized coat"],
        "bottoms": ["skinny jeans", "straight pants", "leather pants"],
        "accessories": ["silver rings", "chain", "belt", "scarf"],
        "styles": ["dark_aesthetic", "streetwear"],
    },
    "running_shoes": {
        "tops": ["tech jacket", "sports bra", "zip hoodie"],
        "bottoms": ["joggers", "biker shorts", "leggings"],
        "accessories": ["sports watch", "headband", "gym bag"],
        "styles": ["athleisure"],
    },

    # What pairs with tops
    "oversized_hoodie": {
        "bottoms": ["skinny jeans", "joggers", "biker shorts", "leggings"],
        "shoes": ["chunky sneakers", "jordans", "slides"],
        "accessories": ["cap", "crossbody bag"],
        "styles": ["streetwear", "athleisure"],
    },
    "blazer": {
        "bottoms": ["tailored trousers", "straight jeans", "midi skirt"],
        "shoes": ["clean sneakers", "loafers", "heeled boots"],
        "accessories": ["watch", "structured bag", "stud earrings"],
        "styles": ["luxury_casual", "minimalist"],
    },
    "crop_top": {
        "bottoms": ["high-waist jeans", "mini skirt", "cargo pants"],
        "shoes": ["platform sneakers", "chunky sandals", "boots"],
        "accessories": ["layered necklaces", "belly chain", "small bag"],
        "styles": ["y2k", "streetwear"],
    },
}

# ==========================================
# COLOR COORDINATION
# ==========================================
COLOR_PALETTES = {
    "monochrome_black": ["black", "charcoal", "dark grey", "white accent"],
    "earth_tones": ["brown", "tan", "olive", "cream", "rust"],
    "neutrals": ["black", "white", "grey", "beige", "navy"],
    "pastels": ["baby blue", "lavender", "mint", "baby pink", "cream"],
    "bold_contrast": ["black + white", "navy + white", "red + black"],
    "warm_autumn": ["burgundy", "camel", "forest green", "mustard"],
    "cool_summer": ["white", "light blue", "sage", "lavender"],
}

SEASON_COLORS = {
    "spring": ["pastels", "neutrals", "cool_summer"],
    "summer": ["cool_summer", "bold_contrast", "pastels"],
    "fall": ["earth_tones", "warm_autumn", "monochrome_black"],
    "winter": ["monochrome_black", "neutrals", "warm_autumn"],
}

# ==========================================
# PRODUCT CATEGORY KNOWLEDGE
# ==========================================
CATEGORY_KNOWLEDGE = {
    "sneakers": {
        "hot_styles_2026": [
            "chunky trail runners", "retro basketball", "slip-on mules",
            "platform sneakers", "techwear runners", "vintage tennis shoes"
        ],
        "price_sweet_spot": "$20-$60",
        "best_ad_formats": ["on_feet_lifestyle", "top_down_flex", "unboxing"],
        "audience": "18-30, sneaker culture, streetwear fans",
    },
    "clothing": {
        "hot_styles_2026": [
            "oversized bombers", "cargo everything", "mesh/sheer layers",
            "vintage wash", "matching sets", "gorpcore"
        ],
        "price_sweet_spot": "$15-$45",
        "best_ad_formats": ["mirror_selfie", "ootd_street", "grwm"],
        "audience": "18-35, fashion-forward, trend followers",
    },
    "beauty": {
        "hot_styles_2026": [
            "glass skin", "lip gloss revival", "clean girl aesthetic",
            "bold liner", "dewy finish", "skin tints"
        ],
        "price_sweet_spot": "$10-$30",
        "best_ad_formats": ["skincare_glow", "perfume_ad"],
        "audience": "16-35, beauty enthusiasts, skincare lovers",
    },
    "wigs": {
        "hot_styles_2026": [
            "body wave lace front", "bob cut", "water wave",
            "kinky curly", "straight HD lace", "colored wigs"
        ],
        "price_sweet_spot": "$25-$80",
        "best_ad_formats": ["mirror_selfie", "grwm", "lifestyle_action"],
        "audience": "18-45, black women, beauty enthusiasts",
    },
    "accessories": {
        "hot_styles_2026": [
            "Cuban link chains", "minimalist watches", "oversized sunglasses",
            "leather belts with logo", "crossbody bags", "layered rings"
        ],
        "price_sweet_spot": "$8-$35",
        "best_ad_formats": ["selfie_flex", "wrist_shot", "hand_shot"],
        "audience": "18-30, style-conscious, luxury aspirational",
    },
}


# ==========================================
# MAIN COORDINATION FUNCTION
# ==========================================
def coordinate_outfit(
    anchor_item: str,
    category: str,
    style: str = "streetwear",
    season: str = "spring",
) -> dict:
    """
    Given an anchor item, suggest a complete outfit.

    Args:
        anchor_item: The main piece (e.g. "chunky white sneakers")
        category: shoes, top, bottom, outerwear
        style: One of the STYLE_PROFILES keys
        season: spring, summer, fall, winter

    Returns:
        dict with suggested outfit components, colors, and styling tips
    """
    style_profile = STYLE_PROFILES.get(style, STYLE_PROFILES["streetwear"])
    season_palettes = SEASON_COLORS.get(season, SEASON_COLORS["spring"])

    # Find matching coordination rules
    best_match = None
    anchor_lower = anchor_item.lower()
    for key, rules in COORDINATION_RULES.items():
        if key.replace("_", " ") in anchor_lower or anchor_lower in key.replace("_", " "):
            best_match = rules
            break

    # Build outfit suggestion
    outfit = {
        "anchor_item": anchor_item,
        "style": style,
        "style_description": style_profile["description"],
        "fit_recommendation": style_profile["fit"],
        "season": season,
    }

    if best_match:
        if category == "shoes":
            outfit["suggested_tops"] = best_match.get("tops", style_profile["staples"][:2])
            outfit["suggested_bottoms"] = best_match.get("bottoms", style_profile["staples"][2:4])
            outfit["suggested_accessories"] = best_match.get("accessories", [])
        elif category == "top":
            outfit["suggested_bottoms"] = best_match.get("bottoms", [])
            outfit["suggested_shoes"] = best_match.get("shoes", [])
            outfit["suggested_accessories"] = best_match.get("accessories", [])
        elif category == "bottom":
            outfit["suggested_tops"] = best_match.get("tops", [])
            outfit["suggested_shoes"] = best_match.get("shoes", [])
    else:
        # Fallback to style profile staples
        outfit["suggested_pieces"] = style_profile["staples"]

    # Add color suggestions
    outfit["color_palettes"] = [
        {"name": p, "colors": COLOR_PALETTES.get(p, [])}
        for p in season_palettes
    ]
    outfit["colors_to_avoid"] = style_profile.get("avoid", [])

    # Add styling tips
    outfit["styling_tips"] = [
        f"For {style}, aim for a {style_profile['fit']} fit",
        f"Reference brands: {', '.join(style_profile.get('brands_reference', [])[:3])}",
        f"Season ({season}): stick to {', '.join(season_palettes[:2])} color palettes",
    ]

    return outfit


def get_category_knowledge(category: str) -> dict:
    """Get expertise about a product category."""
    return CATEGORY_KNOWLEDGE.get(category, CATEGORY_KNOWLEDGE.get("clothing", {}))


def suggest_ad_format(product_type: str) -> list:
    """Suggest the best ad formats for a product type."""
    knowledge = CATEGORY_KNOWLEDGE.get(product_type, {})
    return knowledge.get("best_ad_formats", ["mirror_selfie", "flat_lay"])


# ==========================================
# CLI TEST
# ==========================================
if __name__ == "__main__":
    import json

    print("=" * 60)
    print("  FASHION BRAIN — Test Output")
    print("=" * 60)

    # Test outfit coordination
    tests = [
        ("chunky white sneakers", "shoes", "streetwear", "spring"),
        ("black leather jacket", "top", "dark_aesthetic", "fall"),
        ("high-waist cargo pants", "bottom", "streetwear", "summer"),
        ("clean white sneakers", "shoes", "minimalist", "spring"),
    ]

    for item, cat, style, season in tests:
        print(f"\n📦 Anchor: {item} ({cat}, {style}, {season})")
        print("-" * 40)
        result = coordinate_outfit(item, cat, style, season)
        print(json.dumps(result, indent=2))
