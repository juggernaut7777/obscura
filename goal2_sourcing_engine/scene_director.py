"""
SCENE DIRECTOR — Fashion Editorial Intelligence Engine
=======================================================
Generates diverse, hyper-specific scene/lighting/camera combinations
for the 4-shot campaign layout. Every generation is unique.

Architecture:
Architecture:
  Shot 1 (EDITORIAL)  → Hypebeast editorial / Urban industrial / High-end Streetwear
  Shot 2 (LIFESTYLE)  → Street snap / Tunnel walk / Hypebeast candid
  Shot 3 (STREET)     → Additional urban context / Modified car scene
  Shot 4 (FLAT LAY)   → Product-only styled flat lay (Full Outfit)
  Shot 5 (GHOST)      → Ghost mannequin / hollow hanger (Full Outfit)

The engine randomly combines SCENE + LIGHTING + CAMERA + MOOD
to produce endless variety while staying on-brand.

Style-Aware:
  scene_style = "gritty_urban"  → streetwear/techwear/y2k scenes
  scene_style = "soft_studio"   → elegant/formal/women's scenes
  scene_style = "sport_court"   → athleisure/activewear scenes
  scene_style = "minimal_clean" → basics/accessories
"""

import json
import random
from pathlib import Path


def load_style_tags(product_folder: str) -> dict:
    """Load style tags from a product folder if available."""
    try:
        tags_file = Path(product_folder) / "style_tags.json"
        if tags_file.exists():
            return json.loads(tags_file.read_text(encoding="utf-8"))
        # Also check outfit_metadata.json for merged outfits
        outfit_file = Path(product_folder) / "outfit_metadata.json"
        if outfit_file.exists():
            meta = json.loads(outfit_file.read_text(encoding="utf-8"))
            return {
                "scene_style": meta.get("scene_style", "minimal_clean"),
                "gender": meta.get("gender", "unisex"),
                "niche": meta.get("niche", "basics"),
            }
    except Exception:
        pass
    return {}



# ═══════════════════════════════════════════════════════════════
# SHOT 1 — STREETWEAR EDITORIAL  (Fear of God / Essentials / Corteiz)
# ═══════════════════════════════════════════════════════════════

EDITORIAL_SCENES = [
    "crouching in a high-contrast industrial warehouse, raw concrete and steel environment",
    "standing in a subway station with flickering fluorescent lights and motion-blurred train",
    "leaning against a chain-link fence in a moody urban alleyway at night, neon reflections",
    "mid-stride on a brutalist concrete staircase, sharp shadows and geometric lines",
    "posed in front of a wall of vintage CRT monitors in a dark tech-noir setting",
    "standing on a rain-slicked city street, futuristic urban architecture in background",
    "seated on a customized low-rider bike in a gritty downtown garage",
    "posed in a dark room with a single high-intensity laser beam cutting through smoke",
    "walking through a shipping container yard, vibrant metal textures and industrial scale",
    "standing on an elevated train platform, sunset city skyline with high contrast",
    "posed in a luxury underground parking lot with sleek supercars in soft focus",
    "crouching on a rooftop with a panoramic night view of a cyberpunk-style metropolis",
]

EDITORIAL_LIGHTING = [
    "harsh dramatic spotlight from above, high-contrast urban shadows",
    "moody blue and magenta neon lighting, cyberpunk night aesthetic",
    "strong rim lighting from a sodium-vapor street lamp, orange and teal tones",
    "strobe flash photography, high-key aggressive street editorial vibe",
    "gritty low-key lighting, deep blacks and sharp highlights, industrial mood",
    "single overhead warm beam in a cold dark space, dramatic and focused",
    "diffused moonlight filtering through smoke and haze, ethereal yet urban",
    "flickering fluorescent light aesthetic, cool green-tinted industrial shadows",
    "cinematic anamorphic lens flares, warm horizontal light streaks",
    "underlighting from a floor grate, dramatic shadows cast upwards",
]

