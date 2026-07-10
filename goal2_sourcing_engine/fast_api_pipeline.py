"""
⚡ GOLDEN API PIPELINE (Headless & Fast)
=========================================
Bypasses the UI entirely using pure HTTP requests to Google's internal APIs.
10x faster than Playwright. No DOM piercing. No flakiness.

HOW TO USE:
1. Copy the latest Bearer Token and reCAPTCHA Token from the Sniffer Extension.
2. Paste them into your .env file or below.
3. Run this script.
"""

import os
import sys
import json
import base64
import uuid
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

# The tokens captured by sniffer.js
AUTH_BEARER = os.getenv("FLOW_BEARER_TOKEN", "ya29.YOUR_BEARER_TOKEN_HERE")
RECAPTCHA_TOKEN = os.getenv("FLOW_RECAPTCHA_TOKEN", "0cAFcWe...YOUR_TOKEN_HERE")

# API Endpoints discovered via SPY
PROJECT_ID = str(uuid.uuid4())
UPLOAD_URL = "https://aisandbox-pa.googleapis.com/v1/flow/uploadImage"
GENERATE_URL = f"https://aisandbox-pa.googleapis.com/v1/projects/{PROJECT_ID}/flowMedia:batchGenerateImages"

HEADERS = {
    "Authorization": f"Bearer {AUTH_BEARER}",
    "Content-Type": "application/json",
}

async def upload_image_to_flow(client: httpx.AsyncClient, image_path: str) -> str:
    """Uploads a local image to Google's backend and returns the asset UUID."""
    print(f"[*] Uploading {image_path} via API...")
    
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
        
    payload = {
        "clientContext": {
            "projectId": PROJECT_ID,
            "tool": "PINHOLE"
        },
        "imageBytes": img_b64
    }
    
    response = await client.post(UPLOAD_URL, headers=HEADERS, json=payload, timeout=60.0)
    response.raise_for_status()
    
    data = response.json()
    # The API returns {"media": {"name": "uuid", ...}}
    asset_id = data.get("media", {}).get("name")
    
    if not asset_id:
        print(f"  [!] Warning: Could not find 'media.name' in response: {str(data)[:200]}")
        
    print(f"  [+] Upload successful! Asset ID: {asset_id}")
    return asset_id

async def generate_ugc_api(client: httpx.AsyncClient, prompt: str, asset_ids: list):
    """Sends the actual generation request instantly."""
    print(f"\n[*] Sending Generation Request (Model: GEM_PIX_2)...")
    
    # Format the image references exactly as we found in spy_payload.json
    image_inputs = [
        {"imageInputType": "IMAGE_INPUT_TYPE_REFERENCE", "name": asset_id}
        for asset_id in asset_ids
    ]
    
    payload = {
        "clientContext": {
            "recaptchaContext": {
                "token": RECAPTCHA_TOKEN
            }
        },
        "mediaGenerationContext": {
            "batchId": str(uuid.uuid4())
        },
        "useNewMedia": True,
        "requests": [
            {
                "imageModelName": "GEM_PIX_2",
                "imageAspectRatio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
                "structuredPrompt": {
                    "parts": [{"text": prompt}]
                },
                "seed": int.from_bytes(os.urandom(4), 'big'), # Random seed
                "imageInputs": image_inputs
            }
        ]
    }
    
    response = await client.post(GENERATE_URL, headers=HEADERS, json=payload, timeout=120.0)
    response.raise_for_status()
    
    print("  [+] Generation request accepted! Images are rendering...")
    # NOTE: Flow returns a long-running operation ID here, or streams the images.
    return response.json()

from playwright.async_api import async_playwright
import traceback

async def get_fresh_tokens() -> tuple[str, str]:
    """Briefly spins up Playwright to extract fresh auth and recaptcha tokens."""
    print("\n[+] Spinning up Headless Chrome to extract fresh API tokens...")
    profile_dir = os.path.abspath("playwright_profile")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            channel="chrome",
        )
        page = await context.new_page()
        
        # Go to Flow to load the auth context
        await page.goto("https://labs.google/fx/tools/flow", wait_until="domcontentloaded", timeout=60000)
        
        print("  [*] Extracting Bearer Token...")
        try:
            bearer = await page.evaluate("""async () => {
                const req = await fetch('/fx/api/auth/session', {credentials:'include'});
                if (!req.ok) return null;
                const auth = await req.json();
                return auth.access_token;
            }""")
        except Exception as e:
            print(f"  [!] Failed to get bearer: {e}")
            bearer = None

        print("  [*] Extracting reCAPTCHA Enterprise Token...")
        try:
            recaptcha = await page.evaluate("""async () => {
                if (typeof grecaptcha !== 'undefined' && grecaptcha.enterprise) {
                    return await grecaptcha.enterprise.execute('6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV', {action: 'IMAGE_GENERATION'});
                }
                return null;
            }""")
        except Exception as e:
            print(f"  [!] Failed to get recaptcha: {e}")
            recaptcha = None
            
        await context.close()
        
        if not bearer or not recaptcha:
            print("[!] FATAL: Could not extract tokens. Ensure you are logged into Google Labs in the Playwright profile.")
            return None, None
            
        print("  [+] Tokens extracted successfully!\n")
        return bearer, recaptcha

async def run_fast_api():
    print("=" * 50)
    print(" [FAST API] GOLDEN PIPELINE ACTIVE")
    print("=" * 50)
    
    # 1. Automatically grab fresh tokens
    bearer, recaptcha = await get_fresh_tokens()
    if not bearer: return
    
    global AUTH_BEARER, RECAPTCHA_TOKEN, HEADERS
    AUTH_BEARER = bearer
    RECAPTCHA_TOKEN = recaptcha
    HEADERS["Authorization"] = f"Bearer {AUTH_BEARER}"
    
    async with httpx.AsyncClient() as client:
        # Example Workflow
        try:
            face_id = await upload_image_to_flow(client, "models/character_sheets/f1_face.png")
            body_id = await upload_image_to_flow(client, "models/character_sheets/f1_body.png")
            hoodie_id = await upload_image_to_flow(client, "input_sourcing/red_hoodie.png")
            
            prompt = (
                "Authentic GRWM mirror selfie. The person is the EXACT person from the face and body "
                "reference images. She is wearing the EXACT garment from the product reference image "
                "— same color, same design. Shot on iPhone 15 Pro, slight grain."
            )
            
            result = await generate_ugc_api(client, prompt, [face_id, body_id, hoodie_id])
            print("\nAPI Response:")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"\n[!] API Error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_fast_api())
