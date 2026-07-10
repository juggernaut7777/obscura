"""
Luxury Caption Generator — TikTok-Safe Ad Copy
================================================
Generates viral captions for luxury/designer-inspired products
WITHOUT using brand names (TikTok safe).

Two caption modes:
  - TikTok Safe: No brand names, uses coded language ("the ones with the red bottom")
  - External (IG/Own Store): Can include brand references

Also generates A/B test hook variations and trending hashtag sets.
"""
import random
from typing import List, Dict, Tuple

# ==========================================
# BRAND-SAFE CODE WORDS (TikTok Safe)
# ==========================================
# Maps brand names to "coded" descriptions used on TikTok
BRAND_CODES = {
    "louis vuitton": "the LV pattern ones",
    "lv": "the monogram ones",
    "gucci": "the GG ones",
    "dior": "the ones with the oblique print",
    "nike": "swoosh ones",
    "jordan": "the J's",
    "yeezy": "the foam ones",
    "balenciaga": "the chunky ones",
    "prada": "the triangle logo ones",
    "hermes": "the H belt ones",
    "chanel": "the double C ones",
    "burberry": "the plaid pattern ones",
    "stone island": "the compass patch ones",
    "off-white": "the zip-tie ones",
    "bape": "the camo shark ones",
    "essentials": "the fear of ones",
    "sp5der": "the spider web ones",
    "chrome hearts": "the cross ones",
    "moncler": "the puffer with the patch",
    "canada goose": "the arctic puffer",
    "loro piana": "the cashmere ones",
    "maison margiela": "the split-toe ones",
}


def sanitize_for_tiktok(text: str) -> str:
    """Remove brand names from text, replace with coded language."""
    result = text
    for brand, code in BRAND_CODES.items():
        # Case-insensitive replacement
        import re
        result = re.sub(re.escape(brand), code, result, flags=re.IGNORECASE)
    return result


# ==========================================
# HOOK TEMPLATES (Quiet Power Editorial)
# ==========================================
HOOKS = {
    "shoes": [
        "Engineered for the after-hours.",
        "Quiet power.",
        "The foundation.",
        "Archive silhouette.",
        "Unspoken code.",
        "Built for the concrete.",
        "Form follows function.",
        "Not for everyone.",
    ],
    "clothing": [
        "Quiet power.",
        "Engineered confidence.",
        "Worn with presence.",
        "Uniform.",
        "Archive piece.",
        "Structured for the street.",
        "The new standard.",
        "No performance, just presence.",
    ],
    "accessories": [
        "The details.",
        "Hardware.",
        "Surgical steel.",
        "The final layer.",
        "Industrial precision.",
        "Quiet power.",
    ],
    "general": [
        "The Uniform.",
        "OBSCURA 001.",
        "Available now.",
        "Archive.",
        "Engineered.",
        "Quiet power.",
    ],
}

# ==========================================
# CAPTION TEMPLATES
# ==========================================
CAPTION_TEMPLATES = {
    "tiktok_safe": [
        "{hook}\n\n{product_name}.\n\n🔗 Link in bio.\n\n{hashtags}",
        "{hook}\n\n{description}\n\n🔗 Available now.\n\n{hashtags}",
        "{hook}\n\n🔗 OBSCURA.\n\n{hashtags}",
    ],
    "instagram": [
        "{hook}\n\n{product_name}.\n{description}\n\nAvailable now via link in bio.\n\n{hashtags}",
        "{hook}\n\nArchive.\n\n{hashtags}",
    ],
    "external_store": [
        "{product_name}.\n{hook}\n\n{description}\n\n🛒 {link}\n\n{hashtags}",
        "DROP 001.\n\n{product_name}.\n{hook}\n\n🛒 Available now: {link}",
    ],
}

# ==========================================
# HASHTAG SETS
# ==========================================
HASHTAG_SETS = {
    "shoes_tiktok": (
        "#streetwear #archivefashion #avantgarde #kicks "
        "#fashiontiktok #menswear #obscura #aesthetic"
    ),
    "clothing_tiktok": (
        "#streetwear #archivefashion #avantgarde #outfitinspo "
        "#fashiontiktok #menswear #obscura #aesthetic #highfashion"
    ),
    "accessories_tiktok": (
        "#streetwear #archivefashion #hardware #jewelry "
        "#menswear #obscura #aesthetic"
    ),
    "shoes_instagram": (
        "#streetwear #archivefashion #avantgardefashion #sneakerhead "
        "#menswear #highfashion #obscura #editorial"
    ),
    "clothing_instagram": (
        "#streetwear #archivefashion #avantgardefashion #menswear "
        "#highfashion #obscura #editorialphotography #outfitgrid"
    ),
}