EDITORIAL_CAMERA = [
    "shot on Hasselblad H6D-100c, 85mm f/1.8 macro lens, hyper-realistic skin texture, visible pores, unretouched, medium format clarity",
    "shot on Canon EOS R5, 70-200mm f/2.8 at 135mm, raw photo, natural fine lines, peach fuzz, compressed perspective",
    "shot on Phase One IQ4, 80mm Schneider lens, microscopic skin detail, subtle subsurface scattering, insane detail",
    "shot on Sony A1, 85mm GM f/1.4, creamy bokeh, tack-sharp focus on skin texture, no beauty filters",
    "shot on 35mm film, Kodak Portra 400, fine grain, subtle filmic color, organic skin imperfections",
    "shot on Leica S3, 90mm Summarit, classic European editorial aesthetic, photorealistic texture",
]

EDITORIAL_MOOD_SHARED = [
    "Hypebeast editorial aesthetic. Cold gaze, relaxed but dominant stance.",
    "Fear of God / Essentials campaign energy. Oversized silhouette, luxury streetwear vibes.",
    "Corteiz 'Rule the World' aesthetic. Gritty, raw, authentic street energy.",
    "Margiela / Balenciaga avant-garde swag. Effortless cool, architectural layering.",
    "Bape / LV street luxury. Bold patterns, vibrant energy, high-end drip.",
    "Roaringwild / Randomevent urban hype aesthetic. 90s nostalgia meets modern techwear, effortlessly cool.",
    "Sankuanz / Feng Chen Wang avant-garde energy. Dystopian streetwear, deconstructed tailoring, striking silhouette.",
    "SoulGoods / CLOT heritage streetwear vibe. East meets West swagger, bold cultural references, raw street energy.",
]

EDITORIAL_MOOD_FEMALE = EDITORIAL_MOOD_SHARED + [
    "Baddie streetwear vibe. Fierce, confident, oversized fit with sleek styling.",
    "Cyberpunk street-girl energy. High-tech, low-life aesthetic, sharp and edgy.",
    "Model-off-duty hypebeast look. Baggy cargo pants, oversized hoodie, heavy sneakers.",
]

EDITORIAL_MOOD_MALE = EDITORIAL_MOOD_SHARED + [
    "NBA tunnel walk drip. High-intensity swagger, everything premium and oversized.",
    "UK Drill aesthetic. Brooding, sharp, industrial street presence.",
    "L.A. Hypebeast look. Sunshine, concrete, high-contrast swagger.",
]


# ═══════════════════════════════════════════════════════════════
# SHOT 2 — LIFESTYLE / GRWM / CASUAL  (Instagram / TikTok / Celeb)
# ═══════════════════════════════════════════════════════════════

LIFESTYLE_SCENES_FEMALE = [
    "stepping out of a matte-black G-Wagon, urban streetwear fit, flash photography",
    "standing in a busy Shibuya-style crossing at night, neon lights everywhere",
    "sitting on the hood of a modified drift car in an underground garage",
    "walking through a graffiti-covered skatepark, golden hour lighting",
    "leaning against a convenience store neon sign at 2 AM, cinematic night mood",
    "checking a fit in a reflective mirrored building in a tech-district",
    "candid street snap in London Soho, heavy layering, bucket hat vibe",
    "at a high-end sneaker boutique, holding a limited-edition box",
    "standing on a subway platform, motion blur of a passing train",
    "posing in a dark studio with red laser light effects, tech-wear style",
    "walking through a futuristic airport lounge, oversized travel fit",
    "seated in a VIP booth at a moody nightclub, soft purple glow",
]

LIFESTYLE_SCENES_MALE = [
    "leaning against a modified JDM car, moody night lighting, urban backdrop",
    "walking through a gritty industrial district, oversized hoodie, heavy chain jewelry",
    "entering an exclusive hypebeast pop-up shop, architectural industrial lighting",
    "sitting on a concrete ledge in a brutalist plaza, minimal high-end fit",
    "stepping out of a luxury sports car, flash photography, paparazzi energy",
    "candid moment in a dark studio with atmospheric smoke and blue light",
    "walking through a neon-lit alleyway in Hong Kong, cinematic reflections",
    "leaning on a rooftop railing overlooking a sprawling metropolis at night",
    "at a basketball court at dusk, urban atmosphere, city lights in background",
    "seated in a customized gaming setup, RGB lighting reflections on skin",
    "standing in an industrial elevator, raw metal textures, moody lighting",
    "walking through a futuristic parking garage, tech-wear aesthetic",
]

