"""
Social Auto-Poster v2 — Browser Automation (Zero API Keys)
==========================================================
Posts content to TikTok, Instagram, and Pinterest using Playwright
browser automation instead of official API tokens.

Supports:
  - Single video posts (TikTok, Instagram Reels)
  - Photo carousels (Instagram, Pinterest)
  - Scheduled posting via cron
  - Caption + hashtag injection

For platforms that DO have free API access (X/Twitter), we keep the API path.
For platforms that DON'T (TikTok, Instagram), we use browser automation.
"""
import os
import asyncio
import time
from typing import List, Optional, Union

# ==========================================
# CONFIGURATION
# ==========================================
TIKTOK_COOKIE_FILE = os.path.expanduser("~/.tiktok_cookies.json")
IG_COOKIE_FILE = os.path.expanduser("~/.ig_cookies.json")
PINTEREST_COOKIE_FILE = os.path.expanduser("~/.pinterest_cookies.json")

# Default hashtag sets by product type
HASHTAGS = {
    "clothing": "#fashion #ootd #streetwear #outfitinspo #tiktokmademebuyit #grwm",
    "shoes": "#sneakers #kicks #shoegame #sneakerhead #newshoes #footwear",
    "accessories": "#jewelry #watch #sunglasses #accessories #luxury #style",
    "beauty": "#skincare #perfume #beauty #glowup #selfcare #fragrance",
    "default": "#trending #viral #fyp #foryou #musthave",
}


