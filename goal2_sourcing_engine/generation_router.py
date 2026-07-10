import os
import sys
import time
import base64
import random
import asyncio
import requests
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from glabs_client import GLabsClient
from voice_generator import VoiceGenerator
from video_bridge import VideoBridge
from meta_ai_video_worker import MetaAIVideoWorker
from video_api_client import VideoAPIClient

def safe_print(msg: str):
    """Safely print messages on Windows to avoid UnicodeEncodeErrors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding, errors='replace'))
        except Exception:
            print("[Print Error] Unable to encode output print message.")

def path_to_base64(path: str) -> str:
    """Convert local image file to base64 data URI."""
    if not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    elif ext not in ("png", "jpeg", "webp"):
        ext = "png"
    
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f"data:image/{ext};base64,{encoded}"
    except Exception as e:
        safe_print(f"[!] Router: Base64 encoding error for {path}: {e}")
        return ""

class GenerationRouter:
    """
    Routes generation requests to G-Labs local server, standard Stealth Bridge (localhost:9877),
    Kling AI browser automation, or Meta AI video automation.
    Muxes output videos with synthesized voice narration to compile complete UGC reels.
    """
    
    def __init__(self):
        self.dest_dir = os.path.join(os.getcwd(), "output", "generated")
        self.ugc_dir = os.path.join(os.getcwd(), "output_ugc")
        os.makedirs(self.dest_dir, exist_ok=True)
        os.makedirs(self.ugc_dir, exist_ok=True)
        
        self.glabs = GLabsClient()
        self.voice_gen = VoiceGenerator()
        self.video_api = VideoAPIClient()

        # Provider health cooldown memory
        self.provider_cooldowns = {}  # key: provider_name, value: timestamp when cooldown ends
        self.cooldown_duration = 300  # 5 minutes cooldown
        self.video_bridge = None

    def _is_provider_healthy(self, name: str, force: bool = False) -> bool:
        """Check if a provider is healthy (not currently on cooldown)."""
        if force:
            return True
        cooldown_until = self.provider_cooldowns.get(name, 0)
        if time.time() < cooldown_until:
            remaining = int(cooldown_until - time.time())
            safe_print(f"  [-] Router: Provider '{name}' is on cooldown for another {remaining}s. Skipping.")
            return False
        return True

    def _mark_provider_failed(self, name: str):
        """Mark a provider as failed, putting it on cooldown."""
        self.provider_cooldowns[name] = time.time() + self.cooldown_duration
        safe_print(f"  [!] Router: Provider '{name}' failed. Cooldown set for {self.cooldown_duration}s.")

    def _mark_provider_success(self, name: str):
        """Clear cooldown for a successful provider call."""
        if name in self.provider_cooldowns:
            del self.provider_cooldowns[name]

    def _validate_video(self, video_path: str) -> bool:
        """
        Validate that the generated video file exists, has size > 0,
        and is not corrupt (checks container, duration, and resolution using ffprobe).
        """
        if not video_path or not os.path.exists(video_path):
            safe_print(f"  [!] Video Validation: File does not exist: {video_path}")
            return False
            
        if os.path.getsize(video_path) == 0:
            safe_print(f"  [!] Video Validation: File size is 0 bytes: {video_path}")
            return False
            
        import subprocess
        import json
        
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-select_streams", "v:0", 
            "-show_entries", "stream=width,height,duration", 
            "-of", "json", 
            video_path
        ]
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                startupinfo=startupinfo,
                timeout=10
            )
            if result.returncode != 0:
                safe_print(f"  [!] Video Validation: ffprobe check failed for {video_path}. Return code: {result.returncode}. Error: {result.stderr}")
                return False
                
            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            if not streams:
                safe_print(f"  [!] Video Validation: No video streams found in {video_path}")
                return False
                
            stream = streams[0]
            width = stream.get("width")
            height = stream.get("height")
            duration = stream.get("duration")
            
            if not width or not height:
                safe_print(f"  [!] Video Validation: Invalid resolution: {width}x{height}")
                return False
                
            if duration is not None:
                try:
                    dur_float = float(duration)
                    if dur_float <= 0.0:
                        safe_print(f"  [!] Video Validation: Video duration is <= 0: {dur_float}")
                        return False
                except ValueError:
                    safe_print(f"  [!] Video Validation: Could not parse duration value '{duration}'")
                    return False
                    
            safe_print(f"  [+] Video Validation: Passed! Resolution: {width}x{height}, Duration: {duration}s")
            return True
        except subprocess.TimeoutExpired:
            safe_print(f"  [!] Video Validation: ffprobe timeout expired for {video_path}")
            return False
        except Exception as e:
            safe_print(f"  [!] Video Validation: Exception running ffprobe: {e}")
            safe_print(f"  [!] Video Validation: Falling back to file existence and size check.")
            return os.path.exists(video_path) and os.path.getsize(video_path) > 1000

    async def _get_video_bridge(self) -> VideoBridge:
        """Lazily initialize and start a persistent VideoBridge browser context."""
        if self.video_bridge is None:
            safe_print("[*] Router: Starting persistent VideoBridge browser context...")
            self.video_bridge = VideoBridge(headless=True)
            await self.video_bridge.start()
        return self.video_bridge

    async def close(self):
        """Cleans up resources, such as closing the persistent VideoBridge browser context."""
        if self.video_bridge is not None:
            safe_print("[*] Router: Stopping persistent VideoBridge browser context...")
            try:
                await self.video_bridge.stop()
            except Exception as e:
                safe_print(f"[!] Router: Error stopping VideoBridge: {e}")
            self.video_bridge = None

    async def _get_fresh_flow_tokens(self, action: str = "IMAGE_GENERATION") -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Spins up Playwright headlessly to extract fresh auth, recaptcha, project ID, and authUser tokens."""
        # 1. Try to fetch tokens from the active local bridge first (highest trust reCAPTCHA score)
        import httpx
        safe_print(f"[*] Router: Querying local token bridge for trusted session tokens (Action: {action})...")
        for attempt in range(1, 16):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"http://127.0.0.1:9877/tokens?action={action}&force=true", timeout=3.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        bearer = data.get("bearer")
                        recaptcha = data.get("recaptcha")
                        project_id = data.get("projectId")
                        auth_user = data.get("authUser", "0")
                        if bearer and recaptcha:
                            safe_print(f"  [+] Router: Retrieved active tokens from local token bridge (Port 9877) for {action}!")
                            return bearer, recaptcha, project_id, auth_user
                    elif resp.status_code == 503:
                        safe_print(f"  [*] Router: Bridge active but tokens stale. Requested fresh token (attempt {attempt}/15). Waiting 2s...")
                    else:
                        safe_print(f"  [!] Router: Bridge returned unexpected status {resp.status_code}.")
            except Exception:
                # Bridge not running, bypass loop immediately
                safe_print("  [*] Router: Local token bridge is offline.")
                break
            await asyncio.sleep(2.0)

        return None, None, None, None

    async def _upload_image_to_flow_api(self, client, bearer: str, project_id: str, image_path: str, auth_user: str = "0") -> Optional[str]:
        """Uploads a local image to Google's backend directly via HTTP and returns the asset ID."""
        if not os.path.exists(image_path):
            safe_print(f"  [!] Router: Reference image does not exist: {image_path}")
            return None
            
        safe_print(f"[*] Router: Uploading {os.path.basename(image_path)} via HTTP API...")
        
        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
                
            payload = {
                "clientContext": {
                    "projectId": project_id,
                    "tool": "PINHOLE"
                },
                "imageBytes": img_b64
            }
            
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "text/plain;charset=UTF-8",
                "Origin": "https://labs.google",
                "Referer": "https://labs.google/",
                "X-Goog-Api-Client": "gl-js/1.53.0",
                "X-Goog-AuthUser": auth_user,
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "*/*"
            }
            
            UPLOAD_URL = "https://aisandbox-pa.googleapis.com/v1/flow/uploadImage"
            response = await client.post(UPLOAD_URL, headers=headers, content=json.dumps(payload), timeout=60.0)
            if response.status_code != 200:
                safe_print(f"  [!] Router: Upload API failed with status {response.status_code}. Response: {response.text[:500]}")
            response.raise_for_status()
            
            data = response.json()
            asset_id = data.get("media", {}).get("name")
            if asset_id:
                safe_print(f"  [+] Router: Upload successful! Asset ID: {asset_id[:25]}...")
            else:
                safe_print(f"  [!] Router: No asset ID returned: {data}")
            return asset_id
        except Exception as e:
            safe_print(f"  [!] Router: Upload HTTP error: {e}")
            return None

    async def _generate_flow_api(self, client, bearer: str, recaptcha: str, project_id: str, prompt: str, asset_ids: list, aspect: str, auth_user: str = "0") -> List[str]:
        """Submits the generation request directly via HTTP API and downloads the result."""
        safe_print(f"[*] Router: Sending Generation Request directly via HTTP (Model: GEM_PIX_2)...")
        
        aspect_map = {
            "9:16": "IMAGE_ASPECT_RATIO_PORTRAIT",
            "16:9": "IMAGE_ASPECT_RATIO_LANDSCAPE",
            "3:4": "IMAGE_ASPECT_RATIO_PORTRAIT_THREE_FOUR",
            "4:3": "IMAGE_ASPECT_RATIO_LANDSCAPE_FOUR_THREE",
            "1:1": "IMAGE_ASPECT_RATIO_SQUARE",
        }
        aspect_value = aspect_map.get(aspect, "IMAGE_ASPECT_RATIO_PORTRAIT")
        
        image_inputs = [
            {"imageInputType": "IMAGE_INPUT_TYPE_REFERENCE", "name": asset_id}
            for asset_id in asset_ids if asset_id
        ]
        
        import uuid
        import random
        ctx = {
            "projectId": project_id,
            "tool": "PINHOLE",
            "sessionId": ";" + str(int(time.time() * 1000)),
            "recaptchaContext": {
                "token": recaptcha,
                "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
            }
        }
        
        request_obj = {
            "clientContext": ctx,
            "imageModelName": "GEM_PIX_2",
            "imageAspectRatio": aspect_value,
            "structuredPrompt": {
                "parts": [{"text": prompt}]
            },
            "seed": random.randint(0, 999999)
        }
        if image_inputs:
            request_obj["imageInputs"] = image_inputs
            
        payload = {
            "clientContext": ctx,
            "mediaGenerationContext": {
                "batchId": str(uuid.uuid4())
            },
            "useNewMedia": True,
            "requests": [request_obj]
        }
        
        GENERATE_URL = f"https://aisandbox-pa.googleapis.com/v1/projects/{project_id}/flowMedia:batchGenerateImages"
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "text/plain;charset=UTF-8",
            "Origin": "https://labs.google",
            "Referer": "https://labs.google/",
            "X-Goog-Api-Client": "gl-js/1.53.0",
            "X-Goog-AuthUser": auth_user,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*"
        }
        
        try:
            response = await client.post(GENERATE_URL, headers=headers, content=json.dumps(payload), timeout=120.0)
            if response.status_code != 200:
                safe_print(f"  [!] Router: Generation API failed with status {response.status_code}. Response: {response.text[:500]}")
            response.raise_for_status()
            
            data = response.json()
            media = data.get("media", [])
            safe_print(f"  [+] Router: Generation request accepted! Got {len(media)} media entries.")
            
            saved_paths = []
            for i, m in enumerate(media):
                fife = m.get("fifeUrl") or m.get("image", {}).get("generatedImage", {}).get("fifeUrl") or m.get("fileUrl", "")
                if fife:
                    if "googleusercontent.com" in fife:
                        fife = fife.split("=")[0] + "=s2048"
                    
                    safe_print(f"[*] Router: Downloading generated image from {fife[:60]}...")
                    img_resp = await client.get(fife, timeout=30.0)
                    img_resp.raise_for_status()
                    
                    filepath = os.path.join(self.dest_dir, f"direct_flow_{int(time.time())}_{i+1}.png")
                    with open(filepath, "wb") as f:
                        f.write(img_resp.content)
                    safe_print(f"  [OK] Saved -> {os.path.basename(filepath)}")
                    saved_paths.append(filepath)
            return saved_paths
        except Exception as e:
            safe_print(f"  [!] Router: Generation HTTP error: {e}")
            return []

    async def _generate_flow_video_api(self, 
                                      client, 
                                      bearer: str, 
                                      recaptcha: str, 
                                      project_id: str, 
                                      prompt: str, 
                                      asset_ids: list, 
                                      aspect: str, 
                                      auth_user: str = "0",
                                      action: str = "VIDEO_GENERATION") -> List[str]:
        """Submits Veo video generation to Direct Flow HTTP API and polls for completion."""
        safe_print(f"[*] Router: Sending Video Generation Request directly via HTTP...")
        
        # Endpoints
        endpoint = "https://aisandbox-pa.googleapis.com/v1/video:batchAsyncGenerateVideoText"
            
        aspect_map = {
            "16:9": "VIDEO_ASPECT_RATIO_LANDSCAPE",
            "9:16": "VIDEO_ASPECT_RATIO_PORTRAIT",
        }
        aspect_value = aspect_map.get(aspect, "VIDEO_ASPECT_RATIO_PORTRAIT")
        
        import uuid
        import random
        
        first_asset = asset_ids[0] if (asset_ids and len(asset_ids) > 0 and asset_ids[0]) else None
        
        request_obj = {
            "aspectRatio": aspect_value,
            "videoModelKey": "veo_3_1_i2v_lite" if first_asset else "veo_3_1_t2v_lite",
            "seed": random.randint(0, 999999),
            "metadata": {}
        }
        
        request_obj["textInput"] = {
            "structuredPrompt": {
                "parts": [{"text": prompt}]
            }
        }
        
        if first_asset:
            safe_print(f"  [+] Router: Image-to-Video mode enabled using reference asset: {first_asset}")
            request_obj["textInput"]["structuredPrompt"]["parts"].append({
                "reference": {
                    "media": {
                        "mediaId": first_asset
                    }
                }
            })
        
        payload = {
            "mediaGenerationContext": {
                "batchId": str(uuid.uuid4()),
                "audioFailurePreference": "BLOCK_SILENCED_VIDEOS"
            },
            "clientContext": {
                "projectId": project_id,
                "tool": "PINHOLE",
                "userPaygateTier": "PAYGATE_TIER_ONE",
                "sessionId": ";" + str(int(time.time() * 1000)),
                "recaptchaContext": {
                    "token": recaptcha,
                    "applicationType": "RECAPTCHA_APPLICATION_TYPE_WEB"
                }
            },
            "requests": [request_obj],
            "useV2ModelConfig": True
        }
        
        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "text/plain;charset=UTF-8",
            "Referer": "https://labs.google/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }
        
        try:
            safe_print(f"[*] Router: Posting request to {endpoint}...")
            response = await client.post(endpoint, headers=headers, content=json.dumps(payload), timeout=60.0)
            if response.status_code != 200:
                safe_print(f"  [!] Router: Video generation submit failed with status {response.status_code}. Response: {response.text[:500]}")
                response.raise_for_status()
                
            op_data = response.json()
            media = op_data.get("media", [])
            if not media:
                safe_print(f"  [!] Router: No media items returned in response: {op_data}")
                return []
            media_name = media[0].get("name")
            safe_print(f"  [+] Router: Video generation submitted. Media Name: {media_name}. Polling...")
            
            # Helper to find URLs recursively
            def _find_urls(data, search_str="googleusercontent.com"):
                urls_found = []
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, str) and (search_str in v or ".mp4" in v or "flow-content.google" in v):
                            urls_found.append(v)
                        else:
                            urls_found.extend(_find_urls(v, search_str))
                elif isinstance(data, list):
                    for item in data:
                        urls_found.extend(_find_urls(item, search_str))
                return urls_found
                
            # Phase 2: Poll for completion status
            poll_url = "https://aisandbox-pa.googleapis.com/v1/video:batchCheckAsyncVideoGenerationStatus"
            poll_payload = {
                "media": [
                    {
                        "name": media_name,
                        "projectId": project_id
                    }
                ]
            }
            start_poll = time.time()
            timeout_limit = 360 # 6 minutes
            
            while time.time() - start_poll < timeout_limit:
                await asyncio.sleep(8)
                elapsed = int(time.time() - start_poll)
                safe_print(f"  [*] Router: Polling video status ({elapsed}s elapsed)...")
                
                try:
                    poll_resp = await client.post(poll_url, headers=headers, content=json.dumps(poll_payload), timeout=30.0)
                    if poll_resp.status_code != 200:
                        safe_print(f"    [!] Poll HTTP error {poll_resp.status_code}. Retrying...")
                        continue
                        
                    status_data = poll_resp.json()
                    media_list = status_data.get("media", [])
                    if media_list:
                        m_item = media_list[0]
                        gen_status = m_item.get("mediaMetadata", {}).get("mediaStatus", {}).get("mediaGenerationStatus", "")
                        
                        if gen_status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                            if m_item.get("error") or status_data.get("error"):
                                safe_print(f"    [!] Video generation completed with error: {m_item.get('error') or status_data.get('error')}")
                                return []
                            
                            safe_print(f"    [+] Video generation completed successfully! Fetching video data (Phase 3)...")
                            
                            # Phase 3: Fetch the actual video via GET v1/media/{media_name}
                            # The status endpoint does NOT return download URLs for videos.
                            # Instead, GET v1/media/{name} returns the video as base64 in video.encodedVideo.
                            media_fetch_url = f"https://aisandbox-pa.googleapis.com/v1/media/{media_name}"
                            safe_print(f"[*] Router: GET {media_fetch_url[:70]}...")
                            
                            media_resp = await client.get(media_fetch_url, headers=headers, timeout=120.0)
                            if media_resp.status_code != 200:
                                safe_print(f"    [!] Media fetch failed with status {media_resp.status_code}: {media_resp.text[:300]}")
                                return []
                            
                            media_data = media_resp.json()
                            encoded_video = media_data.get("video", {}).get("encodedVideo", "")
                            
                            if encoded_video:
                                video_bytes = base64.b64decode(encoded_video)
                                safe_print(f"    [+] Decoded video: {len(video_bytes)} bytes ({len(video_bytes)//1024} KB)")
                                
                                filepath = os.path.join(self.ugc_dir, f"direct_flow_video_{int(time.time())}.mp4")
                                with open(filepath, "wb") as f:
                                    f.write(video_bytes)
                                safe_print(f"    [OK] Saved video -> {filepath}")
                                return [filepath]
                            else:
                                safe_print(f"    [!] No encodedVideo field in media response. Keys: {list(media_data.keys())}")
                                return []
                        
                        elif gen_status == "MEDIA_GENERATION_STATUS_FAILED":
                            error_info = m_item.get("mediaMetadata", {}).get("mediaStatus", {})
                            safe_print(f"    [!] Video generation FAILED: {error_info}")
                            return []
                        
                        elif gen_status == "MEDIA_GENERATION_STATUS_ACTIVE":
                            safe_print(f"    [*] Still generating...")
                        else:
                            safe_print(f"    [*] Status: {gen_status}")
                            
                except Exception as poll_e:
                    safe_print(f"    [!] Error during polling iteration: {poll_e}")
                    
            safe_print(f"  [!] Router: Video generation timed out after {timeout_limit}s.")
            return []
            
        except Exception as e:
            safe_print(f"  [!] Router: Direct Flow Video API error: {e}")
            return []

    async def generate_image(self, 
                             prompt: str, 
                             ref_image_paths: Optional[List[str]] = None,
                             aspect: str = "9:16",
                             output_prefix: str = "gen",
                             force_engine: str = "auto") -> List[str]:
        """
        Generate an image, routing to the best available engine.
        
        Args:
            prompt: Text description.
            ref_image_paths: Local paths to model/product reference images.
            aspect: Aspect ratio string (e.g., "3:4", "1:1", "16:9").
            output_prefix: Filename prefix.
            force_engine: 'auto', 'glabs', or 'flow'.
        """
        # Try G-Labs first if allowed and healthy
        if force_engine in ("auto", "glabs") and self._is_provider_healthy("glabs", force=(force_engine == "glabs")):
            is_glabs_online = await self.glabs.check_health()
            if is_glabs_online:
                safe_print("[*] Router: Routing image generation to G-Labs Automation server...")
                aspect_map = {
                    "3:4": "3:4",
                    "4:3": "4:3",
                    "1:1": "1:1",
                    "9:16": "9:16",
                    "16:9": "16:9"
                }
                glabs_aspect = aspect_map.get(aspect, "1:1")
                
                ref_base64 = []
                if ref_image_paths:
                    for path in ref_image_paths:
                        b64_str = path_to_base64(path)
                        if b64_str:
                            ref_base64.append({
                                "data": b64_str,
                                "name": os.path.basename(path)
                            })
                
                try:
                    task_id = await self.glabs.generate_image(
                        prompt=prompt,
                        model="nano_banana_pro",
                        aspect_ratio=glabs_aspect,
                        reference_images=ref_base64
                    )
                    
                    if task_id:
                        saved_files = await self.glabs.poll_task(task_id, self.dest_dir)
                        if saved_files:
                            safe_print(f"[OK] Router: G-Labs image generation completed: {saved_files}")
                            self._mark_provider_success("glabs")
                            return saved_files
                    
                    self._mark_provider_failed("glabs")
                except Exception as glabs_err:
                    safe_print(f"  [!] Router: G-Labs generation failed: {glabs_err}")
                    self._mark_provider_failed("glabs")
            else:
                self._mark_provider_failed("glabs")
                safe_print("[*] Router: G-Labs server offline. Proceeding to Direct Flow API...")
        
        # Try Direct Flow API (Golden API Pipeline) with health memory & retry logic
        if force_engine in ("auto", "flow") and self._is_provider_healthy("flow", force=(force_engine == "flow")):
            safe_print("[*] Router: Attempting Direct Google Flow HTTP API generation...")
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                safe_print(f"[*] Router: Flow API generation attempt {attempt}/{max_attempts}...")
                bearer, recaptcha, project_id, auth_user = await self._get_fresh_flow_tokens()
                if bearer and recaptcha:
                    import httpx
                    if not project_id or project_id in ("NOT_FOUND", "None", "null", ""):
                        project_id = "1e47f082-dbd5-4cf3-869e-cffbf8722f1b"
                        safe_print(f"  [!] Router: Project ID not found or None. Falling back to default project ID: {project_id}")
                    
                    async with httpx.AsyncClient() as client:
                        try:
                            asset_ids = []
                            if ref_image_paths:
                                for path in ref_image_paths:
                                    asset_id = await self._upload_image_to_flow_api(client, bearer, project_id, path, auth_user=auth_user)
                                    if asset_id:
                                        asset_ids.append(asset_id)
                                        
                            generated_files = await self._generate_flow_api(
                                client=client,
                                bearer=bearer,
                                recaptcha=recaptcha,
                                project_id=project_id,
                                prompt=prompt,
                                asset_ids=asset_ids,
                                aspect=aspect,
                                auth_user=auth_user
                            )
                            if generated_files:
                                safe_print(f"[OK] Router: Direct API generation completed on attempt {attempt}: {generated_files}")
                                self._mark_provider_success("flow")
                                return generated_files
                        except Exception as api_err:
                            safe_print(f"  [!] Router: Direct Flow API attempt {attempt} failed: {api_err}")
                else:
                    safe_print(f"  [!] Router: Could not acquire fresh Flow tokens on attempt {attempt}.")
                
                if attempt < max_attempts:
                    await asyncio.sleep(2.0)
            
            # If all attempts failed
            self._mark_provider_failed("flow")

        # Fallback to Stealth Bridge (localhost:9877)
        if force_engine in ("auto", "flow") and self._is_provider_healthy("bridge", force=(force_engine == "flow")):
            BRIDGE_URL = "http://localhost:9877/generate"
            safe_print(f"[*] Router: Falling back to legacy Stealth Bridge with {len(ref_image_paths or [])} reference(s)...")
            
            aspect_map = {
                "3:4": "PORTRAIT_THREE_FOUR",
                "4:3": "LANDSCAPE_FOUR_THREE",
                "1:1": "SQUARE",
                "9:16": "PORTRAIT_NINE_SIXTEEN",
                "16:9": "LANDSCAPE_SIXTEEN_NINE",
            }
            api_aspect = aspect_map.get(aspect, "PORTRAIT_THREE_FOUR")
            
            try:
                def _generate():
                    payload = {
                        "prompt": prompt,
                        "aspect": api_aspect,
                        "ref_image_paths": ref_image_paths or [],
                    }
                    resp = requests.post(BRIDGE_URL, json=payload, timeout=300)
                    resp.raise_for_status()
                    return resp.content
                    
                safe_print("[WAIT] Bridge generating...")
                image_bytes = await asyncio.to_thread(_generate)
                
                if len(image_bytes) < 1000:
                    try:
                        err = json.loads(image_bytes)
                        safe_print(f"   [!] Bridge returned error: {err}")
                        self._mark_provider_failed("bridge")
                        return []
                    except:
                        pass
                
                filepath = os.path.join(self.dest_dir, f"{output_prefix}_{int(time.time())}.png")
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                safe_print(f"   [OK] Saved {len(image_bytes)//1024}KB -> {os.path.basename(filepath)}")
                self._mark_provider_success("bridge")
                return [filepath]
                
            except Exception as e:
                safe_print(f"   [!] Bridge error: {e}")
                self._mark_provider_failed("bridge")
        
        # Fallback to Meta AI image generation (e.g. if force_engine="meta" or auto-fallback)
        if force_engine in ("auto", "meta") and self._is_provider_healthy("meta", force=(force_engine == "meta")):
            safe_print("[*] Router: Routing image generation to Meta AI automation worker...")
            try:
                worker = MetaAIVideoWorker(headless=True)
                generated_files = await worker.generate_image(prompt, ref_image_paths)
                if generated_files:
                    safe_print(f"[OK] Router: Meta AI image generation completed: {generated_files}")
                    self._mark_provider_success("meta")
                    return generated_files
                self._mark_provider_failed("meta")
            except Exception as e:
                safe_print(f"  [!] Router: Meta AI image generation failed: {e}")
                self._mark_provider_failed("meta")
        
        return []

    async def generate_video(self,
                             prompt: str,
                             ref_image_paths: Optional[List[str]] = None,
                             aspect: str = "9:16",
                             output_prefix: str = "gen_video",
                             voice_text: str = "",
                             voice_name: str = "default",
                             force_engine: str = "auto") -> List[str]:
        """
        Generate a video, routing to the best available engine. Muxes voice if provided.
        """
        video_path = None
        
        # Define tasks for APIs that can be run concurrently
        async def run_imagineart():
            if not self._is_provider_healthy("imagineart", force=(force_engine == "imagineart")):
                return None
            safe_print("[*] Router: Routing video generation to ImagineArt API...")
            try:
                res_url = await self.video_api.generate_imagineart_video(
                    image_path=ref_image_paths[0],
                    prompt=prompt,
                    aspect_ratio=aspect
                )
                if res_url:
                    dest_file = os.path.join(self.ugc_dir, f"imagineart_ugc_{int(time.time())}.mp4")
                    success = await self.video_api.download_video(res_url, dest_file)
                    if success and self._validate_video(dest_file):
                        self._mark_provider_success("imagineart")
                        return dest_file
                self._mark_provider_failed("imagineart")
            except Exception as e:
                safe_print(f"[!] Router: ImagineArt API error: {e}")
                self._mark_provider_failed("imagineart")
            return None

        async def run_fal():
            if not self._is_provider_healthy("fal", force=(force_engine == "fal")):
                return None
            safe_print("[*] Router: Routing video generation to Fal.ai API...")
            try:
                res_url = await self.video_api.generate_fal_video(
                    image_path=ref_image_paths[0],
                    prompt=prompt,
                    aspect_ratio=aspect
                )
                if res_url:
                    dest_file = os.path.join(self.ugc_dir, f"fal_ugc_{int(time.time())}.mp4")
                    success = await self.video_api.download_video(res_url, dest_file)
                    if success and self._validate_video(dest_file):
                        self._mark_provider_success("fal")
                        return dest_file
                self._mark_provider_failed("fal")
            except Exception as e:
                safe_print(f"[!] Router: Fal.ai API error: {e}")
                self._mark_provider_failed("fal")
            return None

        # 1 & 2. Try ImagineArt and Fal.ai APIs concurrently
        tasks = []
        if force_engine in ("auto", "imagineart") and ref_image_paths and self.video_api.is_imagineart_available():
            tasks.append(run_imagineart())
        if force_engine in ("auto", "fal") and ref_image_paths and self.video_api.is_fal_available():
            tasks.append(run_fal())
            
        if tasks:
            results = await asyncio.gather(*tasks)
            # Pick the first non-None result
            for res in results:
                if res:
                    video_path = res
                    break

        # 2.5 Try Direct Flow Video API (Golden API Pipeline) with health memory & retry logic
        # Supports both Text-to-Video (veo_3_1_t2v_lite) and Image-to-Video (veo_3_1_i2v_lite).
        should_try_flow = force_engine in ("auto", "flow")
        if not video_path and should_try_flow and self._is_provider_healthy("flow", force=(force_engine == "flow")):
            safe_print("[*] Router: Attempting Direct Google Flow HTTP API Video generation...")
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                safe_print(f"[*] Router: Flow Video API generation attempt {attempt}/{max_attempts}...")
                actions = {1: "VIDEO_GENERATION", 2: "VIDEO_GENERATION", 3: "VIDEO_GENERATION"}
                current_action = actions.get(attempt, "IMAGE_GENERATION")
                safe_print(f"  [*] Router: Requesting token for action '{current_action}'...")
                bearer, recaptcha, project_id, auth_user = await self._get_fresh_flow_tokens(current_action)
                if bearer and recaptcha:
                    import httpx
                    if not project_id or project_id in ("NOT_FOUND", "None", "null", ""):
                        project_id = "1e47f082-dbd5-4cf3-869e-cffbf8722f1b"
                        safe_print(f"  [!] Router: Project ID not found or None. Falling back to default project ID: {project_id}")
                    
                    async with httpx.AsyncClient() as client:
                        try:
                            asset_ids = []
                            if ref_image_paths:
                                for path in ref_image_paths:
                                    asset_id = await self._upload_image_to_flow_api(client, bearer, project_id, path, auth_user=auth_user)
                                    if asset_id:
                                        asset_ids.append(asset_id)
                                        
                            generated_files = await self._generate_flow_video_api(
                                client=client,
                                bearer=bearer,
                                recaptcha=recaptcha,
                                project_id=project_id,
                                prompt=prompt,
                                asset_ids=asset_ids,
                                aspect=aspect,
                                auth_user=auth_user,
                                action=current_action
                            )
                            if generated_files and self._validate_video(generated_files[0]):
                                video_path = generated_files[0]
                                safe_print(f"[OK] Router: Direct Video API generation completed on attempt {attempt}: {video_path}")
                                self._mark_provider_success("flow")
                                break
                        except Exception as api_err:
                            safe_print(f"  [!] Router: Direct Flow Video API attempt {attempt} failed: {api_err}")
                else:
                    safe_print(f"  [!] Router: Could not acquire fresh Flow tokens on attempt {attempt}.")
                
                if attempt < max_attempts:
                    await asyncio.sleep(2.0)
            
            if not video_path:
                self._mark_provider_failed("flow")

        # 3. Try G-Labs Local Server
        if not video_path and force_engine in ("auto", "glabs") and self._is_provider_healthy("glabs", force=(force_engine == "glabs")):
            is_glabs_online = await self.glabs.check_health()
            if is_glabs_online:
                safe_print("[*] Router: Routing video generation to G-Labs Automation server...")
                ref_base64 = []
                if ref_image_paths:
                    for path in ref_image_paths:
                        b64_str = path_to_base64(path)
                        if b64_str:
                            ref_base64.append({
                                "data": b64_str,
                                "name": os.path.basename(path)
                            })
                
                try:
                    task_id = await self.glabs.generate_video(
                        prompt=prompt,
                        model="veo_31_fast",
                        aspect_ratio=aspect,
                        mode="components" if ref_image_paths else "text_to_video",
                        reference_images=ref_base64,
                        resolution=["720p"]
                    )
                    if task_id:
                        saved_files = await self.glabs.poll_task(task_id, self.ugc_dir)
                        if saved_files and self._validate_video(saved_files[0]):
                            video_path = saved_files[0]
                            self._mark_provider_success("glabs")
                        else:
                            self._mark_provider_failed("glabs")
                    else:
                        self._mark_provider_failed("glabs")
                except Exception as glabs_err:
                    safe_print(f"[!] Router: G-Labs video generation failed: {glabs_err}")
                    self._mark_provider_failed("glabs")
            else:
                self._mark_provider_failed("glabs")
                safe_print("[*] Router: G-Labs server offline. Falling back to browser automation...")

        # 4. Try Kling AI Video Bridge
        if not video_path and force_engine in ("auto", "kling") and ref_image_paths and self._is_provider_healthy("kling", force=(force_engine == "kling")):
            safe_print("[*] Router: Attempting Kling AI video generation fallback...")
            try:
                bridge = await self._get_video_bridge()
                res_path = await bridge.generate_kling_video(ref_image_paths[0], prompt)
                if res_path and self._validate_video(res_path):
                    video_path = res_path
                    self._mark_provider_success("kling")
                else:
                    self._mark_provider_failed("kling")
            except Exception as e:
                safe_print(f"[!] Router: Kling AI Bridge error: {e}")
                self._mark_provider_failed("kling")

        # 5. Try Meta AI Video Worker
        if not video_path and force_engine in ("auto", "meta") and self._is_provider_healthy("meta", force=(force_engine == "meta")):
            safe_print("[*] Router: Attempting Meta AI video generation fallback...")
            worker = MetaAIVideoWorker(headless=True)
            try:
                res_paths = await worker.generate_video(prompt, ref_image_paths)
                if res_paths and self._validate_video(res_paths[0]):
                    video_path = res_paths[0]
                    self._mark_provider_success("meta")
                else:
                    self._mark_provider_failed("meta")
            except Exception as e:
                safe_print(f"[!] Router: Meta AI Video Worker error: {e}")
                self._mark_provider_failed("meta")

        # 6. Try Dreamina (Seedance 2.0) Video Bridge
        if not video_path and force_engine in ("auto", "dreamina") and ref_image_paths and self._is_provider_healthy("dreamina", force=(force_engine == "dreamina")):
            safe_print("[*] Router: Attempting Dreamina video generation fallback...")
            try:
                bridge = await self._get_video_bridge()
                res_path = await bridge.generate_dreamina_video(ref_image_paths[0], prompt)
                if res_path and self._validate_video(res_path):
                    video_path = res_path
                    self._mark_provider_success("dreamina")
                else:
                    self._mark_provider_failed("dreamina")
            except Exception as e:
                safe_print(f"[!] Router: Dreamina Bridge error: {e}")
                self._mark_provider_failed("dreamina")

        # If no video generated, return empty list
        if not video_path or not os.path.exists(video_path):
            safe_print("[!] Router: Failed to generate video clip.")
            return []

        # 4. Synthesize voiceover and mux if voice text is provided
        if voice_text:
            safe_print(f"[*] Router: Generating audio track: '{voice_text[:30]}...'")
            audio_out_path = os.path.join(self.ugc_dir, f"audio_{int(time.time())}.mp3")
            audio_path = await self.voice_gen.generate_audio(
                text=voice_text,
                voice_name=voice_name,
                output_path=audio_out_path
            )
            
            if audio_path and os.path.exists(audio_path):
                mixed_out_path = os.path.join(self.ugc_dir, f"{output_prefix}_{int(time.time())}_ugc.mp4")
                final_path = self.voice_gen.combine_video_audio(
                    video_path=video_path,
                    audio_path=audio_path,
                    output_path=mixed_out_path
                )
                if final_path:
                    return [final_path]
            else:
                safe_print("[!] Router: Audio track generation failed. Returning un-narrated video.")

        return [video_path]
