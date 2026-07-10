"""
Outfit Assembler — Auto-Match & Fallback System
================================================
Intelligently pairs products into complete outfits or falls back to
single-item hero shots when no match is found.

Usage:
  from outfit_assembler import OutfitAssembler
  assembler = OutfitAssembler()
  outfit = assembler.build_outfit(top_product)
"""
import os
import json
import random
from datetime import datetime

# ===================================================================
# STYLIST BRAIN: Advanced Fashion Intelligence & Seasonal Awareness
# ===================================================================

# Determine current season dynamically
def get_current_season():
    month = datetime.now().month
    if month in [3, 4, 5]: return "spring"
    if month in [6, 7, 8]: return "summer"
    if month in [9, 10, 11]: return "fall"
    return "winter"

SEASONAL_RULES = {
    "spring": {"allowed": ["t-shirt", "light jacket", "sneakers", "jeans", "cardigan", "blouse", "midi skirt", "pastel"], 
               "banned": ["heavy parka", "snow boots", "thick wool"]},
    "summer": {"allowed": ["t-shirt", "shorts", "sundress", "sandals", "linen", "crop top", "swim", "sunglasses"], 
               "banned": ["puffer jacket", "heavy coat", "fleece", "beanie"]},
    "fall":   {"allowed": ["hoodie", "jeans", "jacket", "boots", "sweater", "trench", "flannel", "earth tones"], 
               "banned": ["swimwear", "flip flops", "tank top"]},
    "winter": {"allowed": ["puffer", "heavy coat", "hoodie", "boots", "beanie", "scarf", "fleece", "thermals"], 
               "banned": ["shorts", "sundress", "sandals", "crop top"]}
}

# Color harmony rules
NEUTRAL_COLORS = ["black", "white", "grey", "gray", "navy", "beige", "cream", "khaki", "tan"]

COLOR_COMPLEMENTS = {
    "red": ["black", "white", "navy", "grey", "beige"],
    "blue": ["white", "tan", "beige", "grey", "black"],
    "green": ["black", "white", "beige", "brown", "cream"],
    "pink": ["black", "white", "grey", "navy", "beige"],
    "yellow": ["black", "navy", "white", "grey", "denim"],
    "orange": ["black", "navy", "white", "brown", "olive"],
    "purple": ["black", "white", "grey", "silver", "beige"],
    "brown": ["white", "cream", "beige", "black", "tan"],
    "denim": ["white", "black", "beige", "brown", "cream"],
}

# Style compatibility rules — Micro-aesthetics & Occasions
STYLE_GROUPS = {
    # Core aesthetics
    "streetwear": ["hoodie", "cargo pants", "sneakers", "oversized tee", "bomber jacket", "bucket hat", "graphic tee", "dunks"],
    "old_money": ["polo", "chinos", "loafers", "blazer", "tennis sweater", "linen shirt", "trousers", "oxford"],
    "gorpcore": ["windbreaker", "hiking boots", "cargo pants", "fleece", "technical jacket", "salomon", "arcteryx", "vest"],
    "opium": ["leather jacket", "black boots", "distressed denim", "silver chain", "black hoodie", "avant-garde", "combat boots"],
    "y2k": ["baby tee", "low rise jeans", "chunky sneakers", "rhinestone", "trucker hat", "velour tracksuit"],
    
    # Occasions
    "gym_athletic": ["sports bra", "leggings", "joggers", "running shoes", "gym shorts", "performance tee", "windbreaker"],
    "date_night": ["dress", "heels", "blouse", "blazer", "slacks", "oxford shoes", "clutch", "jewelry"],
    "airport_comfy": ["sweatpants", "oversized hoodie", "slip-on", "tote bag", "cap"],
}

# What category each item type belongs to
ITEM_CATEGORIES = {
    "top": ["t-shirt", "tee", "blouse", "shirt", "hoodie", "sweater", "cardigan", "tank top", "crop top", "polo", "jacket", "blazer", "bomber", "vest", "sweatshirt", "sports bra", "top"],
    "bottom": ["jeans", "trousers", "pants", "shorts", "skirt", "leggings", "joggers", "cargo pants", "chinos", "track pants", "pencil skirt", "slacks"],
    "shoes": ["sneakers", "heels", "boots", "trainers", "sandals", "loafers", "shoes", "jordans", "dunks", "canvas", "espadrilles", "oxford"],
    "dress": ["dress", "gown", "sundress", "jumpsuit", "romper"],
    "accessory": ["bag", "hat", "watch", "sunglasses", "chain", "necklace", "earrings", "bracelet", "belt", "clutch", "scarf"],
}


