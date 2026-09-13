"""
all_in_one_bridge.py - Token Bridge + Image Generator

1. Starts HTTP server on port 9876
2. You paste a JS snippet in Chrome Console
3. Tokens flow in, image gets generated automatically

Run with: python -u all_in_one_bridge.py
"""
import sys
import json
import os
import random
import socket
import threading
import time
import uuid
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

import requests as req
from pyngrok import ngrok
from PIL import Image
import base64
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

# Force unbuffered output
os.environ["PYTHONUNBUFFERED"] = "1"

BRIDGE_PORT = 9877
PUBLIC_URL = None
TOKENS = {"bearer": None, "recaptcha": None, "user": None, "projectId": None, "authUser": "0", "action": None, "ts": 0}
TOKEN_EVENT = threading.Event()
TOKEN_NEEDED = threading.Event()  # Set when /generate needs a fresh token
REQUIRED_ACTION = "IMAGE_GENERATION"
EXTENSION_RELOAD_NEEDED = False

# Video Generation routing variables
GEN_EVENT = threading.Event()
PENDING_GEN = None
GEN_RESULT = None



def log(msg):
    tstr = time.strftime('%H:%M:%S')
    full_msg = f"[{tstr}] {msg}"
    try:
        print(full_msg, flush=True)
    except UnicodeEncodeError:
        print(full_msg.encode('ascii', 'replace').decode('ascii'), flush=True)
    with open("bridge_log.txt", "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")


_last_chrome_launch = 0

def ensure_chrome_running():
    """Auto-launching Chrome is permanently disabled to prevent duplicate windows and tab spam."""
    return False


def chrome_watchdog_loop():
    """Passive watchdog thread (auto-spawn disabled)."""
    while True:
        time.sleep(60)


# Start background watchdog thread
threading.Thread(target=chrome_watchdog_loop, daemon=True).start()


