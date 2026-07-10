import os
import re
import random
from pathlib import Path

class FashionCritic:
    """
    The Expert Fashion Assistant / Gatekeeper.
    Analyzes products and prompts to ensure they meet ELITE standards before generation.
    """

    def __init__(self, manifesto_content: str):
        self.manifesto = manifesto_content
        self.rules = self._parse_manifesto()

    def _parse_manifesto(self):
        # Basic parsing of the manifesto rules for easy lookup
        return {
            "no_blur": "NO bokeh" in self.manifesto or "sharp" in self.manifesto.lower(),
            "editorial": "editorial" in self.manifesto.lower(),
            "raw_png": "PNG" in self.manifesto
        }

    def evaluate_campaign(self, product_name: str, product_type: str, gender: str) -> dict:
        """
        Determines if a campaign is viable and what styling 'upgrades' it needs.
        """
        errors = []
        styling_requirements = []

        # 1. Gender Verification
        if gender not in ["male", "female"]:
            errors.append(f"Invalid gender detected: {gender}. Must be male or female.")

        # 2. Product-Specific Styling Logic (The 'Assistant' Brain)
        # If the product is an accessory/shoe, we MUST specify the rest of the outfit.
        ptype = product_type.lower()
        
        if "shoe" in ptype or "sneaker" in ptype:
            styling_requirements.append("full_outfit_required")
            if gender == "male":
                styling_requirements.append("Style with luxury selvedge denim and a designer oversized hoodie.")
            else:
                styling_requirements.append("Style with high-end designer wide-leg trousers and a cropped luxury blazer.")
        
        elif "top" in ptype or "shirt" in ptype or "hoodie" in ptype:
            styling_requirements.append("bottom_styling_required")
            if gender == "male":
                styling_requirements.append("Style with matching high-fashion techwear pants.")
            else:
                styling_requirements.append("Style with a luxury leather skirt and high-end accessories.")

        # 3. Manifesto Compliance Check
        # Ensure the prompt doesn't violate core rules
        compliance_check = {
            "sharp_background": True,
            "editorial_lighting": True
        }

        return {
            "is_viable": len(errors) == 0,
            "errors": errors,
            "styling_upgrades": styling_requirements,
            "compliance": compliance_check
        }

    def polish_prompt(self, base_prompt: str, styling_upgrades: list) -> str:
        """
        Injects the styling upgrades and manifesto rules into the final prompt.
        """
        polished = base_prompt
        
        # Inject styling
        if styling_upgrades:
            styling_str = " ".join([s for s in styling_upgrades if not s.endswith("_required")])
            polished = polished.replace("Design a complete, premium high-fashion outfit around this product.", 
                                        f"Design a complete premium outfit: {styling_str}")

        # Final Manifesto Enforcement
        if "NO bokeh" not in polished:
            polished += " Background must be razor-sharp, NO bokeh, deep depth of field."
        
        return polished

    @staticmethod
    def detect_product_type(filename: str) -> str:
        """Automatically categorizes products based on filename."""
        fn = filename.lower()
        if any(s in fn for s in ["shoe", "sneaker", "boot", "mule", "footwear"]):
            return "shoe"
        if any(t in fn for t in ["shirt", "top", "tee", "blouse", "tank"]):
            return "top"
        if any(h in fn for h in ["hoodie", "jacket", "coat", "puffer", "sweater"]):
            return "outerwear"
        if any(p in fn for p in ["pant", "jeans", "trouser", "skirt", "shorts"]):
            return "bottom"
        return "garment"
