"""
VIDEO API CLIENT — REST API Integration for ImagineArt and Fal.ai
=================================================================
Provides direct API-based video generation as the primary pipeline,
allowing Playwright browser automation to serve as a reliable fallback.
"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional

class VideoAPIClient:
    def __init__(self):
        self.imagineart_key = os.getenv("IMAGINEART_API_KEY", "")
        self.fal_key = os.getenv("FAL_API_KEY", "")

    def is_imagineart_available(self) -> bool:
        return bool(self.imagineart_key)

    def is_fal_available(self) -> bool:
        return bool(self.fal_key)

    # ═══════════════════════════════════════════════════════════════
    # IMAGINEART (Vyro AI) API
    # 100 Free Daily Credits
    # ═══════════════════════════════════════════════════════════════
    async def generate_imagineart_video(
        self,
        image_path: str,
        prompt: str,
        style: str = "kling-1.0-pro",
        aspect_ratio: str = "16:9",
        poll_interval: int = 10,
        timeout: int = 300
    ) -> Optional[str]:
        """
        Generates video using ImagineArt REST API.
        Returns the direct URL to the generated video, or None if failed.
        """
        if not self.is_imagineart_available():
            print("[-] ImagineArt API key not configured.")
            return None

        img_path = Path(image_path)
        if not img_path.exists():
            print(f"[-] Image path does not exist: {image_path}")
            return None

        url = "https://api.vyro.ai/v2/video/image-to-video"
        headers = {
            "Authorization": f"Bearer {self.imagineart_key}"
        }

        # Build multipart form data
        data = aiohttp.FormData()
        data.add_field("style", style)
        data.add_field("prompt", prompt)
        data.add_field("aspect_ratio", aspect_ratio)
        
        # Read image bytes
        with open(img_path, "rb") as f:
            image_bytes = f.read()
        data.add_field("file", image_bytes, filename=img_path.name, content_type="image/jpeg")

        async with aiohttp.ClientSession() as session:
            try:
                print(f"[ImagineArt] Submitting image-to-video task (style: {style})...")
                async with session.post(url, headers=headers, data=data) as resp:
                    if resp.status not in (200, 201, 202):
                        err_text = await resp.text()
                        print(f"[-] ImagineArt submit failed: Status {resp.status} - {err_text}")
                        return None
                    
                    res_data = await resp.json()
                    task_id = res_data.get("id")
                    if not task_id:
                        print(f"[-] No task ID returned from ImagineArt: {res_data}")
                        return None

                print(f"[ImagineArt] Task submitted successfully. ID: {task_id}. Polling for completion...")
                
                # Poll for status
                status_url = f"https://api.vyro.ai/v2/video/{task_id}/status"
                start_time = asyncio.get_event_loop().time()
                
                while asyncio.get_event_loop().time() - start_time < timeout:
                    await asyncio.sleep(poll_interval)
                    async with session.get(status_url, headers=headers) as resp:
                        if resp.status != 200:
                            print(f"[!] Error checking ImagineArt status (HTTP {resp.status})")
                            continue
                        
                        status_data = await resp.json()
                        # Structure: {"status": "success", "video": {"id": 1265, "status": "completed"/"processing", "url": "..."}}
                        # Or simple status
                        status = status_data.get("status")
                        video_info = status_data.get("video", {})
                        video_status = video_info.get("status") if isinstance(video_info, dict) else None
                        
                        # Fallbacks
                        if not video_status:
                            video_status = status_data.get("video_status") or status
                            
                        print(f"   [ImagineArt] Status check: status={status}, video_status={video_status}")

                        if video_status in ("completed", "success") or (status == "success" and video_info.get("url")):
                            video_url = video_info.get("url") if isinstance(video_info, dict) else status_data.get("url")
                            if video_url:
                                print(f"[ImagineArt] Video generated successfully! URL: {video_url}")
                                return video_url
                        elif video_status in ("failed", "error"):
                            print(f"[-] ImagineArt video generation failed: {status_data}")
                            return None
                            
                print("[-] ImagineArt video generation timed out.")
                return None

            except Exception as e:
                print(f"[-] Exception in ImagineArt generator: {e}")
                return None

    # ═══════════════════════════════════════════════════════════════
    # FAL.AI API
    # $10 Free Credits
    # ═══════════════════════════════════════════════════════════════
    async def generate_fal_video(
        self,
        image_path: str,
        prompt: str,
        model: str = "fal-ai/kling-video/v1/standard/image-to-video",
        aspect_ratio: str = "16:9",
        poll_interval: int = 10,
        timeout: int = 300
    ) -> Optional[str]:
        """
        Generates video using Fal.ai Queue API.
        """
        if not self.is_fal_available():
            print("[-] Fal.ai API key not configured.")
            return None

        img_path = Path(image_path)
        if not img_path.exists():
            print(f"[-] Image path does not exist: {image_path}")
            return None

        headers = {
            "Authorization": f"Key {self.fal_key}",
            "Content-Type": "application/json"
        }

        # 1. Upload the image to fal storage using serverless files endpoint or direct storage upload
        # Wait, the simplest way is to upload to fal's direct upload endpoint if available,
        # or we can write image as Base64 data URL.
        # Let's try sending as Base64 first!
        import base64
        ext = img_path.suffix.lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        image_url = f"data:image/{ext};base64,{encoded_string}"

        # Setup standard payload
        payload = {
            "prompt": prompt,
            "image_url": image_url,
            "aspect_ratio": aspect_ratio
        }

        # Submit to queue
        submit_url = f"https://queue.fal.run/{model}"
        
        async with aiohttp.ClientSession() as session:
            try:
                print(f"[Fal.ai] Submitting image-to-video task to {model}...")
                async with session.post(submit_url, headers=headers, json=payload) as resp:
                    if resp.status not in (200, 201, 202):
                        err_text = await resp.text()
                        print(f"[-] Fal.ai submit failed with status {resp.status}: {err_text}")
                        # If Base64 payload was too large, let's try direct file upload
                        print("[Fal.ai] Retrying with direct file upload...")
                        upload_url = f"https://api.fal.ai/v1/serverless/files/file/local/inputs/{img_path.name}"
                        upload_headers = {"Authorization": f"Key {self.fal_key}"}
                        
                        data = aiohttp.FormData()
                        with open(img_path, "rb") as f:
                            file_bytes = f.read()
                        data.add_field("file_upload", file_bytes, filename=img_path.name, content_type=f"image/{ext}")
                        
                        async with session.post(upload_url, headers=upload_headers, data=data) as upload_resp:
                            if upload_resp.status not in (200, 201):
                                print(f"[-] Fal.ai file upload failed: {await upload_resp.text()}")
                                return None
                            upload_data = await upload_resp.json()
                            uploaded_url = upload_data.get("url")
                            if not uploaded_url:
                                print("[-] Upload response missing URL.")
                                return None
                        
                        # Resubmit with hosted URL
                        payload["image_url"] = uploaded_url
                        async with session.post(submit_url, headers=headers, json=payload) as retry_resp:
                            if retry_resp.status not in (200, 201, 202):
                                print(f"[-] Fal.ai retry submit failed: {await retry_resp.text()}")
                                return None
                            res_data = await retry_resp.json()
                    else:
                        res_data = await resp.json()

                request_id = res_data.get("request_id")
                status_url = res_data.get("status_url")
                response_url = res_data.get("response_url")

                if not request_id:
                    print(f"[-] No request ID returned from Fal.ai: {res_data}")
                    return None

                print(f"[Fal.ai] Task submitted. Request ID: {request_id}. Polling...")

                start_time = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - start_time < timeout:
                    await asyncio.sleep(poll_interval)
                    
                    # Call status URL
                    async with session.get(status_url, headers=headers) as resp:
                        if resp.status != 200:
                            print(f"[!] Error checking Fal.ai status: HTTP {resp.status}")
                            continue
                        
                        status_data = await resp.json()
                        status = status_data.get("status", "").upper()
                        print(f"   [Fal.ai] Status check: {status}")

                        if status == "COMPLETED":
                            # Fetch final response
                            async with session.get(response_url, headers=headers) as resp_final:
                                if resp_final.status == 200:
                                    final_data = await resp_final.json()
                                    # Output varies slightly by model, but standard is {"video": {"url": "..."}}
                                    video_url = final_data.get("video", {}).get("url") or final_data.get("url")
                                    if video_url:
                                        print(f"[Fal.ai] Video generated successfully! URL: {video_url}")
                                        return video_url
                            print("[-] Fal.ai completed but failed to parse response.")
                            return None
                        elif status in ("FAILED", "ERROR"):
                            print(f"[-] Fal.ai task failed: {status_data}")
                            return None

                print("[-] Fal.ai generation timed out.")
                return None

            except Exception as e:
                print(f"[-] Exception in Fal.ai generator: {e}")
                return None

    async def download_video(self, video_url: str, output_path: str) -> bool:
        """Helper to download a generated video from a URL."""
        out_path = Path(output_path)
        out_path.parent.mkdir(exist_ok=True, parents=True)

        async with aiohttp.ClientSession() as session:
            try:
                print(f"[Video API] Downloading from {video_url} to {output_path}...")
                async with session.get(video_url, timeout=120) as resp:
                    if resp.status == 200:
                        with open(out_path, "wb") as f:
                            f.write(await resp.read())
                        print(f"[Video API] Download completed: {output_path}")
                        return True
                    else:
                        print(f"[-] Download failed: Status {resp.status}")
            except Exception as e:
                print(f"[-] Exception downloading video: {e}")
        return False