def start_tunnel():
    global PUBLIC_URL
    try:
        log("☁️ Starting Ngrok tunnel...")
        # Fix: Read production token from environment only (no hardcoded secrets)
        ngrok_token = os.getenv("NGROK_AUTH_TOKEN")
        if not ngrok_token:
            log("❌ Ngrok token is not set in NGROK_AUTH_TOKEN")
            return
        ngrok.set_auth_token(ngrok_token)
        tunnel = ngrok.connect(BRIDGE_PORT, "http")
        PUBLIC_URL = tunnel.public_url
        log(f"🚀 PUBLIC URL: {PUBLIC_URL}")
        
        # Save to file for easy VPS updating
        with open("ngrok_url.txt", "w") as f:
            f.write(PUBLIC_URL)
            
    except Exception as e:
        log(f"❌ Ngrok failed: {e}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PATCH")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_POST(self):
        log(f"INCOMING POST: {self.path}")
        if self.path == "/push":
            try:
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                data = json.loads(body)
                TOKENS["bearer"] = data.get("bearer")
                TOKENS["recaptcha"] = data.get("recaptcha")
                TOKENS["user"] = data.get("user")
                TOKENS["action"] = data.get("action")
                
                # Only update projectId if it's actually provided and valid
                new_pid = data.get("projectId")
                if new_pid and new_pid != "NOT_FOUND" and len(new_pid) > 10:
                    TOKENS["projectId"] = new_pid
                    log(f"📌 Project ID Sticky-Locked: {TOKENS['projectId']}")
                
                new_auth = data.get("authUser")
                if new_auth:
                    TOKENS["authUser"] = new_auth
                    
                now = time.time()
                TOKENS["ts"] = now
                
                # Store in action-specific sub-dictionary to prevent heartbeat overwrite
                action = data.get("action")
                if not action or action == "None" or action == "null":
                    action = REQUIRED_ACTION or "IMAGE_GENERATION"
                
                TOKENS[action] = {
                    "bearer": data.get("bearer"),
                    "recaptcha": data.get("recaptcha"),
                    "user": data.get("user"),
                    "projectId": TOKENS.get("projectId"),
                    "authUser": TOKENS.get("authUser", "0"),
                    "ts": now
                }
                site_key = data.get("siteKey")
                all_site_keys = data.get("allSiteKeys", [])
                sk_method = data.get("siteKeyMethod", "?")
                cfg_diag = data.get("cfgDiag", "?")
                log(f"DEBUG: TOKENS action='{action}' siteKey='{site_key}' method={sk_method} cfgDiag={cfg_diag} allSiteKeys={all_site_keys}")
                TOKEN_EVENT.set()
                TOKEN_NEEDED.clear()  # Extension delivered, stop asking

                # Auto-forward tokens to 24/7 VPS Bridge so cloud worker generates simultaneously
                vps_url = "https://buffoon-correct-credible.ngrok-free.dev/push"
                def _forward():
                    try:
                        req.post(vps_url, json=data, timeout=5)
                        log(f"🚀 Tokens synced to 24/7 VPS!")
                    except Exception:
                        pass
                threading.Thread(target=_forward, daemon=True).start()

                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                log(f"❌ POST ERROR: {e}")
                self.send_response(500)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(str(e).encode())
        
        elif self.path == "/generate-video-in-browser":
            global PENDING_GEN, GEN_RESULT
            try:
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                data = json.loads(body)
                prompt = data.get("prompt")
                aspect = data.get("aspectRatio")
                
                log(f"🎬 Video generation requested: prompt='{prompt}', aspect='{aspect}'")
                
                PENDING_GEN = {
                    "prompt": prompt,
                    "aspectRatio": aspect,
                    "ts": time.time()
                }
                GEN_RESULT = None
                GEN_EVENT.clear()
                
                # Wait for extension to process and push result (up to 90 seconds)
                success = GEN_EVENT.wait(timeout=90.0)
                
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                if success and GEN_RESULT:
                    log(f"✅ In-browser video generation request completed!")
                    self.wfile.write(json.dumps(GEN_RESULT).encode())
                else:
                    log(f"❌ In-browser video generation request timed out!")
                    self.wfile.write(json.dumps({"error": "generation timed out or failed in browser"}).encode())
                    
                PENDING_GEN = None
                GEN_RESULT = None
            except Exception as e:
                log(f"❌ Video generation POST error: {e}")
                self.send_response(500)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        elif self.path == "/push-generation-result":
            try:
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                data = json.loads(body)
                
                log(f"📥 Received video generation result from browser.")
                GEN_RESULT = data
                GEN_EVENT.set()
                
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                log(f"❌ push-generation-result POST error: {e}")
                self.send_response(500)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == "/ext-status":
            try:
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                data = json.loads(body.decode("utf-8", errors="replace"))
                log(f"🔌 [EXT] {data.get('msg', data)}")
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
        
        elif self.path == "/generate":
            try:
                # 1. Check if we already have a valid token (within 300s) before waiting on extension
                if not (TOKENS["bearer"] and (time.time() - TOKENS.get("ts", 0)) < 300):
                    log("🔄 Requesting fresh token from Chrome extension...")
                    TOKEN_EVENT.clear()   # Clear old signal
                    TOKEN_NEEDED.set()    # Tell extension we need a token NOW
                    
                    # Wait up to 15 seconds for the extension to deliver
                    got_token = TOKEN_EVENT.wait(timeout=15)
                    TOKEN_NEEDED.clear()
                
                if not TOKENS["bearer"]:
                    self.send_response(503)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Tokens are missing. Is Chrome open?"}')
                    return
                
                log(f"✅ Active token ready (age: {int(time.time() - TOKENS['ts'])}s)")

                # 2. Parse requested prompt
                raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                body = raw.decode("utf-8", errors="replace")
                
                # Robust JSON handling
                try:
                    data = json.loads(body, strict=False)
                except Exception:
                    # Fallback for mangled curl escapes
                    import re
                    match = re.search(r'"prompt":\s*"([^"]+)"', body)
                    p_val = match.group(1) if match else ""
                    market_match = re.search(r'"market":\s*"([^"]+)"', body)
                    m_val = market_match.group(1) if market_match else "london_uk"
                    data = {"prompt": p_val, "market": m_val}

                prompt = data.get("prompt", "")
                ref_url = data.get("reference_image_url", "")
                ref_b64 = data.get("reference_image_base64", "")
                ref_paths = data.get("ref_image_paths", [])
                aspect = data.get("aspect", "PORTRAIT_THREE_FOUR")
                if not prompt:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Missing prompt"}')
                    return

                log(f"VPS REQUESTED IMAGE: '{prompt[:40]}...'")
                if ref_paths:
                    log(f"   With {len(ref_paths)} reference image(s): {[os.path.basename(p) for p in ref_paths]}")

                # 3. Generate Image (with reference image uploads)
                result_paths = generate_image(
                    TOKENS["bearer"], TOKENS["recaptcha"], prompt, 
                    ref_url, aspect, ref_b64, 
                    ref_image_paths=ref_paths
                )

                # 4. Return Response — always send raw PNG bytes back
                if result_paths and len(result_paths) > 0:
                    # Find the actual PNG file (not webp) to return full quality
                    png_path = None
                    for rp in result_paths:
                        if rp.endswith(".png") and os.path.exists(rp):
                            png_path = rp
                            break
                    if not png_path:
                        # Fallback to whatever file we have
                        png_path = result_paths[0]
                    
                    with open(png_path, 'rb') as f:
                        img_bytes = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.end_headers()
                    self.wfile.write(img_bytes)
                    log(f"SENT {len(img_bytes)//1024}KB image back. File: {os.path.basename(png_path)}")
                else:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Generation failed"}')

            except Exception as e:
                log(f"Generate error: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        global EXTENSION_RELOAD_NEEDED, REQUIRED_ACTION
        if self.path != "/need-token":
            log(f"INCOMING GET: {self.path}")
        if self.path.startswith("/tokens"):
            req_action = "IMAGE_GENERATION"
            force_fresh = False
            if "?" in self.path:
                from urllib.parse import parse_qs, urlparse
                qs = parse_qs(urlparse(self.path).query)
                req_action = qs.get("action", ["IMAGE_GENERATION"])[0]
                force_fresh = qs.get("force", ["false"])[0].lower() == "true"
                
            is_valid = False
            # Google session tokens are valid for up to 1 hour; allow up to 1800s (30m) cache
            if TOKENS["bearer"] and (time.time() - TOKENS["ts"]) < 1800:
                is_valid = True
            else:
                action_data = TOKENS.get(req_action)
                if isinstance(action_data, dict):
                    bearer = action_data.get("bearer")
                    ts = action_data.get("ts", 0)
                    if bearer and (time.time() - ts) < 1800:
                        is_valid = True

                
            if not is_valid:
                log(f"🔄 Tokens requested for action '{req_action}' (force={force_fresh}) but stale/missing/forced. Signaling Chrome extension to push...")
                REQUIRED_ACTION = req_action
                TOKEN_NEEDED.set()
                ensure_chrome_running()
                self.send_response(503)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "stale or no tokens"}).encode())
                return
            
            # Fetch data from the matching action dictionary if present, else fallback to global TOKENS
            action_data = TOKENS.get(req_action)
            if isinstance(action_data, dict) and action_data.get("bearer"):
                resp_bearer = action_data["bearer"]
                resp_recaptcha = action_data["recaptcha"]
                resp_user = action_data["user"]
                resp_pid = action_data.get("projectId") or TOKENS.get("projectId")
                resp_age = int(time.time() - action_data["ts"])
            else:
                resp_bearer = TOKENS["bearer"]
                resp_recaptcha = TOKENS["recaptcha"]
                resp_user = TOKENS["user"]
                resp_pid = TOKENS["projectId"]
                resp_age = int(time.time() - TOKENS["ts"])

            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "bearer": resp_bearer,
                "recaptcha": resp_recaptcha,
                "user": resp_user,
                "projectId": resp_pid,
                "action": req_action,
                "age_seconds": resp_age,
            }).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "ready": bool(TOKENS["bearer"])}).encode())
        elif self.path == "/reload-extension":
            EXTENSION_RELOAD_NEEDED = True
            log("🔄 Extension reload requested by developer.")
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
        elif self.path == "/need-token":
            if EXTENSION_RELOAD_NEEDED:
                EXTENSION_RELOAD_NEEDED = False
                log("🔄 Signaling Chrome extension to reload...")
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"need": True, "action": "RELOAD"}).encode())
                return
            
            # Extension polls this every 1.5s to know when to generate a fresh token
            need = TOKEN_NEEDED.is_set()
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "need": need,
                "action": REQUIRED_ACTION,
                "pendingGeneration": PENDING_GEN
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()


