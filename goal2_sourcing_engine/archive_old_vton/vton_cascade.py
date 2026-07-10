"""
VTON MULTI-PROVIDER — Cascading Free-to-Cheap Pipeline
========================================================
Solves the "no free GPU" problem by cascading through multiple providers:

Priority 1: Kwai Kolors VTON (HuggingFace - FREE, dedicated GPU space)
Priority 2: FASHN.ai API (10 FREE credits on signup, then ~$0.07/image)
Priority 3: Replicate IDM-VTON (serverless, ~$0.03/run - cheapest paid)
Priority 4: Google AI Studio (our existing browser automation - FREE but no true VTON)

For graphic tees/logos, we MUST use Priority 1-3 (true garment warping).
For plain items, Priority 4 (AI generation) is fine.
"""

import os
import sys
import time
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output_ugc"
OUTPUT_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# PROVIDER 1: Kwai Kolors VTON (FREE - Dedicated HF Space)
# Unlike IDM-VTON which has no free GPU, Kolors has its own
# dedicated GPU allocation from Kwai/Kuaishou.
# ═══════════════════════════════════════════════════════════════

def try_kolors_vton(model_image: str, garment_image: str, description: str) -> str:
    """Uses Kwai-Kolors Virtual Try-On via browser automation (FREE)."""
    print("   [1/4] Trying Kwai Kolors VTON (FREE via browser)...")
    try:
        import asyncio
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto("https://kwai-kolors-kolors-virtual-try-on.hf.space", timeout=60000)
            page.wait_for_timeout(5000)
            
            # Upload person image
            person_input = page.locator("input[type='file']").first
            person_input.set_input_files(model_image)
            page.wait_for_timeout(2000)
            
            # Upload garment image (second file input)
            garment_input = page.locator("input[type='file']").nth(1)
            garment_input.set_input_files(garment_image)
            page.wait_for_timeout(2000)
            
            # Click Run/Submit button
            submit_btn = page.locator("button:has-text('Run'), button:has-text('Submit'), button.primary")
            if submit_btn.count() > 0:
                submit_btn.first.click()
            else:
                print("   [!] Could not find submit button")
                browser.close()
                return None
            
            # Wait for result (up to 90 seconds)
            print("   [*] Generating... (waiting up to 90s)")
            page.wait_for_timeout(10000)  # Initial wait
            
            # Poll for output image
            for attempt in range(16):  # 16 x 5s = 80s max
                output_img = page.locator("div.output img, img.output-image").first
                if output_img.count() > 0:
                    src = output_img.get_attribute("src")
                    if src and ("blob:" in src or "data:" in src or "http" in src):
                        # Download the result
                        import httpx
                        temp_path = str(OUTPUT_DIR / "kolors_temp_{}.png".format(int(time.time())))
                        
                        if src.startswith("http"):
                            resp = httpx.get(src, timeout=30)
                            with open(temp_path, "wb") as f:
                                f.write(resp.content)
                        else:
                            # Screenshot the output area as fallback
                            output_img.screenshot(path=temp_path)
                        
                        print("   [+] Kolors VTON SUCCESS!")
                        browser.close()
                        return temp_path
                
                page.wait_for_timeout(5000)
            
            print("   [!] Kolors timed out after 90s")
            browser.close()
            return None

    except Exception as e:
        error_msg = str(e)
        if "GPU" in error_msg or "queue" in error_msg.lower():
            print("   [!] Kolors GPU busy: {}".format(error_msg[:80]))
        else:
            print("   [!] Kolors failed: {}".format(error_msg[:80]))
        return None


# ═══════════════════════════════════════════════════════════════
# PROVIDER 2: FASHN.ai (10 FREE credits, then $0.07/image)
# Sign up at fashn.ai with Gmail - no credit card needed
# ═══════════════════════════════════════════════════════════════

