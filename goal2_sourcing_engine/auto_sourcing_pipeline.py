"""
Fully Autonomous Sourcing Pipeline
==================================
This script watches an input folder for raw supplier images (e.g. Yupoo/Weidian).
It automatically pairs them with an AI model and runs them through the elite
prompting system to generate luxury UGC, without any manual data entry.
"""

import asyncio
import os
import sys
import glob
import random

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from flow_bridge import FlowBridge

# Import our new Elite Prompts
from test_playwright_vton import VTON_SCENES
from prompt_library import SHOE_PROMPTS, CLOTHING_PROMPTS

INPUT_DIR = "input_sourcing"
OUTPUT_DIR = "output_ugc"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define our model roster
MODELS = {
    "f1": {
        "face": "models/character_sheets/f1_face.png",
        "body": "models/character_sheets/f1_body.png"
    }
}

def get_product_type(filename: str) -> str:
    """Basic categorization for context-aware styling."""
    name = filename.lower()
    if "shoe" in name or "sneaker" in name or "jordan" in name or "asics" in name:
        return "shoe"
    if "puffer" in name or "jacket" in name or "coat" in name or "winter" in name:
        return "winter_clothing"
    return "clothing"

async def run_pipeline():
    print("=" * 60)
    print(" 🚀 FULLY AUTONOMOUS SOURCING PIPELINE (ELITE 2026 EDITION) ")
    print("=" * 60)

    # 1. Scan the input folder
    raw_products = glob.glob(os.path.join(INPUT_DIR, "*.*"))
    raw_products = [p for p in raw_products if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # 1.5 Scan for "Outfit Grids" (multiple items in a subfolder)
    outfit_grid_dir = os.path.join(INPUT_DIR, "outfit_grid")
    outfit_items = []
    if os.path.exists(outfit_grid_dir):
        outfit_items = glob.glob(os.path.join(outfit_grid_dir, "*.*"))
        outfit_items = [p for p in outfit_items if p.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not raw_products and not outfit_items:
        print(f"\n[!] No raw products found in '{INPUT_DIR}' or '{outfit_grid_dir}'.")
        print("    Please drop images into that folder.")
        return

    print(f"\n[+] Found {len(raw_products)} single products and {len(outfit_items)} outfit grid items.\n")

    # 2. Build the jobs automatically
    jobs = []
    
    # Handle single items
    for product_path in raw_products:
        filename = os.path.basename(product_path)
        base_name = os.path.splitext(filename)[0]
        
        # Decide if it's a shoe, winter clothing, or standard clothing
        product_type = get_product_type(base_name)
        
        if product_type == "shoe":
            # Pick a luxury flat lay / shoe flex prompt
            prompt_key = random.choice(list(SHOE_PROMPTS.keys()))
            prompt_text = SHOE_PROMPTS[prompt_key]
            refs = [product_path] 
            output_prefix = f"ugc_shoe_{base_name}_{prompt_key}"
            
        elif product_type == "winter_clothing":
            # Context-Aware: Put heavy jackets in the snow mountain scene
            prompt_text = CLOTHING_PROMPTS.get("snow_mountain", "standing in the snow...")
            refs = [MODELS["f1"]["face"], MODELS["f1"]["body"], product_path]
            output_prefix = f"ugc_f1_{base_name}_snow_mountain"
            
        else:
            # Pick an elite human scene (warehouse, grwm, etc.)
            scene = random.choice(VTON_SCENES)
            prompt_text = scene["prompt"]
            refs = [MODELS["f1"]["face"], MODELS["f1"]["body"], product_path]
            output_prefix = f"ugc_f1_{base_name}_{scene['name']}"

        jobs.append({
            "prompt": prompt_text,
            "reference_images": refs,
            "output_prefix": output_prefix
        })

    # Handle Outfit Grids (Fit Checks)
    if outfit_items:
        # Generate two flat lays: Bed and Floor
        for grid_type in ["bed_fit_check", "floor_fit_check"]:
            jobs.append({
                "prompt": CLOTHING_PROMPTS.get(grid_type, f"A premium flat lay outfit grid on the {grid_type}"),
                "reference_images": outfit_items, # Pass ALL items as references
                "output_prefix": f"ugc_outfit_grid_{grid_type}"
            })

    # 3. Spin up the bridge and process the batch
    bridge = FlowBridge(headless=False)
    await bridge.start()

    print(f"[*] Starting Batch Execution for {len(jobs)} items...")
    
    # Run the batch using max_workers (parallel execution)
    results = await bridge.generate_batch(jobs)

    print("\n" + "=" * 60)
    print(f" 🏁 PIPELINE COMPLETE: {len(results)} elite images generated ")
    print("=" * 60)
    
    for r in results:
        print(f"  ✅ {r}")

    await bridge.close()

if __name__ == "__main__":
    asyncio.run(run_pipeline())
