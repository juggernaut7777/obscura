import os
import sys
import json
import uuid
import random
import asyncio
from pathlib import Path

# Add directory to path to import
sys.path.insert(0, os.getcwd())

from local_generation_worker import (
    setup_browser, discover_models, discover_products,
    upload_image, get_fresh_recaptcha, generate_image,
    save_generated_images, PROMPT_TIERS
)

import httpx

async def generate_specific_tier(page, bearer, model, product_paths, prompt, tier_name):
    project_id = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "text/plain;charset=UTF-8",
        "Referer": "https://labs.google/",
        "Origin": "https://labs.google",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    }
    
    if isinstance(product_paths, str):
        product_paths = [product_paths]
        
    product_name = "_and_".join([Path(p).stem for p in product_paths])[:40]
    if model["gender"] == "male":
        prompt = prompt.replace("her ", "him ").replace("She ", "He ").replace("she ", "he ")
        
    if len(product_paths) > 1:
        prompt = prompt.replace("this EXACT garment", "these EXACT garments")
        prompt = prompt.replace("The garment", "The garments")

    print(f"\n============================================================")
    print(f"[JOB] Tier: {tier_name} | Model: {model['id']} | Product: {product_name}")
    print(f"============================================================")
    
    async with httpx.AsyncClient() as client:
        # Upload references
        face_id = await upload_image(client, model["face"], headers, project_id)
        
        body_id = None
        if tier_name != "TIER_D" and model.get("body"):
            body_id = await upload_image(client, model["body"], headers, project_id)
            
        asset_ids = [aid for aid in [face_id, body_id] if aid]
        
        for path in product_paths:
            pid = await upload_image(client, path, headers, project_id)
            if pid:
                asset_ids.append(pid)
                
        if tier_name == "TIER_D":
            # For product only flatlay, just upload the product images
            asset_ids = []
            for path in product_paths:
                pid = await upload_image(client, path, headers, project_id)
                if pid:
                    asset_ids.append(pid)
            
        # Get FRESH reCAPTCHA right before generation (they expire in ~2min)
        print("[*] Getting fresh reCAPTCHA...")
        recaptcha = await get_fresh_recaptcha(page)
        if not recaptcha:
            print("[!] No reCAPTCHA. Skipping.")
            return []

        print("[>>] Generating with GEM_PIX_2...")
        result = await generate_image(client, prompt, asset_ids, headers, project_id, recaptcha)
        
        saved = save_generated_images(result, f"{model['id']}_{tier_name}", product_name)
        print(f"[OK] Job complete! {len(saved)} images saved.")
        return saved


async def main():
    models = discover_models()
    products = discover_products()

    if not models or not products:
        print("Missing models or products.")
        return

    pw, context, page, bearer = await setup_browser()
    if not bearer:
        return

    # Choose a female model
    model = next((m for m in models if m["id"] == "f5"), models[0])

    # We need an aesthetically pleasing product
    outfit_products = [
        "c:/Users/USER/ai ugc and sales/goal2_sourcing_engine/input_sourcing/vintage_graphic_tee.png"
    ]

    try:
        # 1. Model wearing the full outfit combo (Tier B - Full body lifestyle to show pants/shoes)
        prompt_b = PROMPT_TIERS["TIER_B"][0]
        await generate_specific_tier(page, bearer, model, outfit_products, prompt_b, "TIER_B_COMBO")
        
        print("\n[WAIT] Sleeping 30s before next generation...\n")
        await asyncio.sleep(30)
        
        # 2. Product Only Flat Lay Combo (Tier D)
        prompt_d = PROMPT_TIERS["TIER_D"][0]
        await generate_specific_tier(page, bearer, model, outfit_products, prompt_d, "TIER_D_COMBO")

    finally:
        await context.close()
        await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())