def download_reference_image(url):
    """Download a reference image and return base64-encoded data + mime type."""
    try:
        resp = req.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.status_code != 200:
            log(f"   ⚠️ Reference download failed: {resp.status_code}")
            return None, None
        
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        if "jpeg" in content_type or "jpg" in content_type:
            mime = "image/jpeg"
        elif "png" in content_type:
            mime = "image/png"
        elif "webp" in content_type:
            mime = "image/webp"
        else:
            mime = "image/jpeg"
        
        b64 = base64.b64encode(resp.content).decode("utf-8")
        log(f"   ✅ Reference image downloaded: {len(resp.content)//1024}KB ({mime})")
        return b64, mime
    except Exception as e:
        log(f"   ⚠️ Reference download error: {e}")
        return None, None


ASPECT_MAP = {
    "PORTRAIT_THREE_FOUR": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
    "LANDSCAPE_FOUR_THREE": "IMAGE_ASPECT_RATIO_LANDSCAPE_FOUR_THREE",
    "SQUARE": "IMAGE_ASPECT_RATIO_SQUARE",
    "PORTRAIT_NINE_SIXTEEN": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
    "LANDSCAPE_SIXTEEN_NINE": "IMAGE_ASPECT_RATIO_LANDSCAPE_SIXTEEN_NINE",
    "9:16": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
    "3:4": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
    "1:1": "IMAGE_ASPECT_RATIO_SQUARE",
    "16:9": "IMAGE_ASPECT_RATIO_LANDSCAPE_SIXTEEN_NINE",
}

