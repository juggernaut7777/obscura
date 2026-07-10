"""
Photography Director v2 — Real Fashion Intelligence
=====================================================
Inspired by Ashluxe, shotbyenoma, Highest Vogue, and real editorial campaigns.

Now includes:
  - DUO/GROUP shots (matching fits, couples, crew)
  - COMPLETE OUTFIT flat lays (shirt + shorts + belt + sneakers styled together)
  - STORY-DRIVEN locations (airport tarmac, hedge gardens, Lagos nightlife)
  - PROPS & ENVIRONMENTAL DETAILS (dogs, skateboards, vintage cars, coffee)
  - MOOD DIRECTION per shot ("quiet power", "engineered confidence")
  - Cultural specificity (Nigerian street, London estate, Tokyo alley)

Usage:
    from photo_director import PhotoDirector
    director = PhotoDirector()
    shoot = director.plan_shoot("Flame Print Denim Set", "set", "streetwear")
"""
import random

# ==========================================
# MOOD DIRECTIONS — The Soul of the Shot
# ==========================================
MOODS = {
    "quiet_power": "The mood is quiet power. Stillness. The subject owns the frame without trying. No smile, no performance — just presence. Think Phoebe Philo-era Celine.",
    "engineered_confidence": "The mood is engineered confidence. Every stitch, every fold, every shadow is deliberate. The garment speaks louder than the person. Think Ashluxe 'worn with presence'.",
    "after_hours": "The mood is after-hours energy. The night is young, the city hums. Neon reflections, slight motion blur, the feeling of going somewhere important.",
    "sunday_morning": "The mood is Sunday morning. Soft, unhurried, golden. Coffee steam, bare feet on warm floors, the garment worn loose and comfortable.",
    "main_character": "The mood is main character energy. Walking through the world like the camera follows you. Cinematic, unapologetic, aspirational.",
    "archive_editorial": "The mood is archive editorial. Timeless, museum-quality. The garment is a piece of fashion history being documented. Clean, precise, reverent.",
    "street_gospel": "The mood is street gospel. Raw, authentic, rooted in culture. The block, the crew, the energy of real people wearing real clothes in real neighborhoods.",
    "tropical_heat": "The mood is tropical heat. Warm humidity, rich saturated greens, sweat on skin. The garment breathes in the heat. Lagos, Accra, Kingston energy.",
}

# ==========================================
# STORY LOCATIONS — Not Generic, Cinematic
# ==========================================
LOCATIONS = {
    # --- CINEMATIC / EDITORIAL ---
    "airport_tarmac_dusk": (
        "On an empty private airport tarmac at dusk. A sleek jet partially visible in the "
        "background, grey sky fading to deep blue. Wet tarmac reflecting the last light. "
        "Industrial airport lighting towers in the far distance. Cinematic isolation."
    ),
    "hedge_garden_mansion": (
        "Standing in front of a perfectly manicured tall hedge wall, deep green, geometric. "
        "Gravel path underfoot. Victorian mansion windows visible above the hedge line. "
        "Overcast London light, flat and even. Quiet power. @shotbyenoma aesthetic."
    ),
    "brutalist_stairwell": (
        "Inside a raw concrete brutalist stairwell. Geometric shadows from overhead skylights "
        "cutting diagonal lines across the walls. The model framed between concrete planes. "
        "Moody, architectural, Zaha Hadid energy."
    ),
    "soho_cobblestone_street": (
        "On a cobblestone street in Soho, New York or London. Historic cast-iron architecture "
        "blurring in the background. High-end boutique windows reflecting the late afternoon sun. "
        "The energy of a global fashion capital. Premium, modern, cosmopolitan."
    ),
    "london_council_block": (
        "On the walkway of a London council estate. Concrete balcony rail, blue metal doors "
        "in background, a red post box at the far end. Grey overcast sky. "
        "Authentic British street culture. Skepta album cover energy."
    ),
    "vintage_car_hood": (
        "Leaning on the hood of a matte black vintage Mercedes W123 or BMW E30. "
        "Empty parking lot at golden hour. Chrome details catching warm light. "
        "One hand on the car, weight shifted. Effortless Americana meets European cool."
    ),
    "rooftop_skyline_dusk": (
        "On an urban rooftop at blue hour. City skyline glowing behind — tower lights, "
        "cranes, distant traffic streaks. Gravel surface, metal railing, a water tank. "
        "The model silhouetted against the last light. Cinematic, aspirational."
    ),
    "tokyo_vending_alley": (
        "In a narrow Tokyo side alley at night. Three vending machines glowing blue, orange, "
        "and white. Wet asphalt reflecting neon. Power lines overhead. A single bicycle "
        "leaning against the wall. Atmospheric urban density."
    ),
    "white_cube_gallery": (
        "In a pristine white-cube art gallery. Polished concrete floor, track lighting, "
        "a single large abstract canvas on the wall. The model IS the exhibit. "
        "Minimal, clean, the garment is the art."
    ),
    "greenhouse_tropical": (
        "Inside a Victorian glass greenhouse. Tropical plants, hanging ferns, condensation "
        "on glass panels. Dappled light through canopy. Warm, humid, organic. "
        "The garment surrounded by living texture."
    ),
    "basketball_court_night": (
        "On an outdoor basketball court at night. Chain-link fence, court markings, "
        "a single overhead floodlight casting hard shadows. Urban, athletic, raw. "
        "The model standing at center court."
    ),
    "beach_bonfire_dusk": (
        "On a beach at dusk near a small bonfire. Warm firelight on skin, "
        "dark ocean behind, sparks floating. Sand texture, driftwood. "
        "Intimate, primal, storytelling."
    ),
}