def try_fashn_vton(model_image: str, garment_image: str, description: str) -> str:
    """Uses FASHN.ai API for pixel-perfect virtual try-on."""
    print("   [2/4] Trying FASHN.ai API...")

    api_key = os.environ.get("FASHN_API_KEY")
    if not api_key:
        print("   [!] FASHN_API_KEY not set. Sign up free at https://fashn.ai")
        return None

    try:
        import httpx
        import base64

        def img_to_base64(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()

        headers = {
            "Authorization": "Bearer {}".format(api_key),
            "Content-Type": "application/json",
        }

        payload = {
            "model_image": "data:image/png;base64,{}".format(img_to_base64(model_image)),
            "garment_image": "data:image/png;base64,{}".format(img_to_base64(garment_image)),
            "category": "tops",  # auto-detect would be better
        }

        response = httpx.post(
            "https://api.fashn.ai/v1/run",
            json=payload,
            headers=headers,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("output") and result["output"].get("image_url"):
            image_url = result["output"]["image_url"]
            print("   [+] FASHN.ai SUCCESS!")

            # Download the result
            img_response = httpx.get(image_url, timeout=30)
            temp_path = str(OUTPUT_DIR / "fashn_temp_{}.png".format(int(time.time())))
            with open(temp_path, "wb") as f:
                f.write(img_response.content)
            return temp_path

        print("   [!] FASHN returned unexpected result")
        return None

    except Exception as e:
        print("   [!] FASHN.ai failed: {}".format(str(e)[:80]))
        return None


# ═══════════════════════════════════════════════════════════════
# PROVIDER 3: Replicate IDM-VTON (~$0.03/run - cheapest paid)
# ═══════════════════════════════════════════════════════════════

def try_replicate_vton(model_image: str, garment_image: str, description: str) -> str:
    """Uses Replicate's serverless IDM-VTON (~$0.03 per run)."""
    print("   [3/4] Trying Replicate IDM-VTON ($0.03/run)...")

    api_key = os.environ.get("REPLICATE_API_TOKEN")
    if not api_key:
        print("   [!] REPLICATE_API_TOKEN not set.")
        return None

    try:
        import replicate

        output = replicate.run(
            "cuuupid/idm-vton:c871bb9b046c1b1c0e3068f44eb5a30f02104d1aa3c0c6e8d15a28e3a17df69d",
            input={
                "human_img": open(model_image, "rb"),
                "garm_img": open(garment_image, "rb"),
                "garment_des": description,
                "denoise_steps": 30,
                "seed": 42,
            }
        )

        if output:
            # Replicate returns a URL
            import httpx
            img_url = str(output)
            img_response = httpx.get(img_url, timeout=30)
            temp_path = str(OUTPUT_DIR / "replicate_temp_{}.png".format(int(time.time())))
            with open(temp_path, "wb") as f:
                f.write(img_response.content)
            print("   [+] Replicate SUCCESS!")
            return temp_path

        return None

    except Exception as e:
        print("   [!] Replicate failed: {}".format(str(e)[:80]))
        return None


# ═══════════════════════════════════════════════════════════════
# MASTER CASCADER — Tries each provider in order
# ═══════════════════════════════════════════════════════════════

def cascade_vton(model_image: str, garment_image: str, description: str,
                 output_name: str = None) -> str:
    """
    Cascades through all VTON providers until one succeeds.
    Returns the path to the generated image, or None.
    """
    print("\n" + "=" * 60)
    print("[VTON CASCADE] Starting pixel-perfect try-on...")
    print("   Garment: {}".format(description))
    print("=" * 60)

    # Validate inputs
    if not os.path.exists(model_image):
        print("[!] Model image not found: {}".format(model_image))
        return None
    if not os.path.exists(garment_image):
        print("[!] Garment image not found: {}".format(garment_image))
        return None

    # Try each provider in order (free first, cheap last)
    providers = [
        ("Kolors (FREE)", try_kolors_vton),
        ("FASHN.ai (10 free credits)", try_fashn_vton),
        ("Replicate ($0.03/run)", try_replicate_vton),
    ]

    for name, func in providers:
        result = func(model_image, garment_image, description)
        if result and os.path.exists(result):
            # Move to final output location
            if not output_name:
                safe = description.replace(" ", "_")[:25].lower()
                output_name = "vton_{}_{}.png".format(safe, int(time.time()))
            final_path = str(OUTPUT_DIR / output_name)
            shutil.move(result, final_path)
            print("\n[+] VTON COMPLETE via {} -> {}".format(name, final_path))
            return final_path

    print("\n[!] ALL VTON PROVIDERS FAILED. Falling back to AI generation.")
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("   VTON MULTI-PROVIDER CASCADE TEST")
    print("=" * 60)

    # Check which providers are available
    providers_status = {
        "Kolors (FREE)": "AVAILABLE (no key needed)",
        "FASHN.ai": "SET" if os.environ.get("FASHN_API_KEY") else "NOT SET (sign up free at fashn.ai)",
        "Replicate": "SET" if os.environ.get("REPLICATE_API_TOKEN") else "NOT SET",
    }
    for name, status in providers_status.items():
        print("   {} -> {}".format(name, status))

    # Test with existing assets
    model_body = str(BASE_DIR / "models" / "character_sheets" / "f5_body.png")
    garment = str(BASE_DIR / "input_sourcing" / "vintage_graphic_tee.png")

    if os.path.exists(model_body) and os.path.exists(garment):
        result = cascade_vton(model_body, garment, "Vintage washed graphic tee with metallic logo")
        if result:
            print("\n[OK] Test passed! Check: {}".format(result))
        else:
            print("\n[!] Test: All providers unavailable right now.")
    else:
        print("\n[!] Missing test files. Need model body sheet and garment image.")
