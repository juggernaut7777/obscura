"""
VTON Test — Elite Prompting + Auto Scene Rotation
===================================================
Uses the prompt_library to generate varied, creative content.
NEVER hardcodes garment descriptions — lets the AI see the reference images.
"""
import asyncio
import os
import sys
import random

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from flow_bridge import FlowBridge
from prompt_library import (
    CLOTHING_PROMPTS,
    SCENE_PRESETS,
    CAMERA_PRESETS,
    ANTI_AI_MEDIUM,
    build_pro_prompt,
    build_identity_block,
    MODEL_PRESETS,
    get_random_scene,
)


# ==========================================
# ELITE VTON PROMPTS — Scene Variety
# ==========================================
# These prompts NEVER describe the garment color/type.
# They say "the EXACT clothing from the product reference image"
# so the AI matches the actual uploaded photo.

VTON_SCENES = [
    # Warehouse / Industrial Shoot
    {
        "name": "warehouse",
        "prompt": (
            "High-fidelity fashion campaign photograph. The model is the EXACT person "
            "from the face and body reference images — same face, eyes, hair, skin. "
            "She is wearing the EXACT garment from the product reference image — same color, "
            "same fabric, same design, same fit. Standing in a converted industrial warehouse "
            "with exposed brick walls, concrete floor, and large steel-frame windows letting "
            "in soft diffused natural light. Vintage photography equipment visible in background. "
            "Confident editorial pose, weight shifted to one hip. Shot on Canon EOS R5 with "
            "85mm f/1.4 lens, shallow depth of field. Natural skin texture, visible pores, "
            "no AI smoothing. Raw editorial atmosphere."
        ),
    },
    # Modelling Studio (Behind the Scenes)
    {
        "name": "studio_bts",
        "prompt": (
            "Behind-the-scenes fashion lookbook shot. The model is the EXACT person from "
            "the face and body reference images. She is wearing the EXACT garment from the "
            "product reference image — matching every detail of color, cut, and fabric. "
            "Posing in a professional modelling studio with large softbox lights visible, "
            "a grey seamless paper backdrop, and a reflector stand to the side. Mid-laugh "
            "candid moment between takes. Shot on 50mm lens, natural studio lighting, "
            "authentic behind-the-scenes energy. Visible skin texture, natural flyaway hairs."
        ),
    },
    # GRWM Mirror Selfie
    {
        "name": "grwm_mirror",
        "prompt": (
            "Authentic GRWM mirror selfie. The person is the EXACT person from the face "
            "and body reference images. She is wearing the EXACT garment from the product "
            "reference image — same color, same design, same everything. Taking a full-length "
            "mirror selfie in a modern apartment hallway, phone held at chest height, relaxed "
            "natural pose. Warm overhead LED light, coat rack and shoes visible in background. "
            "Shot on iPhone 15 Pro front camera, slight grain, natural indoor lighting. "
            "Genuine smile, one hand adjusting hair. Instagram Stories aesthetic, not posed."
        ),
    },
    # Home / Couch Content
    {
        "name": "home_cozy",
        "prompt": (
            "Cozy home content creator photo. The person is the EXACT person from the face "
            "and body reference images. She is wearing the EXACT garment from the product "
            "reference image — same color, fabric, and design details. Sitting casually on "
            "a cream bouclé couch in a minimalist living room, legs tucked under, warm afternoon "
            "light from large windows. Coffee table with candles and a book nearby. Relaxed, "
            "authentic mood. Shot on iPhone, natural warm tones, visible skin texture. "
            "Content creator at home vibe, not a professional shoot."
        ),
    },
    # Fitting Room Try-On
    {
        "name": "fitting_room",
        "prompt": (
            "Authentic fitting room try-on photo. The person is the EXACT person from the face "
            "and body reference images. She is wearing the EXACT garment from the product "
            "reference image — matching every single detail. Standing in a well-lit retail "
            "fitting room, soft warm lighting, mirror showing her reflection. Shopping bags on "
            "the bench. Candid try-on haul aesthetic, checking the fit. Shot on iPhone with "
            "slight mirror distortion. Natural, authentic, like a real shopping trip."
        ),
    },
    # Coffee Shop Lifestyle
    {
        "name": "coffee_lifestyle",
        "prompt": (
            "Lifestyle content at a specialty coffee shop. The person is the EXACT person "
            "from the face and body reference images. She is wearing the EXACT garment from "
            "the product reference image — same color, same fabric, same design. Seated at "
            "a minimalist coffee shop with exposed light bulbs and wooden tables, latte in hand. "
            "Soft natural window light from the side, blurred customers in background. Candid, "
            "natural, like a friend took the photo. Shot on 35mm film aesthetic, warm tones, "
            "slight grain. Relaxed expression, mid-conversation moment."
        ),
    },
    # Editorial Studio (Dark/Moody)
    {
        "name": "dark_editorial",
        "prompt": (
            "Dramatic dark editorial fashion photograph. The model is the EXACT person from "
            "the face and body reference images. She is wearing the EXACT garment from the "
            "product reference image — same color, same cut, same material. Single dramatic "
            "side light against a dark charcoal backdrop, deep shadows, chiaroscuro lighting. "
            "Confident power pose, arms crossed or hands in pockets. Shot on Leica Q3 28mm "
            "f/1.7, high contrast, minimal fill. Visible skin texture, catchlights in eyes. "
            "Vogue editorial energy, moody and atmospheric."
        ),
    },
    # Rooftop Golden Hour
    {
        "name": "rooftop_golden",
        "prompt": (
            "Golden hour rooftop fashion photo. The model is the EXACT person from the face "
            "and body reference images. She is wearing the EXACT garment from the product "
            "reference image — every detail matching perfectly. Standing on an urban rooftop "
            "at golden hour, city skyline in the distance, warm amber light creating a rim "
            "light effect on hair and shoulders. Wind slightly catching the fabric for natural "
            "movement. Shot on Sony A7IV with 50mm f/1.2 lens, warm cinematic color grading. "
            "Natural skin glow, visible pores, authentic golden hour atmosphere."
        ),
    },
]


async def run_vton_test():
    print("=" * 50)
    print("VTON TEST - Elite Prompting + Scene Variety")
    print("=" * 50)

    bridge = FlowBridge(headless=False)
    await bridge.start()

    # Use the new worker setup
    page = await bridge._setup_page()
    bridge.page = page

    # Pick a random creative scene
    scene = random.choice(VTON_SCENES)
    print(f"\n   Selected Scene: {scene['name']}")

    images = [
        "models/character_sheets/f1_face.png",
        "models/character_sheets/f1_body.png",
        "test_products/red_hoodie.png",
    ]

    for img in images:
        status = "OK" if os.path.exists(img) else "MISSING"
        print(f"   [{status}] {img}")

    # Use the scene name for output prefix — NOT a garment description
    # This avoids hardcoding garment descriptions in the file prefix
    output_name = f"f1_{scene['name']}"

    print(f"\n   Output prefix: {output_name}")
    print(f"   Prompt preview: {scene['prompt'][:120]}...")

    results = await bridge.generate_image(
        prompt=scene["prompt"],
        reference_images=images,
        output_prefix=output_name,
        page=page,
    )

    print()
    if results:
        print(f"Done! Got {len(results)} image(s):")
        for r in results:
            print(f"  - {r}")
    else:
        print("No images captured.")

    await bridge.close()


if __name__ == "__main__":
    asyncio.run(run_vton_test())
