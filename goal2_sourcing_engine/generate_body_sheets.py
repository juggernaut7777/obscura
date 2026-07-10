"""
BODY SHEET GENERATOR
=====================
Generates full-body reference images for models that only have face shots.
Uses the same Flow API pipeline to create consistent body references.

Missing: f5, f6, m2, m3, m4
"""

import os
import sys
import json
import base64
import uuid
import random
import asyncio
import traceback
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models" / "character_sheets"

# Models that need body sheets
MISSING_BODIES = {
    "f5": {"face": MODELS_DIR / "f5_face.png", "gender": "female"},
    "f6": {"face": MODELS_DIR / "f6_face.png", "gender": "female"},
    "m2": {"face": MODELS_DIR / "m2_face.png", "gender": "male"},
    "m3": {"face": MODELS_DIR / "m3_face.png", "gender": "male"},
    "m4": {"face": MODELS_DIR / "m4_face.png", "gender": "male"},
}

UPLOAD_URL = "https://aisandbox-pa.googleapis.com/v1/flow/uploadImage"

BODY_PROMPT_FEMALE = (
    "Using this EXACT person from the reference image, generate a hyperrealistic "
    "full-body character reference photo. She stands in a relaxed neutral pose, "
    "arms slightly away from body, facing directly toward camera. She is wearing "
    "plain white form-fitting t-shirt and dark blue straight-leg jeans. Simple white "
    "sneakers. Clean white studio background with soft even lighting. "
    "CRITICAL: Her face, skin tone, hair color, hair texture, and facial features "
    "must be IDENTICAL to the reference image. Full body from head to feet visible. "
    "No props, no accessories. This is a character reference sheet for consistent "
    "AI generation. Shot on 50mm lens, even studio lighting, no shadows."
)

BODY_PROMPT_MALE = (
    "Using this EXACT person from the reference image, generate a hyperrealistic "
    "full-body character reference photo. He stands in a relaxed neutral pose, "
    "arms slightly away from body, facing directly toward camera. He is wearing "
    "a plain white crew neck t-shirt and dark blue straight-leg jeans. Simple white "
    "sneakers. Clean white studio background with soft even lighting. "
    "CRITICAL: His face, skin tone, hair color, hair style, and facial features "
    "must be IDENTICAL to the reference image. Full body from head to feet visible. "
    "No props, no accessories. This is a character reference sheet for consistent "
    "AI generation. Shot on 50mm lens, even studio lighting, no shadows."
)


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[{}] {}".format(timestamp, msg)
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode())


async def setup_browser():
    from playwright.async_api import async_playwright

    profile_dir = os.path.abspath("playwright_profile")
    captured_bearer = {"token": None}

    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        channel="chrome",
    )
    page = await context.new_page()

    def on_request(request):
        url = request.url
        if "aisandbox-pa.googleapis.com" in url or "labs.google" in url:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer ya29.") and not captured_bearer["token"]:
                captured_bearer["token"] = auth_header.replace("Bearer ", "")
                log("[+] Captured ya29 Bearer token!")

    page.on("request", on_request)

    await page.goto(
        "https://labs.google/fx/tools/flow",
        wait_until="networkidle",
        timeout=60000
    )

    if not captured_bearer["token"]:
        await page.wait_for_timeout(5000)

    if not captured_bearer["token"]:
        bearer_fallback = await page.evaluate("""async () => {
            try {
                const req = await fetch('/fx/api/auth/session', {credentials:'include'});
                if (!req.ok) return null;
                const auth = await req.json();
                return auth.access_token;
            } catch { return null; }
        }""")
        if bearer_fallback:
            captured_bearer["token"] = bearer_fallback

    bearer = captured_bearer["token"]
    if not bearer:
        log("[!] FATAL: Could not get Bearer token.")
        await context.close()
        await pw.stop()
        return None, None, None, None

    log("[+] Bearer ready!")
    return pw, context, page, bearer


async def get_fresh_recaptcha(page):
    try:
        recaptcha = await page.evaluate("""async () => {
            try {
                if (typeof grecaptcha !== 'undefined' && grecaptcha.enterprise) {
                    return await grecaptcha.enterprise.execute(
                        '6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV',
                        {action: 'IMAGE_GENERATION'}
                    );
                }
                return null;
            } catch { return null; }
        }""")
        return recaptcha
    except Exception as e:
        log("[!] reCAPTCHA error: {}".format(e))
        return None