# ==========================================
# LIGHTING SETUPS
# ==========================================
LIGHTING = {
    "rembrandt": "Rembrandt lighting: key at 45 degrees camera-left creating the signature triangle on the shadow-side cheek. Warm fill from a V-flat. Deep background shadows.",
    "golden_hour_rim": "Golden hour backlight: warm amber from behind creating a glowing rim on hair and shoulders. Face lit by soft bounce. Natural lens flare allowed.",
    "overcast_london": "Overcast London light: massive natural diffusion from thick clouds. No harsh shadows, even illumination, rich saturated colors. Moody, flat, editorial.",
    "neon_mixed": "Mixed neon ambient: cool blue and warm magenta reflecting off wet surfaces. No flash. The environment IS the lighting. Urban night.",
    "single_spotlight": "Single hard spotlight from above-right. Deep dramatic shadows. Most of the frame in darkness. Chiaroscuro. The garment emerges from black.",
    "window_soft": "Large window natural light from the left. Soft gradient shadows. No artificial light. Intimate, warm, editorial morning feel.",
    "bonfire_warm": "Warm practical firelight or tungsten. Orange-amber cast on skin. Deep shadows everywhere else. Intimate, primal, after-hours.",
    "fluorescent_raw": "Raw fluorescent overhead light. Slightly green cast. Unflattering on purpose — makes the garment look REAL, not retouched. Documentary authenticity.",
    "ring_light_ugc": "Ring light from directly in front. Catch light circles visible in eyes. Even illumination on face. Classic influencer/GRWM setup.",
}

# ==========================================
# CAMERA + LENS SETUPS
# ==========================================
CAMERAS = {
    "85mm_portrait": "Shot on 85mm f/1.4 lens, camera at chest height. Shallow depth of field, creamy bokeh background. Classic portrait compression.",
    "35mm_wide_street": "Shot on 35mm f/2.0 lens, showing environment and subject together. Slight barrel distortion. Street photography energy.",
    "50mm_standard": "Shot on 50mm f/1.8 lens at waist height. Natural perspective, no distortion. The closest to how the human eye sees.",
    "100mm_macro_detail": "Shot on 100mm macro lens, f/2.8. Inches from the fabric. Focus stacked. Shows thread weave, zipper teeth, label stitching.",
    "low_angle_24mm": "Shot on 24mm from knee height, looking up. Dramatic perspective distortion. Makes the subject tower. Power shot.",
    "iphone_ugc": "Shot on iPhone 15 Pro front camera. Slightly warm, natural grain, casual angle. Authentic UGC aesthetic.",
    "medium_format_editorial": "Shot on Hasselblad medium format, 80mm lens. Razor sharp detail, massive dynamic range. Fashion campaign quality.",
    "kodak_portra_film": "Shot on 35mm Kodak Portra 400 film. Warm color cast, organic grain, soft highlight rolloff. Analog editorial.",
    "overhead_flat": "Shot from directly overhead, 35mm f/8. Even sharpness edge to edge. Flat lay photography.",
}

