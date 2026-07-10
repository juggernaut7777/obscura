"""
Video Generator Bridge — Browser Automation Hack
==============================================
Since we do not have a $3,000 GPU and video APIs are expensive, this script uses
Playwright to hijack the free tiers of Kling AI and Dreamina (Seedance 2.0).

It opens a hidden browser, uses saved cookies to bypass login, uploads the static 
AI fashion image, types a cinematic prompt, and downloads the generated video.
"""
import os
import sys
import asyncio
import time
from typing import Optional

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding, errors='replace'))
        except Exception:
            print('[Print Error] Unable to encode output print message.')

# Cookie files for the headless browser
KLING_COOKIE_FILE = os.path.expanduser("~/.kling_cookies.json")
DREAMINA_COOKIE_FILE = os.path.expanduser("~/.dreamina_cookies.json")

class VideoBridge:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.pw = None
        self.browser_session = None
        self.context = None
        self.output_dir = os.path.join(os.getcwd(), "output_ugc")
        os.makedirs(self.output_dir, exist_ok=True)

    def get_dreamina_cookie_files(self) -> list:
        files = []
        for i in range(1, 8):
            path = os.path.expanduser(f"~/.dreamina_cookies_{i}.json")
            if os.path.exists(path):
                files.append(path)
        default_path = os.path.expanduser("~/.dreamina_cookies.json")
        if os.path.exists(default_path) and default_path not in files:
            files.append(default_path)
        return files

    def get_kling_cookie_files(self) -> list:
        files = []
        for i in range(1, 8):
            path = os.path.expanduser(f"~/.kling_cookies_{i}.json")
            if os.path.exists(path):
                files.append(path)
        default_path = os.path.expanduser("~/.kling_cookies.json")
        if os.path.exists(default_path) and default_path not in files:
            files.append(default_path)
        return files

    async def start(self):
        from playwright.async_api import async_playwright
        import browser_helper
        self.pw_manager = async_playwright()
        self.pw = await self.pw_manager.__aenter__()
        self.browser_session = await browser_helper.get_browser_context(self.pw, headless=self.headless)
        self.context = self.browser_session.context
        self.browser = self.browser_session.browser

    async def stop(self):
        if self.browser_session:
            await self.browser_session.close()
        if hasattr(self, 'pw_manager') and self.pw_manager:
            await self.pw_manager.__aexit__(None, None, None)

    async def _load_context(self, cookie_file: str):
        import json
        if self.browser_session:
            if self.browser_session.is_cdp or self.browser_session.mode in ("LocalProfile", "Fallback"):
                if self.browser_session.mode == "Fallback" and os.path.exists(cookie_file):
                    try:
                        with open(cookie_file, "r") as f:
                            cookies = json.load(f)
                        await self.context.add_cookies(cookies)
                    except Exception as e:
                        safe_print(f"   [!] Failed to load cookies into fallback context: {e}")
                return self.context

        if self.browser and os.path.exists(cookie_file):
            return await self.browser.new_context(
                storage_state=cookie_file,
                viewport={"width": 1920, "height": 1080}
            )
        return self.context or await self.browser.new_context(viewport={"width": 1920, "height": 1080})

    async def generate_kling_video(self, image_path: str, prompt: str) -> Optional[str]:
        """
        Hijack Kling AI's free daily credits (Image-to-Video).
        Requires you to login manually once to save cookies.
        """
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            safe_print(f"🎬 [VideoBridge] Connecting to Kling AI (Attempt {attempt}/{max_retries})...")
            ctx = await self._load_context(KLING_COOKIE_FILE)
            page = await ctx.new_page()

            try:
                # Kling's generation page
                await page.goto("https://klingai.com/text-to-video/new", wait_until="networkidle", timeout=90000)
                await asyncio.sleep(5)
                
                # Handle region redirect to Chinese domain (Kuaishou)
                if "kuaishou.com" in page.url:
                    safe_print("   [!] Kling AI redirected to Chinese domain. Attempting migration to global site...")
                    migration_btn = page.locator("text=Go to klingai.com").or_(page.locator("a:has-text('Go to klingai.com')")).first
                    if await migration_btn.count() > 0:
                        await migration_btn.click()
                        await asyncio.sleep(5)
                    else:
                        await page.goto("https://klingai.com/text-to-video/new", wait_until="domcontentloaded", timeout=60000)
                        await asyncio.sleep(5)
                
                # Check if we need to login
                if "login" in page.url.lower() or await page.locator("text=Sign in").count() > 0 or await page.locator("text=Log In").count() > 0:
                    safe_print("   ⚠️ Not logged into Kling AI. You must run the login helper first.")
                    if attempt == max_retries:
                        return None
                    continue

                # Switch to Image to Video mode
                safe_print("   📸 Uploading image reference...")
                image_tab = page.locator('text="Image to Video"').or_(page.locator('div:has-text("Image to Video")')).first
                if await image_tab.count() > 0:
                    await image_tab.click()
                    await asyncio.sleep(2)

                # Upload Image
                file_input = page.locator('input[type="file"]')
                if await file_input.count() > 0:
                    await file_input.first.set_input_files(image_path)
                else:
                    upload_trigger = page.locator('.upload-icon, .upload-btn, [class*="upload"]').first
                    async with page.expect_file_chooser() as fc_info:
                        await upload_trigger.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(image_path)
                
                await asyncio.sleep(8) # wait for upload to complete

                # Type Prompt
                safe_print(f"   ✍️ Typing prompt: {prompt[:30]}...")
                prompt_box = page.locator('textarea[placeholder*="Describe"], textarea[placeholder*="describe"], textarea').first
                await prompt_box.fill(prompt)
                await asyncio.sleep(2)

                # Hit Generate
                safe_print("   🚀 Clicking Generate...")
                generate_btn = page.locator('button:has-text("Generate"), button[class*="generate"]').first
                await generate_btn.click()
                safe_print("   ⏳ Generation started! Waiting for rendering (this takes ~3-5 mins)...")

                # Wait for completion
                download_btn = page.locator('button[title="Download"], button:has-text("Download"), [class*="download"]').first
                
                # Wait up to 10 minutes for generation
                success = False
                for i in range(120):
                    await asyncio.sleep(5)
                    if await download_btn.is_visible():
                        safe_print("   ✅ Video rendered successfully!")
                        success = True
                        break
                    if i % 12 == 0:
                        safe_print("      ...still rendering...")

                if not success:
                    raise TimeoutError("Timed out waiting for download button on Kling AI.")

                # Download the video
                async with page.expect_download() as download_info:
                    await download_btn.click()
                download = await download_info.value
                
                output_filename = f"kling_ugc_{int(time.time())}.mp4"
                output_path = os.path.join(self.output_dir, output_filename)
                await download.save_as(output_path)
                safe_print(f"   💾 Saved to: {output_path}")
                return output_path

            except Exception as e:
                safe_print(f"   ❌ Kling AI Error on attempt {attempt}: {e}")
                try:
                    fail_screenshot = os.path.join(self.output_dir, f"kling_fail_attempt{attempt}_{int(time.time())}.png")
                    await page.screenshot(path=fail_screenshot)
                    safe_print(f"   📸 Failure screenshot saved: {fail_screenshot}")
                except Exception as se:
                    safe_print(f"   [-] Failed to capture screenshot: {se}")
                
                if attempt == max_retries:
                    return None
            finally:
                if self.browser_session and self.browser_session.is_cdp:
                    await page.close()
                else:
                    await ctx.close()

    async def generate_kling_video(self, image_path: str, prompt: str) -> Optional[str]:
        """
        Hijack Kling AI's free daily credits (Image-to-Video).
        Supports automatic cookie rotation across multiple accounts.
        """
        cookie_files = self.get_kling_cookie_files()
        if not cookie_files:
            safe_print("❌ [VideoBridge] No Kling cookie files found. Please run login_video.py first.")
            return None

        safe_print(f"🎬 [VideoBridge] Found {len(cookie_files)} Kling cookie files for rotation.")

        for cookie_file in cookie_files:
            safe_print(f"🎬 [VideoBridge] Attempting Kling generation with account: {os.path.basename(cookie_file)}")
            max_retries = 2
            for attempt in range(1, max_retries + 1):
                safe_print(f"   [Kling] Connecting (Attempt {attempt}/{max_retries})...")
                ctx = await self._load_context(cookie_file)
                page = await ctx.new_page()

                try:
                    # Kling's generation page
                    await page.goto("https://klingai.com/text-to-video/new", wait_until="networkidle", timeout=90000)
                    await asyncio.sleep(5)
                    
                    # Handle region redirect to Chinese domain (Kuaishou)
                    if "kuaishou.com" in page.url:
                        safe_print("   [!] Kling AI redirected to Chinese domain. Attempting migration to global site...")
                        migration_btn = page.locator("text=Go to klingai.com").or_(page.locator("a:has-text('Go to klingai.com')")).first
                        if await migration_btn.count() > 0:
                            await migration_btn.click()
                            await asyncio.sleep(5)
                        else:
                            await page.goto("https://klingai.com/text-to-video/new", wait_until="domcontentloaded", timeout=60000)
                            await asyncio.sleep(5)
                    
                    # Check if we need to login
                    if "login" in page.url.lower() or await page.locator("text=Sign in").count() > 0 or await page.locator("text=Log In").count() > 0:
                        safe_print(f"   ⚠️ Account {os.path.basename(cookie_file)} is not logged in or cookie expired. Trying next...")
                        break  # Try next cookie file
                    
                    # Switch to Image to Video mode
                    safe_print("   📸 Uploading image reference...")
                    image_tab = page.locator('text="Image to Video"').or_(page.locator('div:has-text("Image to Video")')).first
                    if await image_tab.count() > 0:
                        await image_tab.click()
                        await asyncio.sleep(2)

                    # Upload Image
                    file_input = page.locator('input[type="file"]')
                    if await file_input.count() > 0:
                        await file_input.first.set_input_files(image_path)
                    else:
                        upload_trigger = page.locator('.upload-icon, .upload-btn, [class*="upload"]').first
                        async with page.expect_file_chooser() as fc_info:
                            await upload_trigger.click()
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(image_path)
                    
                    await asyncio.sleep(8) # wait for upload to complete

                    safe_print(f"   ✍️ Typing prompt: {prompt[:30]}...")
                    prompt_box = page.locator('textarea[placeholder*="describe"], textarea[placeholder*="prompt"], textarea').first
                    await prompt_box.fill(prompt)
                    await asyncio.sleep(2)

                    # Hit Generate
                    safe_print("   🚀 Clicking Generate...")
                    generate_btn = page.locator('button:has-text("Generate"), button[class*="generate"]').first
                    await generate_btn.click()
                    
                    # Check for rate limit / out of points popup
                    await asyncio.sleep(3)
                    insufficient_points = page.locator("text=insufficient, text=not enough, text=limit, text=upgrade, text=points").first
                    if await insufficient_points.count() > 0 and await insufficient_points.is_visible():
                        safe_print(f"   ⚠️ Insufficient points/limit hit on account {os.path.basename(cookie_file)}. Trying next...")
                        break  # Try next cookie file

                    safe_print("   ⏳ Generation started! Waiting for rendering (~3-5 mins)...")

                    # Wait for download button to appear (indicating completion)
                    download_btn = page.locator('button:has-text("Download"), .download-btn, [class*="download"]').first
                    
                    # Wait up to 10 minutes
                    success = False
                    for i in range(120):
                        await asyncio.sleep(5)
                        if await download_btn.is_visible():
                            safe_print("   ✅ Video rendered successfully!")
                            success = True
                            break
                        if i % 12 == 0:
                            safe_print("      ...still rendering...")

                    if not success:
                        raise TimeoutError("Timed out waiting for download button on Kling AI.")

                    # Download the video
                    async with page.expect_download() as download_info:
                        await download_btn.click()
                    download = await download_info.value
                    
                    output_filename = f"kling_ugc_{int(time.time())}.mp4"
                    output_path = os.path.join(self.output_dir, output_filename)
                    await download.save_as(output_path)
                    safe_print(f"   💾 Saved to: {output_path}")
                    return output_path

                except Exception as e:
                    safe_print(f"   ❌ Kling AI Error on account {os.path.basename(cookie_file)}: {e}")
                    try:
                        fail_screenshot = os.path.join(self.output_dir, f"kling_fail_{os.path.basename(cookie_file)}_{int(time.time())}.png")
                        await page.screenshot(path=fail_screenshot)
                        safe_print(f"   📸 Failure screenshot saved: {fail_screenshot}")
                    except Exception as se:
                        safe_print(f"   [-] Failed to capture screenshot: {se}")
                    
                    if attempt == max_retries:
                        safe_print(f"   [-] Retries exhausted for {os.path.basename(cookie_file)}. Trying next account...")
                finally:
                    if self.browser_session and self.browser_session.is_cdp:
                        await page.close()
                    else:
                        await ctx.close()
        return None

    async def generate_dreamina_video(self, image_path: str, prompt: str) -> Optional[str]:
        """
        Hijack Dreamina (Seedance 2.0) free daily credits.
        Supports automatic cookie rotation across 7 accounts.
        """
        cookie_files = self.get_dreamina_cookie_files()
        if not cookie_files:
            safe_print("❌ [VideoBridge] No Dreamina cookie files found. Please run login_dreamina.py first.")
            return None

        safe_print(f"🎬 [VideoBridge] Found {len(cookie_files)} Dreamina cookie files for rotation.")

        for cookie_file in cookie_files:
            safe_print(f"🎬 [VideoBridge] Attempting Dreamina generation with account: {os.path.basename(cookie_file)}")
            max_retries = 2
            for attempt in range(1, max_retries + 1):
                safe_print(f"   [Dreamina] Connecting (Attempt {attempt}/{max_retries})...")
                ctx = await self._load_context(cookie_file)
                page = await ctx.new_page()

                try:
                    # Navigate directly to the video generation tool
                    await page.goto("https://dreamina.com/create/image-to-video", wait_until="domcontentloaded", timeout=90000)
                    await asyncio.sleep(5)
                    
                    # Check if login required
                    current_url = page.url
                    if "login" in current_url.lower() or await page.locator("text=Sign in").count() > 0 or await page.locator("text=Log in").count() > 0:
                        safe_print(f"   ⚠️ Account {os.path.basename(cookie_file)} is not logged in or cookie expired. Trying next...")
                        break  # Try next cookie file

                    safe_print("   📸 Uploading reference image...")
                    # Trigger file input
                    file_input = page.locator('input[type="file"]')
                    if await file_input.count() > 0:
                        await file_input.first.set_input_files(image_path)
                    else:
                        upload_trigger = page.locator('text="Upload"').or_(page.locator('text="Add Image"')).or_(page.locator('[class*="upload"]')).first
                        async with page.expect_file_chooser() as fc_info:
                            await upload_trigger.click()
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(image_path)
                        
                    await asyncio.sleep(8) # wait for upload to finish

                    safe_print(f"   ✍️ Typing prompt: {prompt[:30]}...")
                    # Locate text area for prompt
                    prompt_box = page.locator('textarea[placeholder*="describe"], textarea[placeholder*="vision"], textarea').first
                    await prompt_box.fill(prompt)
                    await asyncio.sleep(2)

                    # Hit Generate
                    safe_print("   🚀 Clicking Generate...")
                    generate_btn = page.locator('button:has-text("Generate"), button:has-text("Create"), button[class*="generate"]').first
                    await generate_btn.click()
                    
                    # Check for rate limit / out of points popup
                    await asyncio.sleep(3)
                    insufficient_points = page.locator("text=insufficient, text=not enough, text=limit, text=upgrade, text=points").first
                    if await insufficient_points.count() > 0 and await insufficient_points.is_visible():
                        safe_print(f"   ⚠️ Insufficient points/limit hit on account {os.path.basename(cookie_file)}. Trying next...")
                        break  # Try next cookie file

                    safe_print("   ⏳ Generation started! Waiting for rendering (this takes ~2-4 mins)...")

                    # Wait for download button to appear (indicating completion)
                    download_btn = page.locator('button[title*="Download"], button:has-text("Download"), .download-btn, [class*="download"]').first
                    
                    # Wait up to 8 minutes
                    success = False
                    for i in range(96):
                        await asyncio.sleep(5)
                        if await download_btn.is_visible():
                            safe_print("   ✅ Video rendered successfully!")
                            success = True
                            break
                        if i % 12 == 0:
                            safe_print("      ...still rendering...")

                    if not success:
                        raise TimeoutError("Timed out waiting for download button on Dreamina.")

                    # Download the video
                    safe_print("   📥 Downloading video...")
                    async with page.expect_download() as download_info:
                        await download_btn.click()
                    download = await download_info.value
                    
                    output_filename = f"dreamina_ugc_{int(time.time())}.mp4"
                    output_path = os.path.join(self.output_dir, output_filename)
                    await download.save_as(output_path)
                    safe_print(f"   💾 Saved to: {output_path}")
                    return output_path

                except Exception as e:
                    safe_print(f"   ❌ Dreamina Error on account {os.path.basename(cookie_file)}: {e}")
                    try:
                        fail_screenshot = os.path.join(self.output_dir, f"dreamina_fail_{os.path.basename(cookie_file)}_{int(time.time())}.png")
                        await page.screenshot(path=fail_screenshot)
                        safe_print(f"   📸 Failure screenshot saved: {fail_screenshot}")
                    except Exception as se:
                        safe_print(f"   [-] Failed to capture screenshot: {se}")
                    
                    if attempt == max_retries:
                        safe_print(f"   [-] Retries exhausted for {os.path.basename(cookie_file)}. Trying next account...")
                finally:
                    if self.browser_session and self.browser_session.is_cdp:
                        await page.close()
                    else:
                        await ctx.close()

async def test_bridge():
    bridge = VideoBridge(headless=False)
    await bridge.start()
    
    test_img = os.path.join(os.getcwd(), "test_image.png")
    if not os.path.exists(test_img):
        with open(test_img, "w") as f: f.write("dummy")
        
    await bridge.generate_kling_video(
        test_img, 
        "Cinematic slow motion, fashion editorial, walking down a neon-lit street"
    )
    
    await bridge.stop()

if __name__ == "__main__":
    asyncio.run(test_bridge())