async def generate_body_sheet(page, bearer, model_id, model_info):
    import httpx

    project_id = str(uuid.uuid4())
    headers = {
        "Authorization": "Bearer {}".format(bearer),
        "Content-Type": "text/plain;charset=UTF-8",
        "Referer": "https://labs.google/",
        "Origin": "https://labs.google",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    }

    prompt = BODY_PROMPT_FEMALE if model_info["gender"] == "female" else BODY_PROMPT_MALE

    log("")
    log("=" * 50)
    log("[BODY] Generating body sheet for: {}".format(model_id))
    log("=" * 50)

    async with httpx.AsyncClient() as client:
        try:
            # Upload face reference
            log("  [^] Uploading face: {}".format(model_info["face"].name))
            with open(model_info["face"], "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')

            payload = {
                "clientContext": {"projectId": project_id, "tool": "PINHOLE"},
                "imageBytes": img_b64
            }
            response = await client.post(UPLOAD_URL, headers=headers,
                                         content=json.dumps(payload), timeout=60.0)
            response.raise_for_status()
            face_id = response.json().get("media", {}).get("name")
            log("  [OK] Face uploaded: {}...".format(face_id[:20]))

            # Get fresh reCAPTCHA
            recaptcha = await get_fresh_recaptcha(page)
            if not recaptcha:
                log("[!] No reCAPTCHA. Skipping.")
                return None

            # Generate body sheet
            generate_url = "https://aisandbox-pa.googleapis.com/v1/projects/{}/flowMedia:batchGenerateImages".format(project_id)

            gen_payload = {
                "clientContext": {
                    "recaptchaContext": {
                        "token": recaptcha,
                        "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
                    },
                    "projectId": project_id,
                    "tool": "PINHOLE"
                },
                "mediaGenerationContext": {"batchId": str(uuid.uuid4())},
                "useNewMedia": True,
                "requests": [{
                    "clientContext": {
                        "recaptchaContext": {
                            "token": recaptcha,
                            "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
                        },
                        "projectId": project_id,
                        "tool": "PINHOLE"
                    },
                    "imageModelName": "GEM_PIX_2",
                    "imageAspectRatio": "IMAGE_ASPECT_RATIO_PORTRAIT",
                    "structuredPrompt": {"parts": [{"text": prompt}]},
                    "seed": random.randint(1, 2147483647),
                    "imageInputs": [
                        {"imageInputType": "IMAGE_INPUT_TYPE_REFERENCE", "name": face_id}
                    ]
                }]
            }

            log("[>>] Generating body sheet...")
            response = await client.post(generate_url, headers=headers,
                                         content=json.dumps(gen_payload), timeout=120.0)
            response.raise_for_status()
            result = response.json()

            # Download and save
            media_list = result.get("media", [])
            for media_item in media_list:
                fife_url = media_item.get("image", {}).get("generatedImage", {}).get("fifeUrl", "")
                if fife_url:
                    img_response = client.get(fife_url, timeout=60.0)
                    # Use sync client for download
                    with httpx.Client() as dl:
                        img_response = dl.get(fife_url, timeout=60.0)
                        img_response.raise_for_status()
                        save_path = MODELS_DIR / "{}_body.png".format(model_id)
                        with open(save_path, "wb") as f:
                            f.write(img_response.content)
                        log("[SAVED] {} ({} KB)".format(save_path.name, len(img_response.content) // 1024))
                        return str(save_path)

            log("[!] No image in response for {}".format(model_id))
            return None

        except Exception as e:
            log("[!] Error generating body for {}: {}".format(model_id, e))
            traceback.print_exc()
            return None


async def main():
    log("=" * 50)
    log("BODY SHEET GENERATOR")
    log("Generating body refs for: {}".format(list(MISSING_BODIES.keys())))
    log("=" * 50)

    # Filter to only models that actually need bodies
    to_generate = {}
    for model_id, info in MISSING_BODIES.items():
        body_path = MODELS_DIR / "{}_body.png".format(model_id)
        if not body_path.exists():
            to_generate[model_id] = info
        else:
            log("[SKIP] {} already has body sheet".format(model_id))

    if not to_generate:
        log("[+] All models already have body sheets!")
        return

    # Setup browser
    pw, context, page, bearer = await setup_browser()
    if not bearer:
        return

    generated = 0
    try:
        for model_id, info in to_generate.items():
            result = await generate_body_sheet(page, bearer, model_id, info)
            if result:
                generated += 1
            # Small delay between generations
            await asyncio.sleep(10)
    finally:
        log("[*] Done! Generated {}/{} body sheets.".format(generated, len(to_generate)))
        await context.close()
        await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