# ==========================================
# MODEL ACTIONS
# ==========================================
ACTIONS = {
    "hands_in_pockets": "Standing with both hands in pockets, slight forward lean, looking directly into camera. Confident, minimal.",
    "adjusting_collar": "Both hands reaching up to adjust the collar, chin slightly lifted, looking off-camera. Caught in the moment.",
    "leaning_wall": "Leaning against the wall with one shoulder, arms crossed loosely, weight on one leg. Relaxed, unbothered.",
    "walking_toward": "Walking confidently toward camera, mid-stride. Arms swinging naturally. Slight motion blur on trailing leg.",
    "crouching": "Crouching with forearms on knees, looking up at camera. Streetwear signature pose.",
    "turning_away": "Captured mid-turn, looking back over shoulder. Shows the back of the garment. Dynamic.",
    "sitting_edge": "Sitting on a concrete ledge, legs extended at an angle, leaning back on one arm. Casual, unbothered.",
    "caught_laughing": "Caught mid-laugh, head tilted back, eyes crinkled. Genuine candid moment.",
    "hands_on_hips_power": "Hands on hips, feet shoulder-width apart, chest open, direct eye contact. Power stance. Adidas campaign energy.",
    "dog_companion": "Standing relaxed with a dog sitting at their feet or on a leash beside them. The dog adds life and authenticity. Lifestyle moment.",
    "holding_coffee": "One hand holding a takeaway coffee cup, other hand in pocket. Mid-stride on a sidewalk. Morning energy.",
    "phone_in_hand": "Looking at phone in one hand, slight smile. The other hand adjusting the garment. Natural modern moment.",
}

# ==========================================
# BACKGROUND PROPS — Environmental Storytelling
# ==========================================
PROPS = {
    "streetwear": [
        "A Rottweiler or Doberman sitting obediently at the model's feet, alert and poised.",
        "A vintage boombox sitting on the ground beside the model.",
        "A basketball tucked under one arm.",
        "A skateboard leaning against the wall behind.",
        "Graffiti-tagged wall partially visible in the background.",
        "A matte black motorcycle parked in the background, slightly out of focus.",
    ],
    "luxury": [
        "A sleek black town car visible in the background, door open.",
        "A leather attaché case on the ground beside the model.",
        "A small espresso cup on a marble ledge nearby.",
        "An architectural staircase spiraling behind.",
        "A single white orchid in a stone pot in the background.",
    ],
    "casual": [
        "A golden retriever walking alongside on a leash.",
        "A tote bag slung over one shoulder.",
        "Earbuds dangling from one hand.",
        "A bicycle leaned against a railing behind.",
        "A half-drunk iced coffee on a bench nearby.",
    ],
    "editorial": [
        "No props. Negative space IS the prop. The environment tells the story.",
        "A single dramatic element in the background — a pillar, a doorway, a shadow.",
        "A mirror visible reflecting the model from another angle.",
    ],
}

# ==========================================
# OUTFIT FLAT LAY COMPOSITIONS
# ==========================================
FLAT_LAY_STYLES = {
    "streetwear_full": (
        "A premium overhead flat lay photograph of a complete streetwear outfit styled on "
        "a textured grey carpet or raw concrete floor. The main garment centered with 'stuffed volume' "
        "so it looks three-dimensional. Below: coordinated shorts or pants folded once showing the waistband. "
        "To the left: a pair of sneakers placed at a casual angle, laces loose. "
        "A studded or graphic belt coiled near the waistband. "
        "A chain necklace or watch placed near the collar. "
        "Every item is from the reference image — match them EXACTLY. "
        "Shot from directly overhead, soft diffused light from above-left. "
        "Highest Vogue / streetwear brand flat lay aesthetic."
    ),
    "minimal_luxury": (
        "A premium overhead flat lay of a luxury outfit on a matte black linen surface. "
        "The garment folded precisely, showing the label. Beside it: a leather wallet, "
        "a pair of sunglasses, and car keys with a premium fob. "
        "Minimal, clean, negative space around each item. "
        "Soft studio lighting, no harsh shadows. "
        "Shot overhead on medium format camera. Mr Porter product styling."
    ),
    "casual_weekend": (
        "A lifestyle flat lay of a casual weekend outfit on an unmade white linen bed. "
        "The garment tossed casually but artfully. Beside it: white sneakers, a baseball cap, "
        "AirPods case, a small cologne bottle. A book with a coffee cup ring stain nearby. "
        "Warm morning window light. Lived-in, authentic. "
        "Shot from above at a slight angle. Instagram lifestyle content."
    ),
}