class OutfitAssembler:
    """Builds complete outfits from individual product items."""
    
    def __init__(self, product_catalog: list = None):
        """
        Args:
            product_catalog: List of product dicts with keys like:
                {"name": "Black Cargo Pants", "category": "bottom", "color": "black", 
                 "style": "streetwear", "image_path": "products/cargo.png", "price": 25}
        """
        self.catalog = product_catalog or []
    
    def detect_item_category(self, product_name: str) -> str:
        """Determine if a product is a top, bottom, shoes, dress, or accessory."""
        name_lower = product_name.lower()
        for category, keywords in ITEM_CATEGORIES.items():
            if any(kw in name_lower for kw in keywords):
                return category
        return "top"  # Default assumption
    
    def detect_style(self, product_name: str) -> str:
        """Determine the style vibe of a product."""
        name_lower = product_name.lower()
        for style, keywords in STYLE_GROUPS.items():
            if any(kw in name_lower for kw in keywords):
                return style
        return "casual"
    
    def detect_color(self, product_name: str) -> str:
        """Extract the primary color from the product name."""
        name_lower = product_name.lower()
        all_colors = list(COLOR_COMPLEMENTS.keys()) + NEUTRAL_COLORS
        for color in all_colors:
            if color in name_lower:
                return color
        return "black"  # Safe default
    
    def colors_match(self, color_a: str, color_b: str) -> bool:
        """Check if two colors go well together."""
        if color_a in NEUTRAL_COLORS or color_b in NEUTRAL_COLORS:
            return True  # Neutrals go with everything
        complements = COLOR_COMPLEMENTS.get(color_a, [])
        return color_b in complements or color_a == color_b
    
    def build_outfit(self, hero_product: dict) -> dict:
        """
        Given a hero product, try to build a complete outfit from the catalog.
        
        Returns:
        {
            "type": "full_outfit" | "single_hero",
            "hero": {...},
            "items": [{...}, {...}, ...],  # All items in the outfit
            "caption_note": "Complete outfit" | "Top only available",
            "total_price": float,
        }
        """
        hero_name = hero_product.get("name", "")
        hero_category = self.detect_item_category(hero_name)
        hero_style = self.detect_style(hero_name)
        hero_color = self.detect_color(hero_name)
        hero_price = hero_product.get("price", 0)
        
        outfit_items = [hero_product]
        needed_categories = []
        
        # Determine what's needed for a complete outfit
        if hero_category == "dress":
            needed_categories = ["shoes", "accessory"]
        elif hero_category == "top":
            needed_categories = ["bottom", "shoes"]
        elif hero_category == "bottom":
            needed_categories = ["top", "shoes"]
        elif hero_category == "shoes":
            needed_categories = ["top", "bottom"]
        elif hero_category == "accessory":
            needed_categories = ["top", "bottom", "shoes"]
        
        # Try to find matching items from catalog
        total_price = hero_price
        matched_all = True
        
        for needed in needed_categories:
            match = self._find_best_match(needed, hero_style, hero_color, outfit_items)
            if match:
                outfit_items.append(match)
                total_price += match.get("price", 0)
            else:
                matched_all = False
        
        if matched_all and len(outfit_items) >= 2:
            return {
                "type": "full_outfit",
                "hero": hero_product,
                "items": outfit_items,
                "caption_note": "Complete outfit — all items available",
                "total_price": total_price,
            }
        else:
            return {
                "type": "single_hero",
                "hero": hero_product,
                "items": [hero_product],
                "caption_note": f"{hero_category.title()} only — styled for inspiration",
                "total_price": hero_price,
            }
    
    def _find_best_match(self, category: str, target_style: str, 
                         target_color: str, exclude: list) -> dict:
        """Find the best matching item from catalog for a given category."""
        exclude_names = [p.get("name", "") for p in exclude]
        candidates = []
        
        current_season = get_current_season()
        season_rules = SEASONAL_RULES.get(current_season, {})
        allowed_items = season_rules.get("allowed", [])
        banned_items = season_rules.get("banned", [])

        for product in self.catalog:
            name = product.get("name", "").lower()
            if name in exclude_names:
                continue
            
            # 1. Seasonality Check (HARD FILTER)
            # A stylist wouldn't pair a winter parka with summer shorts.
            is_banned = any(b in name for b in banned_items)
            if is_banned:
                continue
            
            p_category = self.detect_item_category(name)
            if p_category != category:
                continue
            
            p_style = self.detect_style(name)
            p_color = self.detect_color(name)
            
            # 2. Score the match (Stylist Logic)
            score = 0
            
            # Heavy weight for aesthetic match
            if p_style == target_style:
                score += 5
            
            # Seasonal relevance bonus
            if any(a in name for a in allowed_items):
                score += 2
                
            # Color harmony
            if self.colors_match(target_color, p_color):
                score += 3
            if p_color in NEUTRAL_COLORS:
                score += 1
            
            # Monochromatic bonus (high fashion)
            if p_color == target_color and p_color not in NEUTRAL_COLORS:
                score += 2
            
            if score > 3:  # Require a minimum threshold for a "good" match
                candidates.append((score, product))
        
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        
        return None
    
    def generate_caption(self, outfit: dict) -> str:
        """Generate a social media caption for the outfit."""
        items = outfit["items"]
        
        if outfit["type"] == "full_outfit":
            item_lines = []
            for item in items:
                name = item.get("name", "Item")
                price = item.get("price", 0)
                if price > 0:
                    item_lines.append(f"• {name} — £{price}")
                else:
                    item_lines.append(f"• {name}")
            
            total = outfit.get("total_price", 0)
            caption = f"GET THE LOOK 🔥\n\n"
            caption += "\n".join(item_lines)
            if total > 0:
                caption += f"\n\nFull outfit: £{total}"
            caption += "\n\nLink in bio 🛒"
            return caption
        else:
            hero = outfit["hero"]
            name = hero.get("name", "Item")
            price = hero.get("price", 0)
            note = outfit.get("caption_note", "")
            caption = f"🔥 {name}"
            if price > 0:
                caption += f" — £{price}"
            caption += f"\n\n{note}"
            caption += "\n\nLink in bio 🛒"
            return caption
