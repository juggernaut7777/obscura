import asyncio
import os
import json
import glob
from generation_router import GenerationRouter

async def generate_full_fit():
    print("Starting Generation for Smart Merge / Full Fit...")
    
    # 1. Load the plan
    plan_path = "smart_merge_plan.json"
    if not os.path.exists(plan_path):
        print("[!] No plan found. Run test_smart_merge.py first.")
        return
        
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
        
    print(f"[*] Loaded plan: {plan.get('fit_name', 'Outfit')}")
    
    # 2. Get the reference images
    input_dir = "input_sourcing"
    product_images = glob.glob(os.path.join(input_dir, "*.png"))
    model_img_path = r"C:\Users\USER\.gemini\antigravity\brain\83a89fde-ace2-4259-9b25-28e931d346cb\m1_face_raw_1777633179487.png"
    
    ref_images_on_model = [model_img_path] + product_images
    ref_images_flat_lay = product_images # No model for flat lay
    
    # 3. Setup output directory (Review Pending)
    output_dir = os.path.join("review_pending", "full_fit_test")
    os.makedirs(output_dir, exist_ok=True)
    
    router = GenerationRouter()
    
    # Define the shots we want to generate from the plan
    shots = [
        {"name": "front_hero", "prompt": plan.get('full_fit_prompt', ''), "refs": ref_images_on_model, "aspect": "3:4"},
        {"name": "flat_lay", "prompt": plan.get('flat_lay_prompt', ''), "refs": ref_images_flat_lay, "aspect": "1:1"}
    ]
    
    # Also grab back_prompt and lifestyle_prompt if they exist in the raw response
    # (Since I only explicitly printed front and flat lay in the test script, 
    # but asked Gemini for all 4 in the director prompt).
    raw_text = plan.get('_raw', '')
    if "back_prompt" in plan:
        shots.append({"name": "back_detail", "prompt": plan['back_prompt'], "refs": ref_images_on_model, "aspect": "3:4"})
    if "lifestyle_prompt" in plan:
        shots.append({"name": "lifestyle", "prompt": plan['lifestyle_prompt'], "refs": ref_images_on_model, "aspect": "3:4"})
        
    print(f"[*] Preparing to generate {len(shots)} shots...")
    
    for shot in shots:
        if not shot["prompt"]:
            print(f"[!] Skipping {shot['name']}, no prompt found.")
            continue
            
        print(f"\n Generating {shot['name']}...")
        print(f"   Prompt: {shot['prompt'][:100]}...")
        
        try:
            images = await router.generate_image(
                prompt=shot["prompt"],
                ref_image_paths=shot["refs"],
                output_prefix=f"full_fit_{shot['name']}",
                aspect=shot["aspect"],
            )
            
            if images and len(images) > 0:
                src_path = images[0]
                filename = os.path.basename(src_path)
                dest_path = os.path.join(output_dir, filename)
                
                # Copy to pending folder
                import shutil
                shutil.copy2(src_path, dest_path)
                print(f"   [+] Saved to {dest_path}")
            else:
                print(f"   [!] Generation failed for {shot['name']}")
                
        except Exception as e:
            print(f"   [!] Error generating {shot['name']}: {e}")
            
    print("\n[+] Full Fit Generation Complete! Check review_pending/full_fit_test/")

if __name__ == "__main__":
    asyncio.run(generate_full_fit())
