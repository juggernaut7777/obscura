import os
import sys
import asyncio
import time
from typing import Optional, List
from playwright.async_api import async_playwright

def safe_print(msg: str):
    """Safely print messages on Windows to avoid UnicodeEncodeErrors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding, errors='replace'))
        except Exception:
            print("[Print Error] Unable to encode output print message.")

# Recurse through Shadow DOM to find prompt inputs or video outputs
FIND_INPUT_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 10) return null;
        const all = root.querySelectorAll('*');
        for (const el of all) {
            const ph = el.getAttribute('placeholder') || '';
            const ariaLabel = el.getAttribute('aria-label') || '';
            if (ph.toLowerCase().includes('ask meta') || 
                ph.toLowerCase().includes('want to create') ||
                ph.toLowerCase().includes('prompt') ||
                ariaLabel.toLowerCase().includes('ask') ||
                ariaLabel.toLowerCase().includes('prompt')) {
                return el;
            }
            if (el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && el.type === 'text')) {
                return el;
            }
            if (el.shadowRoot) {
                const found = findInShadow(el.shadowRoot, depth + 1);
                if (found) return found;
            }
        }
        return null;
    }
    const el = findInShadow(document, 0);
    if (el) {
        el.focus();
        return true;
    }
    return false;
}"""

FIND_VIDEO_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 10) return [];
        const results = [];
        const all = root.querySelectorAll('video');
        for (const el of all) {
            results.push(el.src || el.querySelector('source')?.src || '');
        }
        const shadows = root.querySelectorAll('*');
        for (const el of shadows) {
            if (el.shadowRoot) {
                results.push(...findInShadow(el.shadowRoot, depth + 1));
            }
        }
        return results;
    }
    return findInShadow(document, 0);
}"""

FIND_IMAGE_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 10) return [];
        const results = [];
        const all = root.querySelectorAll('img');
        for (const el of all) {
            const w = el.naturalWidth || el.width || 0;
            const h = el.naturalHeight || el.height || 0;
            const src = el.src || '';
            // Generated images are large (usually 512x512 or 1024x1024)
            // Skip static FB assets (e.g. rsrc.php, static UI assets)
            if (src && 
                !src.includes('data:image/svg+xml') && 
                !src.includes('/rsrc.php/') && 
                !src.includes('/static/') && 
                (w >= 256 || h >= 256 || (!w && !h && (src.startsWith('blob:') || src.includes('scontent'))))) {
                results.push(src);
            }
        }
        const shadows = root.querySelectorAll('*');
        for (const el of shadows) {
            if (el.shadowRoot) {
                results.push(...findInShadow(el.shadowRoot, depth + 1));
            }
        }
        return results;
    }
    return findInShadow(document, 0);
}"""