LIFESTYLE_LIGHTING = [
    "golden hour sun, warm amber tones, long shadows, natural and dreamy",
    "soft overcast natural light, even illumination, no harsh shadows, editorial clean",
    "neon city lights reflecting off wet pavement, pink and blue glow, night energy",
    "warm café interior tungsten light, cozy and inviting, slight orange cast",
    "bright midday sun with shade, contrasty light patches, authentic street snap",
    "blue hour twilight, cool purple-blue ambient light, serene and cinematic",
    "ring light catch-light in eyes, front-lit GRWM aesthetic, beauty influencer look",
    "dappled sunlight through tree canopy, natural bokeh, organic warmth",
    "flash photography pop, high-contrast street-style capture, candid energy",
    "window light from the side, Vermeer-style illumination, intimate and warm",
]

LIFESTYLE_CAMERA = [
    "shot on iPhone 15 Pro Max, natural HDR, unretouched skin, visible pores, authentic social media aesthetic",
    "shot on Sony A7IV, 35mm f/1.4, raw photo, natural skin texture, wide lifestyle framing, environmental portrait",
    "shot on Fujifilm X-T5, 56mm f/1.2, classic film simulation colors, organic imperfections",
    "shot on Canon R6 II, 50mm f/1.2, creamy bokeh, razor-sharp focus on realistic face details",
    "shot on 35mm film, Kodak Gold 200, warm nostalgic tones, slight grain, no AI glow",
    "shot on iPhone front camera, selfie perspective, flash on, hyper-detailed skin pores, authentic UGC energy",
]

LIFESTYLE_MOOD_FEMALE = [
    "Street baddie aesthetic. Bold, oversized, heavy on accessories.",
    "Hypebeast energy. Head-to-toe street drip, effortlessly cool.",
    "Fit-check energy. Adjusting hoodie strings, checking sneakers, authentic.",
    "Off-duty model caught by street-style photographer. Sunglasses, oversized fit.",
    "TikTok viral streetwear aesthetic. Dynamic, high-energy, trend-setting.",
    "Cyberpunk-girl mood. Tech-focused, dark, futuristic street style.",
    "Gritty urban vibe. Raw, unapologetic, authentic street culture.",
    "Main character energy. Dominating the scene, oversized everything.",
]

LIFESTYLE_MOOD_MALE = [
    "Street-wear icon. Heavy layering, oversized silhouette, undeniable swag.",
    "Hypebeast energy. Head-to-toe limited edition drip, effortlessly cool.",
    "NBA tunnel walk swagger. Aggressive confidence, premium streetwear.",
    "UK Drill mood. Brooding intensity, sharp and industrial street style.",
    "L.A. Hypebeast aesthetic. Clean, sun-drenched, high-contrast street vibe.",
    "Modified car culture energy. Low-key, mechanical, gritty and cool.",
    "Tech-wear specialist. Functional, dark, futuristic street presence.",
    "Main character energy. Icy gaze, oversized hoodie, heavy on the drip.",
]


# ═══════════════════════════════════════════════════════════════
# SHOT 3 — FLAT LAY (Product-Only, No Model)
# ═══════════════════════════════════════════════════════════════

FLATLAY_SCENES = [
    "neatly folded on a clean white marble surface, styled with a leather watch and sunglasses",
    "expertly styled on a sleek slate display table, high-end boutique lighting",
    "arranged perfectly on a brushed steel surface, avant-garde minimalist fashion display",
    "placed on a concrete floor with eucalyptus sprigs, minimalist Scandinavian aesthetic",
    "styled on a premium suede tray with gold accessories, warm luxury palette",
    "hanging on a minimal matte-black hanger against a cream plaster wall, boutique display",
    "folded on a velvet podium, luxury unboxing aesthetic with subtle shadows",
    "laid flat on an illuminated frosted glass table, ultra-modern futuristic retail vibe",
    "styled on a luxury velvet couch, lifestyle aesthetic with natural lighting",
    "laid flat on an aesthetic messy bed with white linen sheets, casual morning vibe",
    "arranged creatively on a textured floor rug, high-end Instagram flat lay style",
]