UPLOAD_URL = "https://aisandbox-pa.googleapis.com/v1/flow/uploadImage"


def upload_reference_image(image_path, bearer, pid):
    """Upload a reference image to Flow and get back a UUID asset ID."""
    log(f"   [UPLOAD] {os.path.basename(image_path)}...")
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "clientContext": {"projectId": pid, "tool": "PINHOLE"},
        "imageBytes": img_b64
    }
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": "https://labs.google",
        "Referer": "https://labs.google/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    try:
        resp = req.post(UPLOAD_URL, headers=headers, data=json.dumps(payload), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        asset_id = data.get("media", {}).get("name")
        if asset_id:
            log(f"   [UPLOAD OK] {os.path.basename(image_path)} -> {asset_id[:25]}...")
        else:
            log(f"   [UPLOAD WARN] Unexpected response: {str(data)[:150]}")
        return asset_id
    except Exception as e:
        log(f"   [UPLOAD FAIL] {e}")
        return None


def generate_image(bearer, recaptcha, prompt, reference_url="", aspect="PORTRAIT_THREE_FOUR", reference_b64="", ref_image_paths=None):
    """Generate an image with optional reference images (model + product).
    
    ref_image_paths: list of local file paths to upload as references.
                     e.g. [model_face.png, model_body.png, product.png]
    """
    pid = TOKENS.get("projectId")
    if not pid:
        log("ERROR: No Project ID captured yet! Run the snippet in Chrome.")
        return None
        
    ctx = {
        "projectId": pid, "tool": "PINHOLE",
        "sessionId": ";" + str(int(time.time() * 1000)),
        "recaptchaContext": {"token": recaptcha, "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"},
    }
    
    # --- UPLOAD REFERENCE IMAGES (model + product) ---
    image_inputs = []
    if ref_image_paths:
        log(f"   [REF] Uploading {len(ref_image_paths)} reference image(s)...")
        for img_path in ref_image_paths:
            if img_path and os.path.exists(img_path):
                asset_id = upload_reference_image(img_path, bearer, pid)
                if asset_id:
                    image_inputs.append({
                        "imageInputType": "IMAGE_INPUT_TYPE_REFERENCE",
                        "name": asset_id
                    })
        log(f"   [REF] {len(image_inputs)} reference(s) uploaded successfully.")
    
    prompt_parts = [{"text": prompt}]
    aspect_value = ASPECT_MAP.get(aspect, "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR")
    
    # Build request - include imageInputs only if we have references
    requests_list = []
    for _ in range(4):
        req_obj = {
            "clientContext": ctx, 
            "imageModelName": "GEM_PIX_2",
            "imageAspectRatio": aspect_value,
            "structuredPrompt": {"parts": prompt_parts},
            "seed": random.randint(0, 999999),
        }
        if image_inputs:
            req_obj["imageInputs"] = image_inputs
        requests_list.append(req_obj)
    
    payload = {
        "clientContext": ctx,
        "mediaGenerationContext": {"batchId": str(uuid.uuid4())},
        "useNewMedia": True,
        "requests": requests_list,
    }
    url = f"https://aisandbox-pa.googleapis.com/v1/projects/{pid}/flowMedia:batchGenerateImages"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "text/plain;charset=UTF-8",
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Origin": "https://labs.google",
        "Referer": "https://labs.google/",
        "X-Goog-Api-Client": "gl-js/1.53.0",
        "X-Goog-AuthUser": TOKENS.get("authUser", "0"),
        "X-Requested-With": "XMLHttpRequest"
    }
    
    log(f"   Using Token: {bearer[:15]}... (PID: {pid}, Refs: {len(image_inputs)})")
    
    # --- ACCOUNT PROTECTION SYSTEM ---
    if not hasattr(generate_image, '_consecutive_403s'):
        generate_image._consecutive_403s = 0
    
    if generate_image._consecutive_403s >= 3:
        log("EMERGENCY BRAKE: 3 consecutive 403s detected. Cooling down 30 min...")
        time.sleep(1800)
        generate_image._consecutive_403s = 0
        log("Cooldown complete. Resuming...")
    
    # Human simulation delay
    pre_delay = random.uniform(2.0, 5.0)
    log(f"   Human-sim delay: {pre_delay:.1f}s before API call...")
    time.sleep(pre_delay)
    
    # --- SMART RETRY ---
    max_retries = 3
    resp = None
    for attempt in range(1, max_retries + 1):
        current_bearer = TOKENS.get("bearer", bearer)
        current_rc = TOKENS.get("recaptcha", recaptcha)
        headers["Authorization"] = f"Bearer {current_bearer}"
        ctx["recaptchaContext"]["token"] = current_rc
        
        log(f"Calling Flow API (attempt {attempt}/{max_retries}, 180s timeout)...")
        resp = req.post(url, headers=headers, data=json.dumps(payload), timeout=180)
        log(f"API Response: {resp.status_code}")
        
        if resp.status_code == 200:
            generate_image._consecutive_403s = 0
            break
        
        if resp.status_code == 403:
            generate_image._consecutive_403s += 1
            if generate_image._consecutive_403s >= 3:
                log("EMERGENCY: 3 consecutive 403s. Aborting.")
                log(f"ERROR: {resp.text[:300]}")
                return None
            if attempt < max_retries:
                base_wait = 90 * attempt
                jitter = random.uniform(-15, 30)
                wait_secs = base_wait + jitter
                log(f"reCAPTCHA cooldown. Waiting {wait_secs:.0f}s...")
                time.sleep(wait_secs)
                log("Requesting fresh token before retry...")
                TOKEN_NEEDED.set()
                TOKEN_EVENT.clear()
                TOKEN_EVENT.wait(timeout=30)
                continue
        
        log(f"ERROR: {resp.text[:300]}")
        return None
    
    if not resp or resp.status_code != 200:
        return None
    
    data = resp.json()
    media = data.get("media", [])
    log(f"Got {len(media)} image(s)")
    
    os.makedirs("output", exist_ok=True)
    saved = []
    # Only save the FIRST image (1 per API call)
    for i, m in enumerate(media[:1]):
        fife = m.get("fifeUrl") or m.get("image", {}).get("generatedImage", {}).get("fifeUrl") or m.get("fileUrl", "")
        if fife:
            if "googleusercontent.com" in fife:
                fife = fife.split("=")[0] + "=s2048"
            img = req.get(fife, timeout=30)
            local_fp = os.path.join("output", f"bridge_gen_{int(time.time())}_{i+1}.png")
            with open(local_fp, "wb") as f:
                f.write(img.content)
            log(f"SAVED: {local_fp} ({len(img.content)//1024}KB)")
            saved.append(local_fp)
        else:
            log(f"No URL found. Keys: {list(m.keys())}")
    return saved


