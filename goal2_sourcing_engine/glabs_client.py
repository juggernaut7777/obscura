import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional

class GLabsClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8765", api_key: str = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("GLABS_API_KEY", "")
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def check_health(self) -> bool:
        """Check if G-Labs Automation server is online."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/api/health", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("status") == "ok"
            except Exception:
                return False
        return False

    async def generate_image(self, prompt: str, model: str = "imagen4", 
                             aspect_ratio: str = "1:1", reference_images: List[str] = None, 
                             upscale: List[str] = None) -> Optional[str]:
        """Submit an image generation task. Returns task_id if successful."""
        payload = {
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "reference_images": reference_images or [],
            "upscale": upscale or []
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.base_url}/api/image/generate", 
                                       headers=self.headers, json=payload, timeout=30) as resp:
                    if resp.status == 202:
                        data = await resp.json()
                        return data.get("task_id")
                    else:
                        print(f"[GLabs] Generate image failed with status {resp.status}: {await resp.text()}")
            except Exception as e:
                print(f"[GLabs] Error submitting image task: {e}")
        return None

    async def generate_video(self, prompt: str, model: str = "veo_31_fast", 
                             aspect_ratio: str = "16:9", mode: str = "text_to_video", 
                             reference_images: List[str] = None, resolution: List[str] = None, 
                             voice: str = "", video_length: int = None) -> Optional[str]:
        """Submit a video generation task. Returns task_id if successful."""
        payload = {
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "mode": mode,
            "reference_images": reference_images or [],
            "resolution": resolution or ["720p"]
        }
        if voice:
            payload["voice"] = voice
        if video_length:
            payload["video_length"] = video_length

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.base_url}/api/video/generate", 
                                       headers=self.headers, json=payload, timeout=30) as resp:
                    if resp.status == 202:
                        data = await resp.json()
                        return data.get("task_id")
                    else:
                        print(f"[GLabs] Generate video failed with status {resp.status}: {await resp.text()}")
            except Exception as e:
                print(f"[GLabs] Error submitting video task: {e}")
        return None

    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific task."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/api/status/{task_id}", 
                                      headers=self.headers, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception as e:
                print(f"[GLabs] Error checking task status {task_id}: {e}")
        return None

    async def download_file(self, file_url: str, save_path: str) -> bool:
        """Download a generated output file."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(file_url, timeout=60) as resp:
                    if resp.status == 200:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(await resp.read())
                        return True
            except Exception as e:
                print(f"[GLabs] Error downloading file {file_url}: {e}")
        return False

    async def poll_task(self, task_id: str, save_dir: str, interval: int = 5, 
                        timeout: int = 600) -> List[str]:
        """Poll task status and download results when completed."""
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            status_data = await self.get_status(task_id)
            if not status_data:
                await asyncio.sleep(interval)
                continue

            status = status_data.get("status")
            if status == "completed":
                results = status_data.get("results", [])
                saved_paths = []
                for url in results:
                    filename = url.split("/")[-1]
                    save_path = os.path.join(save_dir, filename)
                    if await self.download_file(url, save_path):
                        saved_paths.append(save_path)
                return saved_paths
            elif status == "failed":
                print(f"[GLabs] Task {task_id} failed: {status_data.get('error')}")
                return []
            
            await asyncio.sleep(interval)
        
        print(f"[GLabs] Task {task_id} timed out after {timeout}s")
        return []

async def test_connection():
    client = GLabsClient()
    is_alive = await client.check_health()
    print(f"G-Labs Server Status on port 8765: {'ONLINE' if is_alive else 'OFFLINE'}")

if __name__ == "__main__":
    asyncio.run(test_connection())
