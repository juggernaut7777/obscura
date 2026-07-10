"""
Test: Can the Flow API accept inline base64 images in the prompt payload?
=========================================================================
If this works, we skip Playwright entirely and run VTON at API speed.
"""
import os
import sys
import json
import time
import base64
import random
import uuid
import requests as req

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BRIDGE_URL = "http://127.0.0.1:9877"

def get_tokens():
    """Get fresh tokens from our running bridge."""
    try:
        r = req.get(f"{BRIDGE_URL}/tokens", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"   Bearer token age: {data.get('age_seconds', '?')}s")
            return data["bearer"], data["recaptcha"]
    except:
        pass
    return None, None

def image_to_base64(path):
    """Convert an image file to base64 string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def test_inline_image(bearer, recaptcha, prompt, image_paths):
    """Try sending images as inline base64 data in the prompt parts."""
    pid = "340fd8e5-c7b8-4b36-b388-cc7964cf2999"
    ctx = {
        "projectId": pid, "tool": "PINHOLE",
        "sessionId": ";" + str(int(time.time() * 1000)),
        "recaptchaContext": {"token": recaptcha, "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"},
    }

    # Build multimodal parts array: text + images
    parts = [{"text": prompt}]
    for img_path in image_paths:
        if os.path.exists(img_path):
            ext = os.path.splitext(img_path)[1].lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            b64 = image_to_base64(img_path)
            parts.append({"inlineData": {"mimeType": mime, "data": b64}})
            print(f"   Added image: {os.path.basename(img_path)} ({len(b64)//1024}KB base64)")

    payload = {
        "clientContext": ctx,
        "mediaGenerationContext": {"batchId": str(uuid.uuid4())},
        "useNewMedia": True,
        "requests": [{
            "clientContext": ctx,
            "imageModelName": "GEM_PIX_2",
            "imageAspectRatio": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
            "structuredPrompt": {"parts": parts},
            "seed": random.randint(0, 999999),
        }],
    }

    url = f"https://aisandbox-pa.googleapis.com/v1/projects/{pid}/flowMedia:batchGenerateImages"
    headers = {"Authorization": f"Bearer {bearer}", "Content-Type": "text/plain;charset=UTF-8"}

    print(f"\n   Sending to API ({len(json.dumps(payload))//1024}KB payload)...")
    resp = req.post(url, headers=headers, data=json.dumps(payload), timeout=180)
    print(f"   Response: {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        media = data.get("media", [])
        print(f"   GOT {len(media)} IMAGE(S)!")

        os.makedirs("output/vton_api_test", exist_ok=True)
        for i, m in enumerate(media):
            fife = m.get("fifeUrl") or m.get("image", {}).get("generatedImage", {}).get("fifeUrl") or m.get("fileUrl", "")
            if fife:
                img = req.get(fife, timeout=30)
                path = f"output/vton_api_test/api_vton_{int(time.time())}_{i+1}.png"
                with open(path, "wb") as f:
                    f.write(img.content)
                print(f"   SAVED: {path} ({len(img.content)//1024}KB)")
        return True
    else:
        print(f"   FAILED: {resp.text[:500]}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("INLINE IMAGE API TEST")
    print("=" * 50)

    # Step 1: Get tokens from running bridge
    print("\n1. Getting tokens from bridge...")
    bearer, recaptcha = get_tokens()
    if not bearer:
        print("   Bridge is not running or tokens are stale!")
        print("   Start the bridge first: python all_in_one_bridge.py")
        print("   Then push tokens from Chrome console.")
        sys.exit(1)
    print("   Tokens acquired!")

    # Step 2: Test with our model + product
    print("\n2. Testing inline image generation...")
    prompt = (
        "Using this exact person from the reference images, generate a "
        "hyperrealistic full-body OOTD photo of her wearing this exact hoodie. "
        "The face and body must match the references EXACTLY. "
        "Golden hour, urban sidewalk, shot on 85mm lens at f/1.8, "
        "natural skin texture, streetwear editorial, RAW photo style."
    )

    images = [
        "models/character_sheets/f1_face.png",
        "models/character_sheets/f1_body.png",
        "test_products/black_hoodie.jpg",
    ]

    success = test_inline_image(bearer, recaptcha, prompt, images)

    if success:
        print("\n=== IT WORKS! The API accepts inline images! ===")
        print("This means we can run VTON at full API speed from the VPS!")
    else:
        print("\n=== API rejected inline images. ===")
        print("We'll need to use a different approach.")