def compress_to_webp(local_path, quality=85):
    """Converts PNG to optimized WebP to save mobile data."""
    try:
        webp_path = local_path.replace(".png", ".webp")
        with Image.open(local_path) as img:
            img.save(webp_path, "WEBP", quality=quality)
        return webp_path
    except Exception as e:
        log(f"Compression Error: {e}")
        return None


def upload_to_vps(local_path):
    """Securely uploads the file to the VPS and returns the remote path."""
    vps_ip = "34.75.179.135"
    vps_user = "USER"
    ssh_key = os.path.expanduser("~/.ssh/google_compute_engine")
    remote_dir = "/home/USER/ai-ugc/output/generated"
    
    filename = os.path.basename(local_path)
    remote_path = f"{remote_dir}/{filename}"
    
    # Use Windows built-in scp for speed and simplicity
    scp_cmd = [
        "scp", "-i", ssh_key, 
        "-o", "StrictHostKeyChecking=no",
        local_path, f"{vps_user}@{vps_ip}:{remote_path}"
    ]
    
    try:
        subprocess.run(scp_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return remote_path
    except Exception as e:
        log(f"SCP Error: {e}")
        return None


def main():
    log("=" * 50)
    log("FLOW TOKEN BRIDGE + IMAGE GENERATOR")
    log("=" * 50)

    # Check port is free
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("localhost", BRIDGE_PORT))
    sock.close()
    if result == 0:
        log(f"ERROR: Port {BRIDGE_PORT} is already in use!")
        log("Kill the other process first, then retry.")
        sys.exit(1)

    # Start Tunnel in a separate thread so it doesn't block local server startup
    threading.Thread(target=start_tunnel, daemon=True).start()

    # Multi-threaded server so /generate can block while /need-token + /push still work
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    server = ThreadedHTTPServer(("0.0.0.0", BRIDGE_PORT), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    log(f"Server started on port {BRIDGE_PORT}")
    log("")
    log("PASTE THIS IN CHROME CONSOLE (on a Flow project page):")
    log("-" * 50)
    site_key = os.environ.get("RECAPTCHA_SITE_KEY")
    if not site_key:
        log("WARNING: RECAPTCHA_SITE_KEY environment variable is not set. Falling back to empty string, which may cause failures.")
        site_key = ""

    snippet = f"""(async function() {{
    const pid = window.location.href.match(/([a-f0-9]{{8}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{12}})/i)?.[1] || "NOT_FOUND";
    const auth = await (await fetch('/fx/api/auth/session', {{credentials:'include'}})).json();
    const rc = await grecaptcha.enterprise.execute('{site_key}', {{action:'IMAGE_GENERATION'}});
    await fetch('http://localhost:9877/push', {{method:'POST', headers:{{'Content-Type':'application/json'}},
        body: JSON.stringify({{bearer: auth.access_token, recaptcha: rc, user: auth.user?.name, projectId: pid}})}});
    console.log('Tokens pushed for Project: ' + pid);
}})();"""
    print(snippet, flush=True)
    log("-" * 50)
    log("")
    log("Server is running in 24/7 PERSISTENT MODE.")
    log("Waiting for VPS requests on Port 9877...")
    log("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Stopped.")

if __name__ == "__main__":
    main()