class SocialPoster:
    """Browser-based social media poster using Playwright."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.pw = None

    async def start(self):
        pass # Replaced by CloakBrowser persistent contexts

    async def _load_context(self, cookie_id: str, cookie_file: str):
        """Create a browser context using CloakBrowser."""
        import cloakbrowser
        return await cloakbrowser.launch_persistent_context_async(
            user_data_dir=os.path.dirname(cookie_file) + f"/cloak_{cookie_id}",
            headless=self.headless,
            viewport={"width": 1920, "height": 1080}
        )

    async def _save_cookies(self, context, cookie_file: str):
        state = await context.storage_state()
        import json
        with open(cookie_file, "w") as f:
            json.dump(state, f)

    # ==========================================
    # TIKTOK — Browser Upload
    # ==========================================
    async def post_to_tiktok(
        self,
        media_path: str,
        caption: str,
        product_type: str = "default"
    ) -> bool:
        """
        Upload a video to TikTok via the web uploader.
        Uses tiktok.com/upload (Creator Center).
        """
        print(f"📱 [TikTok] Posting: {os.path.basename(media_path)}")
        ctx = await self._load_context("tiktok", TIKTOK_COOKIE_FILE)
        page = await ctx.new_page() if len(ctx.pages) == 0 else ctx.pages[0]

        try:
            await page.goto("https://www.tiktok.com/upload", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            # Check if logged in
            if "login" in page.url.lower():
                print("   ⚠️  Not logged in to TikTok. Run login flow first.")
                await ctx.close()
                return False

            # Upload the video file
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(media_path)
            await asyncio.sleep(5)
            print("   📎 Video uploaded, waiting for processing...")

            # Wait for upload to complete
            await asyncio.sleep(10)

            # Type the caption + hashtags
            hashtags = HASHTAGS.get(product_type, HASHTAGS["default"])
            full_caption = f"{caption}\n\n{hashtags}"

            caption_input = page.locator('[data-placeholder*="caption"]').or_(
                page.locator('[contenteditable="true"]').first
            )
            await caption_input.click()
            await caption_input.fill(full_caption)
            await asyncio.sleep(1)

            # Click Post
            post_btn = page.locator('button:has-text("Post")').or_(
                page.locator('[data-e2e="upload-btn"]')
            )
            await post_btn.first.click()
            await asyncio.sleep(5)

            print("   ✅ [TikTok] Posted successfully!")
            await self._save_cookies(ctx, TIKTOK_COOKIE_FILE)
            return True

        except Exception as e:
            print(f"   ❌ [TikTok] Failed: {e}")
            return False
        finally:
            await ctx.close()

    # ==========================================
    # INSTAGRAM — Browser Upload
    # ==========================================
    async def post_to_instagram(
        self,
        media_paths: Union[str, List[str]],
        caption: str,
        product_type: str = "default"
    ) -> bool:
        """
        Post to Instagram via the web interface.
        Supports both single image/video and carousel (multiple images).
        """
        is_carousel = isinstance(media_paths, list)
        print(f"📸 [Instagram] Posting: {'Carousel' if is_carousel else 'Single'}")

        ctx = await self._load_context("instagram", IG_COOKIE_FILE)
        page = await ctx.new_page()

        try:
            await page.goto("https://www.instagram.com/", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            if "login" in page.url.lower():
                print("   ⚠️  Not logged in to Instagram. Run login flow first.")
                await ctx.close()
                return False

            # Click the "Create" / "+" button
            create_btn = page.locator('[aria-label="New post"]').or_(
                page.locator('svg[aria-label="New post"]')
            ).or_(page.locator('[aria-label="Create"]'))
            await create_btn.first.click()
            await asyncio.sleep(2)

            # Upload file(s)
            file_input = page.locator('input[type="file"]')
            if is_carousel:
                await file_input.set_input_files(media_paths)
            else:
                await file_input.set_input_files(media_paths)
            await asyncio.sleep(3)

            # Click through the creation flow: Next → Next → Share
            for _ in range(2):
                next_btn = page.locator('button:has-text("Next")').or_(
                    page.locator('[aria-label="Next"]')
                )
                if await next_btn.count() > 0:
                    await next_btn.first.click()
                    await asyncio.sleep(2)

            # Type caption
            hashtags = HASHTAGS.get(product_type, HASHTAGS["default"])
            full_caption = f"{caption}\n\n{hashtags}"
            caption_input = page.locator('textarea[aria-label*="caption"]').or_(
                page.locator('[aria-label="Write a caption..."]')
            )
            if await caption_input.count() > 0:
                await caption_input.first.fill(full_caption)
                await asyncio.sleep(1)

            # Click Share
            share_btn = page.locator('button:has-text("Share")').or_(
                page.locator('[aria-label="Share"]')
            )
            await share_btn.first.click()
            await asyncio.sleep(5)

            print("   ✅ [Instagram] Posted successfully!")
            await self._save_cookies(ctx, IG_COOKIE_FILE)
            return True

        except Exception as e:
            print(f"   ❌ [Instagram] Failed: {e}")
            return False
        finally:
            await ctx.close()

    # ==========================================
    # PINTEREST — Browser Upload
    # ==========================================
    async def post_to_pinterest(
        self,
        image_path: str,
        title: str,
        description: str,
        link: str = "",
        board: str = ""
    ) -> bool:
        """Post a pin to Pinterest via the web interface."""
        print(f"📌 [Pinterest] Posting: {title[:40]}...")
        ctx = await self._load_context("pinterest", PINTEREST_COOKIE_FILE)
        page = await ctx.new_page()
        page = await ctx.new_page()

        try:
            await page.goto("https://www.pinterest.com/pin-builder/", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            if "login" in page.url.lower():
                print("   ⚠️  Not logged in to Pinterest. Run login flow first.")
                await ctx.close()
                return False

            # Upload image
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(image_path)
            await asyncio.sleep(3)

            # Fill in title
            title_input = page.locator('input[id="pin-draft-title"]').or_(
                page.locator('[placeholder*="title"]')
            )
            if await title_input.count() > 0:
                await title_input.first.fill(title)

            # Fill in description
            desc_input = page.locator('textarea').or_(
                page.locator('[placeholder*="description"]')
            )
            if await desc_input.count() > 0:
                await desc_input.first.fill(description)

            # Add link
            if link:
                link_input = page.locator('input[placeholder*="link"]').or_(
                    page.locator('[id*="link"]')
                )
                if await link_input.count() > 0:
                    await link_input.first.fill(link)

            # Publish
            publish_btn = page.locator('button:has-text("Publish")').or_(
                page.locator('[data-test-id="board-dropdown-save-button"]')
            )
            await publish_btn.first.click()
            await asyncio.sleep(3)

            print("   ✅ [Pinterest] Pinned successfully!")
            await self._save_cookies(ctx, PINTEREST_COOKIE_FILE)
            return True

        except Exception as e:
            print(f"   ❌ [Pinterest] Failed: {e}")
            return False
        finally:
            await ctx.close()

    # ==========================================
    # LOGIN HELPERS
    # ==========================================
    async def login_platform(self, platform: str):
        """Open a visible browser for manual login. Run once per platform."""
        urls = {
            "tiktok": ("https://www.tiktok.com/login", TIKTOK_COOKIE_FILE),
            "instagram": ("https://www.instagram.com/accounts/login/", IG_COOKIE_FILE),
            "pinterest": ("https://www.pinterest.com/login/", PINTEREST_COOKIE_FILE),
        }

        if platform not in urls:
            print(f"Unknown platform: {platform}")
            return

        url, cookie_file = urls[platform]
        from playwright.async_api import async_playwright
        pw = await async_playwright().__aenter__()
        browser = await pw.chromium.launch(headless=False, slow_mo=500)
        ctx = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await ctx.new_page()
        await page.goto(url)

        print(f"\n🔐 Log into {platform.title()} in the browser window.")
        print("   Press ENTER here after you're logged in...")
        input()

        state = await ctx.storage_state()
        import json
        with open(cookie_file, "w") as f:
            json.dump(state, f)
        print(f"   ✅ {platform.title()} cookies saved to {cookie_file}")

        await browser.close()
        await pw.stop()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()


# ==========================================
# CONVENIENCE FUNCTION (backward compatible)
# ==========================================
def distribute_content(
    video_url: Union[str, List[str]],
    caption: str,
    product_link: str,
    product_type: str = "default",
    is_merged_outfit: bool = False
):
    """
    Main distribution function — backward compatible with sourcing_engine.py.
    Accepts either a video path or list of image paths (carousel).
    """
    async def _distribute():
        poster = SocialPoster(headless=True)
        await poster.start()

        is_carousel = isinstance(video_url, list)

        if is_merged_outfit:
            # Post to TikTok (video only)
            if not is_carousel and os.path.exists(str(video_url)):
                tiktok_caption = f"{caption} Link in Bio: {product_link} #outfit"
                await poster.post_to_tiktok(video_url, tiktok_caption, product_type)

            # Post to Instagram (carousel or single)
            ig_caption = f"{caption}\n\nGet yours: {product_link}"
            await poster.post_to_instagram(video_url, ig_caption, product_type)
        else:
            print("   ℹ️ Skipping TikTok/IG (Item is a basic solo product, not a Merged Outfit)")

        # Always Post to Pinterest (Catalog/Moodboard)
        pin_img = video_url[0] if is_carousel else video_url
        if os.path.exists(str(pin_img)):
            await poster.post_to_pinterest(
                image_path=pin_img,
                title=caption[:100],
                description=f"{caption}\n\nShop now: {product_link}",
                link=product_link
            )

        await poster.close()
        print("\n🎉 Social Distribution Complete!")

    asyncio.run(_distribute())


# ==========================================
# CLI
# ==========================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        platform = sys.argv[2] if len(sys.argv) > 2 else "tiktok"
        poster = SocialPoster()
        asyncio.run(poster.login_platform(platform))
    else:
        # Test
        distribute_content(
            video_url="output/generated/test_video.mp4",
            caption="This new hoodie just changed my wardrobe game 🔥",
            product_link="https://store.ko.fa/hoodie-001",
            product_type="clothing"
        )
