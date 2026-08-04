import os
import json
import asyncio
import aiohttp

BRIDGE_URL = "http://localhost:9877"
OUTPUT_DIR = os.path.join(os.getcwd(), "models", "character_sheets")

# High-end photography parameters for maximum realism (based on 2026 Higgsfield/Flux best practices for skin texture)
PHOTO_TECH = "ultra-high resolution, hyper-realistic skin texture, visible pores and micro-texture, natural fine lines and skin imperfections, peach fuzz, unretouched, soft diffused cinematic lighting, subtle subsurface scattering, shot on 85mm macro lens, shallow depth of field, 8k, photorealistic, cinematic film grain. (CRITICAL: Do NOT use smooth skin, plastic, waxy, airbrushed, CGI, AI glow, beauty filter, or over-processed looks)."

def _save_local_file(img_path, dest):
    if os.path.exists(img_path):
        import shutil
        shutil.copy2(img_path, dest)
        print(f"   ✅ Saved locally to: {dest}")
        return True
    return False

def _download_from_vps(img_path, dest):
    import subprocess
    dest_webp = dest.replace(".png", ".webp")
    cmd = [
        "scp",
        "-i", "C:/Users/USER/.ssh/google_compute_engine",
        "-o", "StrictHostKeyChecking=no",
        f"USER@34.75.179.135:{img_path}",
        dest_webp
    ]
    subprocess.run(cmd, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(dest_webp):
        print(f"   ✅ Downloaded and saved to: {dest_webp}")
        return True
    else:
        print(f"   ❌ Failed to download from VPS.")
        return False

# Define the 10 models with their specific descriptions
MODELS = {
    # WOMEN
    "f1": "A beautiful confident mixed-ethnicity young woman early 20s, warm brown skin, natural curly dark hair, brown eyes, defined cheekbones, athletic toned build.",
    "f2": "A stunning elegant East Asian young woman mid 20s, porcelain skin, straight glossy black hair past shoulders, almond eyes, delicate features, slim graceful build.",
    "f3": "A striking White European young woman early 20s, edgy high-fashion editorial look, pale skin, sharp angular jawline, short blonde bob hair, intense piercing blue eyes, very tall and very thin high-fashion build.",
    "f4": "A gorgeous Latina young woman mid 20s, warm olive skin, thick wavy dark brown hair, soft warm smile, curvy and voluptuous hourglass build.",
    "f5": "An elegant South Asian young woman mid 20s, rich brown skin, long luxurious dark hair, large expressive dark eyes, graceful and tall slim build.",
    "f6": "A bold striking Black young woman mid 20s, dark skin, short cropped natural hair, strong cheekbones, intense confident expression, full lips, strong athletic build.",
    "f7": "A striking East Asian young woman early 20s, raw streetwear aesthetic, unretouched skin, short blunt black bob haircut, intense cold editorial stare, extremely slim and tall high-fashion build.",
    
    # MEN
    "m1": "A handsome athletic Black young man early 20s, dark skin, short fade haircut, strong jawline, confident expression, muscular athletic build.",
    "m2": "A handsome clean-cut White European young man mid 20s, fair skin, styled medium-length brown hair, approachable warm smile, lean and fit build.",
    "m3": "A striking Middle Eastern young man late 20s, olive skin, thick dark hair, perfectly groomed dark beard, strong masculine jawline, tall and broad-shouldered luxury model build.",
    "m4": "A handsome East Asian young man early 20s, smooth skin, trendy textured black hair with a middle part, youthful and relaxed expression, very slim streetwear-style build.",
    "m5": "A rugged Chinese young man mid 20s, edgy avant-garde streetwear aesthetic, natural skin with subtle imperfections, slightly messy mid-length hair, sharp jawline, lean architectural build."
}

async def generate_sheet(session, model_id, prompt, suffix):
    print(f"\n🎨 Generating {model_id} {suffix} sheet...")
    try:
        async with session.post(
            f"{BRIDGE_URL}/generate",
            json={"prompt": prompt},
            timeout=aiohttp.ClientTimeout(total=240)
        ) as r:
            if r.status == 200:
                data = await r.json()
                if data.get("images"):
                    # Use run_in_executor for makedirs too to avoid any blocking IO
                    await asyncio.to_thread(os.makedirs, OUTPUT_DIR, exist_ok=True)
                    for img_path in data["images"]:
                        dest = os.path.join(OUTPUT_DIR, f"{model_id}_{suffix}.png")

                        saved_local = await asyncio.to_thread(_save_local_file, img_path, dest)
                        if not saved_local:
                            # Bridge uploaded it to VPS and deleted local. Download it back.
                            print(f"   ☁️  Downloading from VPS: {img_path}")
                            await asyncio.to_thread(_download_from_vps, img_path, dest)
                        return True
            else:
                text = await r.text()
                print(f"   ❌ Bridge Error: {r.status} - {text}")
    except Exception as e:
        print(f"   ❌ Request Failed: {e}")
    return False

async def main():
    print("==================================================")
    print("🤖 NANO BANANA PRO - 10 MODEL CHARACTER SHEET GENERATOR")
    print("==================================================")
    
    # Optional: We could just do the 4 most critical ones first so it doesn't take 30 minutes
    # We'll run through the complete roster of 10 models
    target_models = list(MODELS.keys())
    
    async with aiohttp.ClientSession() as session:
        for model_id in target_models:
            desc = MODELS[model_id]

            # 1. FACE SHEET
            face_prompt = f"Professional character reference sheet, 3 face views arranged side by side horizontally on a pure white background. {desc} LEFT VIEW: Front-facing headshot looking at camera. CENTER VIEW: Three-quarter angle headshot turned slightly right. RIGHT VIEW: Side profile headshot. The exact SAME person in all three views. {PHOTO_TECH}"

            # 2. BODY SHEET
            # We specify plain underwear/sports attire to ensure the clothes don't block the body shape
            gender = "man" if model_id.startswith("m") else "woman"
            attire = "plain black fitted t-shirt and black shorts" if gender == "man" else "plain black sports bra and black bike shorts"

            body_prompt = f"Professional character reference sheet, 3 full-body views arranged side by side horizontally on a pure white background. {desc} Wearing {attire} to show body proportions clearly. LEFT VIEW: Front-facing full body standing straight. CENTER VIEW: Side profile full body. RIGHT VIEW: Back view full body. The exact SAME person with identical height, weight, and build in all three views. {PHOTO_TECH}"
            
            # Generate them concurrently
            success_face, success_body = await asyncio.gather(
                generate_sheet(session, model_id, face_prompt, "face"),
                generate_sheet(session, model_id, body_prompt, "body"),
                return_exceptions=True
            )

            print("-" * 50)
            print("⏳ Waiting 25 seconds to prevent reCAPTCHA 'Unusual Activity' bans...")
            await asyncio.sleep(25)

if __name__ == "__main__":
    asyncio.run(main())
