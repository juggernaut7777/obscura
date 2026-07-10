import asyncio
import os
import sys

# Configure UTF-8 safe prints
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from generation_router import GenerationRouter

async def main():
    print("=" * 60)
    print("         TESTING DIRECT FLOW API ROUTING")
    print("=" * 60)
    
    router = GenerationRouter()
    
    # Test 1: Simple text generation (no reference images)
    prompt = "Fashion editorial shot, a futuristic glass handbag resting on a sleek dark marble table, neon lighting highlights, 8k resolution, photorealistic"
    print("\n[*] Starting Test 1: Text-only generation...")
    
    try:
        results = await router.generate_image(
            prompt=prompt,
            ref_image_paths=[],
            aspect="1:1",
            output_prefix="test_direct_text",
            force_engine="flow" # Force Flow engine to bypass G-Labs and test the new API integration directly
        )
        print(f"\n[+] Test 1 Result: {results}")
    except Exception as e:
        print(f"\n[!] Test 1 Failed with exception: {e}")

    # Test 2: Multi-reference generation (Try-on style)
    # Check if we have character sheet and product mockups
    ref_paths = [
        "models/character_sheets/f1_1.png",
        "test_products/red_hoodie.png"
    ]
    
    # Filter to existing files
    valid_refs = [p for p in ref_paths if os.path.exists(p)]
    
    if len(valid_refs) == 2:
        print("\n[*] Starting Test 2: Multi-reference outfit try-on generation...")
        vton_prompt = (
            "High-fidelity fashion editorial. A woman wearing the EXACT clothing from the product "
            "reference image. Streetwear style, urban brick background, natural lighting, 8k resolution, realistic."
        )
        try:
            results2 = await router.generate_image(
                prompt=vton_prompt,
                ref_image_paths=valid_refs,
                aspect="3:4",
                output_prefix="test_direct_vton",
                force_engine="flow"
            )
            print(f"\n[+] Test 2 Result: {results2}")
        except Exception as e:
            print(f"\n[!] Test 2 Failed with exception: {e}")
    else:
        print(f"\n[!] Skipping Test 2. Missing test reference files (Found {len(valid_refs)} of 2).")
        print("    Please ensure you have generated models and products if you want to test VTON.")

if __name__ == "__main__":
    asyncio.run(main())