FLATLAY_CAMERA = [
    "overhead bird's-eye view, iPhone 15 Pro, clean and sharp",
    "45-degree angle, 50mm lens f/2.8, shallow focus on garment details",
    "flat overhead shot, soft diffused window light from the left, no harsh shadows",
]


# ═══════════════════════════════════════════════════════════════
# SHOT 4 — GHOST MANNEQUIN / HOLLOW HANGER
# ═══════════════════════════════════════════════════════════════

GHOST_SCENES = [
    "invisible mannequin, garment appears to float with natural volume and drape",
    "hollow-man effect, garment shaped as if worn by an invisible person, 3D form visible",
    "ghost mannequin with front and back composite, showing full garment construction",
]

GHOST_LIGHTING = [
    "clean white studio cyclorama, even soft lighting from multiple angles, no shadows",
    "bright high-key studio, minimal shadows, commercial e-commerce standard",
    "soft gradient background from white to light grey, professional catalog lighting",
]


# ═══════════════════════════════════════════════════════════════
# ELEGANT / FORMAL SCENE POOLS  (women's elegant, formal)
# ═══════════════════════════════════════════════════════════════

ELEGANT_SCENES = [
    "seated at a marble-top cafe table with a latte and fresh flowers, soft morning light",
    "walking through a sun-drenched art gallery with white walls and abstract paintings",
    "standing in front of a floor-to-ceiling window overlooking a European cityscape",
    "browsing in a high-end boutique, warm golden interior lighting",
    "seated on a chaise longue in a bright minimalist studio, editorial pose",
    "strolling through a botanical garden, soft dappled natural light",
    "standing on a Parisian street corner, cobblestones, warm afternoon glow",
    "at a rooftop terrace restaurant at sunset, city lights beginning to appear",
]

ELEGANT_LIGHTING = [
    "soft diffused natural window light, warm white tones, no harsh shadows",
    "golden hour natural light, warm amber glow, long soft shadows",
    "professional studio beauty lighting, soft boxes on both sides, bright and airy",
    "romantic candlelight ambience, warm flickering tones, intimate and luxurious",
    "overcast daylight through sheer curtains, even and diffused, ultra-soft",
]

ELEGANT_CAMERA = [
    "shot on Sony A7IV 85mm f/1.8, shallow depth of field, creamy bokeh, natural skin",
    "shot on Canon R5 50mm f/1.4, soft tones, film-like warmth, natural imperfections",
    "shot on Fujifilm X-T5 56mm, classic film simulation, warm gentle colors",
]

ELEGANT_MOOD = [
    "Old Money aesthetic. Quiet luxury, effortless elegance, understated wealth.",
    "Parisian chic. Effortlessly sophisticated, classic yet modern.",
    "Editorial beauty. Refined confidence, graceful movement, high-fashion poise.",
    "Soft girl era. Feminine, delicate, romantic — floral and warm.",
    "Influencer off-duty. Relaxed luxury, curated casual, perfectly imperfect.",
]


# ═══════════════════════════════════════════════════════════════
# ATHLEISURE / SPORT SCENE POOLS
# ═══════════════════════════════════════════════════════════════

SPORT_SCENES = [
    "stretching on a rooftop tennis court, early morning light, clean modern setting",
    "walking out of a luxury gym with a premium gym bag, confident post-workout energy",
    "at an outdoor basketball court at golden hour, warm light casting long shadows",
    "running along a waterfront promenade, motion blur background, dynamic energy",
    "seated on bleachers at a minimalist sports stadium, natural daylight",
    "in a modern yoga studio with large windows and plants, clean natural setting",
]

SPORT_LIGHTING = [
    "bright clean daylight, even and energetic, no harsh shadows",
    "golden hour warm light, active and dynamic",
    "clean indoor sports lighting, bright whites, fresh energy",
]

SPORT_MOOD = [
    "Athletic energy. Performance meets street style, functional and fierce.",
    "Pilates princess aesthetic. Luxury activewear, soft tones, effortless fitness.",
    "Tennis core aesthetic. Preppy, clean, high-energy sport fashion.",
    "Gym-to-street look. Transition from workout to lifestyle seamlessly.",
]


# ═══════════════════════════════════════════════════════════════
# MAIN API — build_campaign_prompts()
# ═══════════════════════════════════════════════════════════════

