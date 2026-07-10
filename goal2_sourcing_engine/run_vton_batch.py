"""
VTON Batch Generator — Fully Autonomous
========================================
Runs multiple VTON generations back-to-back with zero manual intervention.
Each job auto-creates a new Flow project, uploads images, attaches them,
types the prompt, generates, and saves the result.
"""
import asyncio
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from flow_bridge import FlowBridge

async def run_batch():
    print("=" * 50)
    print("  FULLY AUTONOMOUS VTON BATCH GENERATOR")
    print("=" * 50)

    bridge = FlowBridge(headless=False)
    await bridge.start()

    # ──────────────────────────────────────────────
    # Define your batch jobs here.
    # Each job = one generated image.
    # ──────────────────────────────────────────────
    jobs = [
        {
            "prompt": (
                "High-fidelity fashion editorial. The character is a woman with hazel eyes "
                "and shoulder-length wavy dark hair, matching the face and body reference "
                "images exactly. She is wearing the EXACT clothing from the product reference "
                "image. Streetwear style, urban background, natural lighting, 8k resolution, "
                "realistic skin texture."
            ),
            "reference_images": [
                "models/character_sheets/f1_1.png",
                "test_products/red_hoodie.png",
            ],
            "output_prefix": "f1_red_hoodie",
        },
        # ── Add more jobs below ──
        # {
        #     "prompt": "Same woman wearing a black leather jacket...",
        #     "reference_images": [
        #         "models/character_sheets/f1_face.png",
        #         "models/character_sheets/f1_body.png",
        #         "test_products/black_jacket.png",
        #     ],
        #     "output_prefix": "f1_black_jacket",
        # },
    ]

    # Verify images exist
    for job in jobs:
        for img in job.get("reference_images", []):
            status = "OK" if os.path.exists(img) else "MISSING"
            print(f"   [{status}] {img}")

    results = await bridge.generate_batch(jobs)

    print()
    print("=" * 50)
    print(f"  BATCH COMPLETE: {len(results)} image(s) generated")
    print("=" * 50)
    for r in results:
        print(f"  - {r}")

    await bridge.close()

asyncio.run(run_batch())
