import json
from outfit_assembler import OutfitAssembler

# 1. Define our dummy product catalog (simulating scraped products from AliExpress/TikTok Shop)
catalog = [
    {
        "productId": "top_001",
        "name": "Black Oversized Streetwear Hoodie",
        "category": "top",
        "color": "black",
        "style": "streetwear",
        "price": 35.99,
        "image_path": "test_products/black_hoodie.jpg"
    },
    {
        "productId": "bot_001",
        "name": "Black Tactical Cargo Pants",
        "category": "bottom",
        "color": "black",
        "style": "streetwear",
        "price": 42.50,
        "image_path": "test_products/cargo_pants.jpg"
    },
    {
        "productId": "shoe_001",
        "name": "White Classic Leather Sneakers",
        "category": "shoes",
        "color": "white",
        "style": "casual",
        "price": 29.99,
        "image_path": "test_products/sneakers.jpg"
    }
]

print("👗 INITIALIZING OUTFIT ASSEMBLER...")
assembler = OutfitAssembler(product_catalog=catalog)

# 2. Pick a "Hero Product" (the main thing we want to sell)
hero_product = catalog[0] # The Black Hoodie

print(f"\n🎯 HERO PRODUCT SELECTED: {hero_product['name']} (£{hero_product['price']})")
print(f"   Category detected: {assembler.detect_item_category(hero_product['name'])}")
print(f"   Style detected: {assembler.detect_style(hero_product['name'])}")
print(f"   Color detected: {assembler.detect_color(hero_product['name'])}")

# 3. Ask the Assembler to build a full outfit around the hero product
print("\n🔄 ASSEMBLING OUTFIT...")
outfit = assembler.build_outfit(hero_product)

print(f"\n✅ OUTFIT TYPE: {outfit['type']}")
print(f"   Status Note: {outfit['caption_note']}")
print(f"   Total Value: £{outfit['total_price']}")

print("\n📦 ITEMS IN OUTFIT:")
for item in outfit['items']:
    print(f"   - {item['name']} (£{item['price']})")

# 4. Generate the social media caption
print("\n📝 AUTO-GENERATED TIKTOK/INSTAGRAM CAPTION:")
print("-" * 40)
print(assembler.generate_caption(outfit))
print("-" * 40)