# ==========================================
# MAIN GENERATOR
# ==========================================
class CaptionGenerator:
    """Generates viral captions for product ads."""

    def __init__(self):
        self.generated_count = 0

    def generate_caption(
        self,
        product_name: str,
        price: str = "",
        category: str = "general",
        platform: str = "tiktok",
        affiliate_link: str = "Link in bio",
        num_variants: int = 3,
    ) -> List[Dict]:
        """
        Generate multiple caption variants for A/B testing.

        Args:
            product_name: Name of the product
            price: Price string (e.g. "$22")
            category: Product category (shoes, clothing, accessories)
            platform: Target platform (tiktok, instagram, external_store)
            affiliate_link: The link or CTA
            num_variants: Number of variants to generate

        Returns:
            List of caption dicts with hook, body, hashtags
        """
        variants = []

        # Get hooks for this category
        hook_list = HOOKS.get(category, HOOKS["general"])

        # Get hashtags for platform
        if platform == "tiktok":
            hashtags = HASHTAG_SETS.get(f"{category}_tiktok",
                                        HASHTAG_SETS.get("clothing_tiktok"))
        else:
            hashtags = HASHTAG_SETS.get(f"{category}_instagram",
                                        HASHTAG_SETS.get("clothing_instagram"))

        # Get caption templates
        if platform == "tiktok":
            templates = CAPTION_TEMPLATES["tiktok_safe"]
        elif platform == "instagram":
            templates = CAPTION_TEMPLATES["instagram"]
        else:
            templates = CAPTION_TEMPLATES["external_store"]

        # Sanitize product name for TikTok
        safe_name = sanitize_for_tiktok(product_name) if platform == "tiktok" else product_name
        description = f"Quality: 🔥🔥🔥\nFit: True to size\nMaterial: Premium"

        for i in range(num_variants):
            hook = random.choice(hook_list)
            template = random.choice(templates)

            caption = template.format(
                hook=hook,
                product_name=safe_name,
                description=description,
                price=price or "Check link",
                link=affiliate_link,
                brand_hint=safe_name,
                hashtags=hashtags,
            )

            variants.append({
                "variant": i + 1,
                "hook": hook,
                "caption": caption,
                "platform": platform,
                "category": category,
                "is_brand_safe": platform == "tiktok",
            })

        self.generated_count += len(variants)
        return variants

    def generate_for_catalog(
        self,
        products: List[Dict],
        platform: str = "tiktok"
    ) -> List[Dict]:
        """
        Generate captions for an entire product catalog.
        Returns products with captions attached.
        """
        for product in products:
            name = product.get("productName", "product")
            price = product.get("price", "")
            category = product.get("category", "general")
            link = product.get("affiliateUrl", product.get("productUrl", ""))

            captions = self.generate_caption(
                product_name=name,
                price=f"${price}" if price else "",
                category=category,
                platform=platform,
                affiliate_link=link,
                num_variants=3,
            )

            product["captions"] = captions

        return products

    def get_ab_test_hooks(self, category: str = "general", count: int = 5) -> List[str]:
        """Get a set of hooks for A/B testing."""
        hook_list = HOOKS.get(category, HOOKS["general"])
        return random.sample(hook_list, min(count, len(hook_list)))


# ==========================================
# CLI
# ==========================================
if __name__ == "__main__":
    gen = CaptionGenerator()

    # Test: Generate captions for a product
    print("=" * 60)
    print("  CAPTION GENERATOR — Test Output")
    print("=" * 60)

    test_products = [
        {"productName": "Louis Vuitton Trainer Sneaker", "price": "89", "category": "shoes"},
        {"productName": "Sp5der Hoodie Pink", "price": "32", "category": "clothing"},
        {"productName": "Dior B30 Countdown", "price": "52", "category": "shoes"},
    ]

    for product in test_products:
        print(f"\n📦 Product: {product['productName']}")
        print("-" * 40)

        # TikTok (brand-safe)
        tiktok_captions = gen.generate_caption(
            product_name=product["productName"],
            price=f"${product['price']}",
            category=product["category"],
            platform="tiktok",
        )
        print(f"\n  🎵 TikTok Caption (Brand-Safe):")
        print(f"  {tiktok_captions[0]['caption'][:150]}...")

        # Instagram (can mention brands)
        ig_captions = gen.generate_caption(
            product_name=product["productName"],
            price=f"${product['price']}",
            category=product["category"],
            platform="instagram",
        )
        print(f"\n  📸 Instagram Caption:")
        print(f"  {ig_captions[0]['caption'][:150]}...")

    print(f"\n\n✅ Generated {gen.generated_count} total caption variants")