# ==========================================
# DUO / GROUP SHOT COMPOSITIONS
# ==========================================
DUO_COMPOSITIONS = {
    "matching_fits_walk": (
        "Two models walking side by side toward the camera wearing coordinating outfits from the "
        "reference images. Both wearing the SAME garment in different colorways, or complementary "
        "pieces from the same collection. Walking in sync, mid-stride, on a clean urban sidewalk. "
        "One model looking at camera, the other looking slightly away. "
        "Overcast light, 50mm lens, full body. Matching energy, individual style."
    ),
    "couple_editorial": (
        "A man and woman standing close together, both wearing pieces from the collection. "
        "She leans slightly into him, his arm around her shoulder. Both looking off-camera "
        "in the same direction. Cinematic golden hour backlight. "
        "85mm lens, shallow depth of field. The couple is the campaign. Fashion power couple energy."
    ),
    "crew_lineup": (
        "Three models standing in a row against a plain wall, each wearing a different piece "
        "from the collection. Varied poses — one with arms crossed, one hands in pockets, "
        "one crouching. Different heights, different builds, same brand energy. "
        "Dead center camera, flash photography, confrontational. Crew campaign."
    ),
    "friends_candid": (
        "Two friends sitting on concrete steps, both wearing the garment. One is laughing, "
        "the other looking at their phone. A dog sitting between them. Takeaway coffee cups "
        "on the step. Natural afternoon light. Candid, unposed, real friendship. "
        "35mm film aesthetic, warm tones. UGC that sells."
    ),
    "back_to_back": (
        "Two models standing back-to-back, arms crossed, both wearing the garment. "
        "Looking in opposite directions. Symmetrical composition. Studio or clean wall background. "
        "Even lighting. The garment is the connection between them. "
        "Strong, graphic, social-media-ready composition."
    ),
}


class PhotoDirector:
    """Plans fashion shoots with real creative direction."""

    def plan_shoot(self, product_name, garment_type, style="streetwear", 
                   reference_note=None, model_desc=None, 
                   include_duo=True, include_flatlay=True, 
                   companion_items=None, drop_location=None, drop_lighting=None):
        """
        Creates a cohesive, multi-shot editorial plan for a garment.
        If drop_location and drop_lighting are provided, it locks the aesthetics
        to create a unified 'Lookbook' campaign across multiple products.
        """
        ref = f"Using the reference image as the EXACT garment. Match every detail — color, print, hardware, label, stitching. {reference_note} " if reference_note else ""
        model = f"The model is {model_desc}. Face and body match reference exactly. " if model_desc else ""
        mood = random.choice(list(MOODS.values()))
        prop = random.choice(PROPS.get(style, PROPS["streetwear"]))

        shots = []

        # Lock the aesthetics for the 'Drop/Lookbook' if provided, otherwise random
        loc = drop_location if drop_location else self._pick(LOCATIONS, style)
        light = drop_lighting if drop_lighting else self._pick(LIGHTING, style)

        # === 1. HERO — Cinematic story shot ===
        cam = CAMERAS["85mm_portrait"]
        action = self._pick(ACTIONS)

        shots.append({"name": "hero", "priority": 1, "prompt": (
            f"{ref}{model}"
            f"Hyperrealistic fashion editorial photograph. {mood} "
            f"The model wears {product_name}. {action} {loc} {light} {cam} "
            f"{prop} "
            f"The garment has realistic fabric weight, natural drape and creasing. "
            f"Visible skin texture, natural pores, no AI smoothing. RAW photo, 8K."
        )})

        # === 2. DETAIL MACRO — Sell the craft ===
        shots.append({"name": "detail", "priority": 2, "prompt": (
            f"{ref}"
            f"Extreme close-up macro photograph of {product_name}. "
            f"{CAMERAS['100mm_macro_detail']} "
            f"Focus on a key design element: stitching, zipper pull, label, fabric weave, "
            f"or print detail. Shallow depth of field. Soft directional side lighting "
            f"revealing every fiber. The viewer can almost touch it. "
            f"Commercial product photography. 8K resolution."
        )})

        # === 3. LIFESTYLE — Candid story moment ===
        loc2 = self._pick(LOCATIONS, style, exclude_val=loc)
        action2 = random.choice(["caught_laughing", "holding_coffee", "phone_in_hand", "dog_companion"])

        shots.append({"name": "lifestyle", "priority": 2, "prompt": (
            f"{ref}{model}"
            f"Hyperrealistic candid lifestyle photograph. {mood} "
            f"The model wears {product_name}. {ACTIONS[action2]} {loc2} "
            f"{self._pick(LIGHTING)} "
            f"{CAMERAS['kodak_portra_film']} "
            f"This should feel like a candid moment captured by a friend. "
            f"Natural skin texture, one flyaway hair. The garment is part of the story. "
        )})

        # === 4. POWER SHOT — Low angle, confrontational ===
        shots.append({"name": "power", "priority": 2, "prompt": (
            f"{ref}{model}"
            f"Hyperrealistic low-angle fashion photograph. "
            f"The model wears {product_name}. {ACTIONS['hands_on_hips_power']} "
            f"{loc} {LIGHTING['single_spotlight']} "
            f"{CAMERAS['low_angle_24mm']} "
            f"The model towers over the camera. The garment billows with authority. "
            f"Dramatic, confrontational. Fashion power shot."
        )})

        # === 5. OUTFIT FLAT LAY (if requested) ===
        if include_flatlay:
            flatlay_base = self._pick(FLAT_LAY_STYLES, style)
            companion_text = ""
            if companion_items:
                companion_text = f" Companion items styled alongside: {', '.join(companion_items)}."
            shots.append({"name": "flatlay", "priority": 3, "prompt": (
                f"{ref}{flatlay_base}{companion_text}"
            )})

        # === 6. DUO / GROUP (if requested) ===
        if include_duo:
            duo = self._pick(DUO_COMPOSITIONS, style)
            shots.append({"name": "duo", "priority": 3, "prompt": (
                f"{ref}{duo} "
                f"The garment is {product_name}. {mood}"
            )})

        # === 7. UGC SOCIAL — Mirror selfie / GRWM ===
        shots.append({"name": "ugc", "priority": 4, "prompt": (
            f"{ref}{model}"
            f"Hyperrealistic mirror selfie. The model wears {product_name}. "
            f"Full-length mirror in a modern apartment hallway. Phone at chest height. "
            f"Other hand adjusting the garment. Warm LED light. Slightly messy background: "
            f"coat rack, shoes on floor, tote bag on hook. "
            f"{CAMERAS['iphone_ugc']} "
            f"No filter, no editing. A real customer post. Authentic GRWM content."
        )})

        return shots

    def _pick(self, source, style=None, exclude_val=""):
        """Pick a random value from a dict, optionally filtered by style."""
        if isinstance(source, dict):
            keys = list(source.keys())
            vals = [source[k] for k in keys if source[k] != exclude_val]
            return random.choice(vals) if vals else list(source.values())[0]
        return random.choice(list(source)) if source else ""


