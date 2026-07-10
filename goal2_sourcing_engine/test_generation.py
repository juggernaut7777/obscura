import asyncio
import json
import logging
from generation_router import GenerationRouter

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def test_generation():
    with open("smart_merge_plan.json", "r") as f:
        plan = json.load(f)
        
    prompt = plan.get("full_fit_prompt")
    indices = plan.get("selected_indices", [])
    
    if not prompt:
        logging.error("No prompt found.")
        return

    # 1. Get ALL products used during the design phase (SORTED)
    import os, glob
    input_dir = "input_sourcing"
    product_images = sorted(glob.glob(os.path.join(input_dir, "*.png")))
    
    # 2. Build the exact Reference List: [Face, Body, Prod1, Prod2...]
    model_face = r"C:\Users\USER\.gemini\antigravity\brain\83a89fde-ace2-4259-9b25-28e931d346cb\official_male_face_sheet_1777644321778.png"
    model_body = r"C:\Users\USER\.gemini\antigravity\brain\83a89fde-ace2-4259-9b25-28e931d346cb\official_male_body_sheet_1777644429422.png"
    
    ref_paths = [model_face, model_body]
    for idx in indices:
        if idx < len(product_images):
            ref_paths.append(product_images[idx])

    logging.info(f"🚀 Sending Technical Merge to Bridge...")
    logging.info(f"PROMPT: {prompt}")
    logging.info(f"REFERENCES ({len(ref_paths)}): {[os.path.basename(p) for p in ref_paths]}")
    
    try:
        router = GenerationRouter()
        result = await router.generate_image(
            prompt=prompt, 
            ref_image_paths=ref_paths, 
            aspect="3:4"
        )
        
        if result:
            logging.info(f"✅ SUCCESS! Image saved to: {result}")
        else:
            logging.error("❌ FAILED: Received None. Check bridge logs.")
            
    except Exception as e:
        logging.error(f"❌ Error during generation test: {e}")

if __name__ == "__main__":
    asyncio.run(test_generation())