def build_campaign_prompts(model, m_count, p_start, p_end, product_count=1, scene_style="gritty_urban", product_folder=None, is_set=False):
    """
    Build 5 unique, randomized campaign prompts based on product count AND style.
    - Solo Item (1 product, not a set): Flat lays, detail macros, ghost mannequins ONLY.
    - Merged Outfit or Set: Full body model shots using the CORRECT scene style.
      scene_style options: gritty_urban | soft_studio | sport_court | minimal_clean
    """
    # Auto-load tags from product folder if provided
    tags = {}
    if product_folder:
        tags = load_style_tags(product_folder)
        if tags:
            scene_style = tags.get("scene_style", scene_style)
            # Also override model gender if tags say something different
            tag_gender = tags.get("gender", "")
            if tag_gender and tag_gender != "unisex":
                model = {**model, "gender": tag_gender}

    p_range = f"image {p_start}" if p_start == p_end else f"images {p_start} to {p_end}"
    m_range = f"image 1" if m_count == 1 else f"images 1 to {m_count}"
    gender = model.get("gender", "female")
    
    outfit_desc = "the EXACT products" if product_count > 1 else "the EXACT product"
    if product_count > 1 or is_set:
        merge_hint = " Combine these into a single full outfit. Add fitting footwear (e.g. sneakers for sportswear, do NOT use mismatched formal shoes like heels for a gym set)."
    else:
        merge_hint = ""

    if gender == "male":
        pronoun = "He"
        lifestyle_scenes = LIFESTYLE_SCENES_MALE
        lifestyle_moods = LIFESTYLE_MOOD_MALE
        editorial_moods = EDITORIAL_MOOD_MALE
    else:
        pronoun = "She"
        lifestyle_scenes = LIFESTYLE_SCENES_FEMALE
        lifestyle_moods = LIFESTYLE_MOOD_FEMALE
        editorial_moods = EDITORIAL_MOOD_FEMALE

    # ── IF SOLO ITEM (NO MODEL) ──
    if product_count == 1:
        # Shot 1: High-end Editorial Flat Lay
        shot1 = (
            f"Professional flat lay: {outfit_desc} from {p_range} {random.choice(FLATLAY_SCENES)}. "
            f"{random.choice(FLATLAY_CAMERA)}. No human. Match colors and logos exactly. 8K."
        )
        # Shot 2: Clean E-commerce Flat Lay
        shot2 = (
            f"Professional flat lay: {outfit_desc} from {p_range} neatly folded on a clean slate background. "
            f"Soft diffused lighting from above. No human. High-end retail standard."
        )
        # Shot 3: Ghost Mannequin / Hovering
        shot3 = (
            f"Professional e-commerce photo: {random.choice(GHOST_SCENES)} showing {outfit_desc} from {p_range}. "
            f"{random.choice(GHOST_LIGHTING)}. No human. Sharp details."
        )
        # Shot 4: Macro Detail
        shot4 = (
            f"Macro detail photograph: extreme close-up of the fabric texture and hardware of {outfit_desc} from {p_range}. "
            f"Soft natural side lighting revealing depth. Razor sharp focus. No human."
        )
        # Shot 5: Alt Flat Lay
        shot5 = (
            f"Creative flat lay: {outfit_desc} from {p_range} hanging on a luxury velvet hanger against a textured concrete wall. "
            f"Cinematic moody lighting. No human. Match product exactly."
        )
        return [shot1, shot2, shot3, shot4, shot5]

    # ── IF MERGED OUTFIT OR SET (USE MODEL) ──
    else:
        # Check if Gemini generated a highly specific custom scene for this exact item
        if tags and tags.get("custom_scene"):
            primary_scenes = [tags["custom_scene"]]
            primary_lighting = [tags.get("custom_lighting", random.choice(EDITORIAL_LIGHTING))]
            primary_camera = [tags.get("custom_camera", random.choice(EDITORIAL_CAMERA))]
            primary_moods = [tags.get("custom_mood", random.choice(EDITORIAL_MOOD_MALE if pronoun=="He" else EDITORIAL_MOOD_FEMALE))]
            
            # Use secondary scenes from normal pools as backup/lifestyle variety
            secondary_scenes = [tags["custom_scene"]] + lifestyle_scenes
            secondary_moods = [tags.get("custom_mood", "effortless lifestyle")]
            
        else:
            # Fallback to hardcoded scene pools based on niche/style
            if scene_style == "soft_studio":
                primary_scenes = ELEGANT_SCENES
                primary_lighting = ELEGANT_LIGHTING
                primary_camera = ELEGANT_CAMERA
                primary_moods = ELEGANT_MOOD
                secondary_scenes = ELEGANT_SCENES
                secondary_moods = ELEGANT_MOOD
            elif scene_style == "sport_court":
                primary_scenes = SPORT_SCENES
                primary_lighting = SPORT_LIGHTING
                primary_camera = LIFESTYLE_CAMERA
                primary_moods = SPORT_MOOD
                secondary_scenes = SPORT_SCENES
                secondary_moods = SPORT_MOOD
            else:
                # Default: gritty_urban / minimal_clean → original streetwear scenes
                primary_scenes = EDITORIAL_SCENES
                primary_lighting = EDITORIAL_LIGHTING
                primary_camera = EDITORIAL_CAMERA
                primary_moods = editorial_moods
                secondary_scenes = lifestyle_scenes
                secondary_moods = lifestyle_moods

        # Shot 1: Hero Editorial
        shot1 = (
            f"{m_range} = model reference. {p_range} = {outfit_desc}. "
            f"Put {outfit_desc} from {p_range} on the model as a coordinated outfit.{merge_hint} "
            f"Full-body editorial: {pronoun} is {random.choice(primary_scenes)}. "
            f"{random.choice(primary_lighting)}. {random.choice(primary_camera)}. {random.choice(primary_moods)} 8K."
        )
        # Shot 2: Lifestyle
        shot2 = (
            f"{m_range} = model reference. {p_range} = {outfit_desc}. "
            f"Put {outfit_desc} from {p_range} on the model.{merge_hint} "
            f"Lifestyle photo: {pronoun} is {random.choice(secondary_scenes)}. "
            f"{random.choice(LIFESTYLE_LIGHTING)}. {random.choice(LIFESTYLE_CAMERA)}. {random.choice(secondary_moods)} Natural skin texture."
        )
        # Shot 3: Context Shot
        shot3 = (
            f"{m_range} = model reference. {p_range} = {outfit_desc}. "
            f"Full-body photo: {pronoun} wearing {outfit_desc} while {random.choice(secondary_scenes)}. "
            f"Focus on the fit and fabric. {random.choice(secondary_moods)} 8K."
        )
        # Shot 4: Flat Lay
        shot4 = (
            f"Professional flat lay: {outfit_desc} styled together {random.choice(FLATLAY_SCENES)}. "
            f"{random.choice(FLATLAY_CAMERA)}. No human. Match colors exactly."
        )
        # Shot 5: Ghost Mannequin
        shot5 = (
            f"Professional e-commerce photo: {random.choice(GHOST_SCENES)} showing {outfit_desc} as a full set. "
            f"{random.choice(GHOST_LIGHTING)}. No human. High-end catalog standard."
        )
        return [shot1, shot2, shot3, shot4, shot5]


# ═══════════════════════════════════════════════════════════════
# PREVIEW — for testing prompt variety
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_model = {"id": "m1", "gender": "male", "references": ["a", "b", "c"]}
    
    print("=" * 70)
    print("SCENE DIRECTOR -- Sample Campaign (Male Model, 3 refs, 1 product)")
    print("=" * 70)
    
    prompts = build_campaign_prompts(test_model, 3, 4, 4)
    for i, p in enumerate(prompts, 1):
        print(f"\n{'-' * 60}")
        print(f"SHOT {i}:")
        print(f"{'-' * 60}")
        print(p)
    
    print("\n\n")
    
    test_model_f = {"id": "f1", "gender": "female", "references": ["a", "b", "c"]}
    print("=" * 70)
    print("SCENE DIRECTOR -- Sample Campaign (Female Model, 3 refs, 1 product)")
    print("=" * 70)
    
    prompts = build_campaign_prompts(test_model_f, 3, 4, 4)
    for i, p in enumerate(prompts, 1):
        print(f"\n{'-' * 60}")
        print(f"SHOT {i}:")
        print(f"{'-' * 60}")
        print(p)