# ==========================================
# 5-HOUR SMART SCHEDULER
# ==========================================
class ProductionScheduler:
    """Maximizes output during the 5-hour daily PC window."""

    def __init__(self, window_hours=5.0, interval_minutes=10):
        self.window_hours = window_hours
        self.interval_minutes = interval_minutes
        self.max_generations = int((window_hours * 60) / interval_minutes)

    def plan_daily_queue(self, products: list) -> list:
        queue = []
        budget = self.max_generations
        for product in products[:10]:
            if budget <= 0:
                break
            director = PhotoDirector()
            shots = director.plan_shoot(
                product.get("name", "Unknown"),
                product.get("type", "jacket"),
                product.get("style", "streetwear"),
                reference_note=product.get("reference_image_url", ""),
                companion_items=product.get("companion_items"),
            )
            shots.sort(key=lambda s: s["priority"])
            for shot in shots:
                if budget <= 0:
                    break
                queue.append({
                    "product_name": product.get("name"),
                    "shot_name": shot["name"],
                    "prompt": shot["prompt"],
                    "reference_image_url": product.get("reference_image_url", ""),
                    "priority": shot["priority"],
                })
                budget -= 1
        return queue

    def get_stats(self):
        return {
            "window_hours": self.window_hours,
            "interval_minutes": self.interval_minutes,
            "max_gens_per_day": self.max_generations,
            "max_images_per_day": self.max_generations * 2,
            "max_products_per_day": self.max_generations // 4,
        }


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    director = PhotoDirector()
    shoot = director.plan_shoot(
        product_name="Flame Print Washed Denim Set",
        garment_type="set",
        style="streetwear",
        companion_items=["khaki cargo shorts", "studded star belt", "red Dunk Low sneakers"],
    )

    print(f"\nSHOOT PLAN: {len(shoot)} shots")
    print("=" * 60)
    for i, shot in enumerate(shoot, 1):
        print(f"\n--- Shot {i}: {shot['name'].upper()} (P{shot['priority']}) ---")
        print(shot["prompt"][:300] + "...")

    stats = ProductionScheduler().get_stats()
    print(f"\nDAILY: {stats['max_images_per_day']} images, {stats['max_products_per_day']} products")