class MetaAIVideoWorker:
    def __init__(self, headless: bool = True, profile_dir: str = "playwright_profile_meta"):
        self.headless = headless
        self.profile_dir = os.path.abspath(profile_dir)
        self.dest_dir = os.path.join(os.getcwd(), "output_ugc")
        os.makedirs(self.dest_dir, exist_ok=True)

    async def generate_image(self, prompt: str, ref_image_paths: Optional[List[str]] = None) -> List[str]:
        """Automates Meta AI to generate an image."""
        safe_print(f"[*] MetaAI: Initializing unified browser session for image generation...")
        
        async with async_playwright() as p:
            import browser_helper
            browser_session = await browser_helper.get_browser_context(
                p,
                headless=self.headless,
                profile_dir=self.profile_dir
            )
            context = browser_session.context
            
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Apply stealth scripts
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            safe_print("[*] MetaAI: Navigating to meta.ai...")
            try:
                await page.goto("https://www.meta.ai/", wait_until="load", timeout=90000)
            except Exception as e:
                safe_print(f"[!] MetaAI: Initial load timed out, trying page load fallback: {e}")
            
            await asyncio.sleep(5)
            
            # Try to click accept/sign-in dialogs if they block
            try:
                for selector in ["button:has-text('Accept All')", "button:has-text('Accept')", "button:has-text('Agree')"]:
                    if await page.locator(selector).is_visible():
                        await page.locator(selector).click()
                        await asyncio.sleep(2)
            except Exception:
                pass
            
            try:
                # If reference images are provided, upload them first
                if ref_image_paths:
                    safe_print(f"[*] MetaAI: Uploading reference images: {ref_image_paths}")
                    for img_path in ref_image_paths:
                        if os.path.exists(img_path):
                            file_input = page.locator('input[type="file"]')
                            if await file_input.count() > 0:
                                await file_input.first.set_input_files(img_path)
                                safe_print(f"   [+] Uploaded via file input: {img_path}")
                            else:
                                upload_trigger = page.locator('[aria-label*="attach" i], [aria-label*="upload" i], button:has-text("Attach"), button:has-text("Upload"), [class*="attach"], [class*="upload"]').first
                                if await upload_trigger.count() > 0:
                                    async with page.expect_file_chooser() as fc_info:
                                        await upload_trigger.click()
                                    file_chooser = await fc_info.value
                                    await file_chooser.set_files(img_path)
                                    safe_print(f"   [+] Uploaded via file chooser trigger: {img_path}")
                                else:
                                    safe_print(f"   [!] Could not find upload input or button for: {img_path}")
                            await asyncio.sleep(4) # Wait for file upload to register

                # Find and fill the prompt textbox
                safe_print("[*] MetaAI: Finding prompt input box...")
                input_found = await page.evaluate(FIND_INPUT_JS)
                if not input_found:
                    safe_print("[!] MetaAI: Prompt box not found via Shadow DOM. Retrying selector-based input...")
                    try:
                        await page.click("textarea", timeout=10000)
                        input_found = True
                    except Exception:
                        pass
                
                if not input_found:
                    safe_print("[!] MetaAI: Failed to locate input textbox. Saving page screenshot for debugging...")
                    await page.screenshot(path=os.path.join(self.dest_dir, "meta_ai_image_input_failed.png"))
                    await browser_session.close()
                    return []
                    
                image_prompt = prompt
                if not prompt.lower().startswith("imagine") and not prompt.lower().startswith("generate"):
                    image_prompt = f"imagine {prompt}"
                    
                safe_print(f"[*] MetaAI: Inputting prompt: {image_prompt}")
                await page.keyboard.type(image_prompt, delay=50)
                await asyncio.sleep(1)
                
                # Submit the prompt (Press Enter)
                safe_print("[*] MetaAI: Submitting prompt...")
                await page.keyboard.press("Enter")
                
                # Wait for generation to start and complete (usually 15-90 seconds, poll up to 180s)
                safe_print("[*] MetaAI: Waiting for image generation (polling up to 180s)...")
                image_urls = []
                start_time = time.time()
                
                while time.time() - start_time < 180:
                    await asyncio.sleep(5)
                    image_urls = await page.evaluate(FIND_IMAGE_JS)
                    image_urls = [url for url in image_urls if url]
                    if image_urls:
                        safe_print(f"[OK] MetaAI: Found generated image source candidates: {len(image_urls)}")
                        break
                
                if not image_urls:
                    safe_print("[!] MetaAI: Image element did not appear within timeout. Saving debug screenshot...")
                    await page.screenshot(path=os.path.join(self.dest_dir, "meta_ai_image_generation_timeout.png"))
                    await browser_session.close()
                    return []
                    
                # Download the image file (pick the last one)
                image_url = image_urls[-1]
                filename = f"meta_image_{int(time.time())}.png"
                dest_path = os.path.join(self.dest_dir, filename)
                
                safe_print(f"[*] MetaAI: Downloading image from {image_url[:100]}... to {dest_path}...")
                
                if image_url.startswith("blob:"):
                    js_download = f"""async (url) => {{
                        const resp = await fetch(url);
                        const blob = await resp.blob();
                        return new Promise((resolve) => {{
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.readAsDataURL(blob);
                        }});
                    }}"""
                    base64_data = await page.evaluate(js_download, image_url)
                    if base64_data and "," in base64_data:
                        import base64
                        bytes_data = base64.b64decode(base64_data.split(",")[1])
                        with open(dest_path, "wb") as f:
                            f.write(bytes_data)
                        safe_print(f"[OK] MetaAI: Downloaded blob image -> {dest_path}")
                        await browser_session.close()
                        return [dest_path]
                elif image_url.startswith("data:image"):
                    import base64
                    try:
                        header, encoded = image_url.split(",", 1)
                        bytes_data = base64.b64decode(encoded)
                        with open(dest_path, "wb") as f:
                            f.write(bytes_data)
                        safe_print(f"[OK] MetaAI: Decoded data URI image -> {dest_path}")
                        await browser_session.close()
                        return [dest_path]
                    except Exception as e:
                        safe_print(f"[!] MetaAI data URI decode failed: {e}")
                else:
                    import aiohttp
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(image_url, timeout=45) as resp:
                                if resp.status == 200:
                                    with open(dest_path, "wb") as f:
                                        f.write(await resp.read())
                                    safe_print(f"[OK] MetaAI: Downloaded image -> {dest_path}")
                                    await browser_session.close()
                                    return [dest_path]
                    except Exception as e:
                        safe_print(f"[!] MetaAI: aiohttp download failed: {e}")
                
            except Exception as e:
                safe_print(f"[!] MetaAI generation error: {e}")
                try:
                    await page.screenshot(path=os.path.join(self.dest_dir, f"meta_ai_image_fail_{int(time.time())}.png"))
                except Exception:
                    pass
            finally:
                await browser_session.close()
            
            return []

    async def generate_video(self, prompt: str, ref_image_paths: Optional[List[str]] = None) -> List[str]:
        """Automates Meta AI to generate a video clip."""
        safe_print(f"[*] MetaAI: Initializing unified browser session...")
        
        async with async_playwright() as p:
            import browser_helper
            browser_session = await browser_helper.get_browser_context(
                p,
                headless=self.headless,
                profile_dir=self.profile_dir
            )
            context = browser_session.context
            
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Apply stealth scripts
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            safe_print("[*] MetaAI: Navigating to meta.ai...")
            try:
                await page.goto("https://www.meta.ai/", wait_until="load", timeout=90000)
            except Exception as e:
                safe_print(f"[!] MetaAI: Initial load timed out, trying page load fallback: {e}")
            
            await asyncio.sleep(5)
            
            # Try to click accept/sign-in dialogs if they block
            try:
                for selector in ["button:has-text('Accept All')", "button:has-text('Accept')", "button:has-text('Agree')"]:
                    if await page.locator(selector).is_visible():
                        await page.locator(selector).click()
                        await asyncio.sleep(2)
            except Exception:
                pass
            
            try:
                # If reference images are provided, upload them first
                if ref_image_paths:
                    safe_print(f"[*] MetaAI: Uploading reference images: {ref_image_paths}")
                    for img_path in ref_image_paths:
                        if os.path.exists(img_path):
                            file_input = page.locator('input[type="file"]')
                            if await file_input.count() > 0:
                                await file_input.first.set_input_files(img_path)
                                safe_print(f"   [+] Uploaded via file input: {img_path}")
                            else:
                                upload_trigger = page.locator('[aria-label*="attach" i], [aria-label*="upload" i], button:has-text("Attach"), button:has-text("Upload"), [class*="attach"], [class*="upload"]').first
                                if await upload_trigger.count() > 0:
                                    async with page.expect_file_chooser() as fc_info:
                                        await upload_trigger.click()
                                    file_chooser = await fc_info.value
                                    await file_chooser.set_files(img_path)
                                    safe_print(f"   [+] Uploaded via file chooser trigger: {img_path}")
                                else:
                                    safe_print(f"   [!] Could not find upload input or button for: {img_path}")
                            await asyncio.sleep(4) # Wait for file upload to register

                # Find and fill the prompt textbox
                safe_print("[*] MetaAI: Finding prompt input box...")
                input_found = await page.evaluate(FIND_INPUT_JS)
                if not input_found:
                    safe_print("[!] MetaAI: Prompt box not found via Shadow DOM. Retrying selector-based input...")
                    try:
                        await page.click("textarea", timeout=10000)
                        input_found = True
                    except Exception:
                        pass
                
                if not input_found:
                    safe_print("[!] MetaAI: Failed to locate input textbox. Saving page screenshot for debugging...")
                    await page.screenshot(path=os.path.join(self.dest_dir, "meta_ai_input_failed.png"))
                    await browser_session.close()
                    return []
                    
                video_prompt = prompt
                if not prompt.lower().startswith("generate a video") and not prompt.lower().startswith("/animate"):
                    video_prompt = f"generate a video of {prompt}"
                    
                safe_print(f"[*] MetaAI: Inputting prompt: {video_prompt}")
                await page.keyboard.type(video_prompt, delay=50)
                await asyncio.sleep(1)
                
                # Submit the prompt (Press Enter)
                safe_print("[*] MetaAI: Submitting prompt...")
                await page.keyboard.press("Enter")
                
                # Wait for generation to start and complete (usually 30-180 seconds, poll up to 300s)
                safe_print("[*] MetaAI: Waiting for video generation (polling up to 300s)...")
                video_urls = []
                start_time = time.time()
                
                while time.time() - start_time < 300:
                    await asyncio.sleep(5)
                    video_urls = await page.evaluate(FIND_VIDEO_JS)
                    video_urls = [url for url in video_urls if url]
                    if video_urls:
                        safe_print(f"[OK] MetaAI: Found generated video source: {video_urls[0]}")
                        break
                
                if not video_urls:
                    safe_print("[!] MetaAI: Video element did not appear within timeout. Saving debug screenshot...")
                    await page.screenshot(path=os.path.join(self.dest_dir, "meta_ai_generation_timeout.png"))
                    await browser_session.close()
                    return []
                    
                # Download the video file
                video_url = video_urls[0]
                filename = f"meta_video_{int(time.time())}.mp4"
                dest_path = os.path.join(self.dest_dir, filename)
                
                safe_print(f"[*] MetaAI: Downloading video from {video_url} to {dest_path}...")
                
                if video_url.startswith("blob:"):
                    js_download = f"""async (url) => {{
                        const resp = await fetch(url);
                        const blob = await resp.blob();
                        return new Promise((resolve) => {{
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.readAsDataURL(blob);
                        }});
                    }}"""
                    base64_data = await page.evaluate(js_download, video_url)
                    if base64_data and "," in base64_data:
                        import base64
                        bytes_data = base64.b64decode(base64_data.split(",")[1])
                        with open(dest_path, "wb") as f:
                            f.write(bytes_data)
                        safe_print(f"[OK] MetaAI: Downloaded blob video -> {dest_path}")
                        await browser_session.close()
                        return [dest_path]
                else:
                    import aiohttp
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(video_url, timeout=45) as resp:
                                if resp.status == 200:
                                    with open(dest_path, "wb") as f:
                                        f.write(await resp.read())
                                    safe_print(f"[OK] MetaAI: Downloaded video -> {dest_path}")
                                    await browser_session.close()
                                    return [dest_path]
                    except Exception as e:
                        safe_print(f"[!] MetaAI: aiohttp download failed: {e}")
                
            except Exception as e:
                safe_print(f"[!] MetaAI generation error: {e}")
                try:
                    await page.screenshot(path=os.path.join(self.dest_dir, f"meta_ai_fail_{int(time.time())}.png"))
                except Exception:
                    pass
            finally:
                await browser_session.close()
            
            return []

async def test_generation():
    worker = MetaAIVideoWorker(headless=True)
    paths = await worker.generate_video("a luxury golden necklace floating on water, 4k resolution")
    print(f"Meta AI Generated Paths: {paths}")

if __name__ == "__main__":
    asyncio.run(test_generation())
