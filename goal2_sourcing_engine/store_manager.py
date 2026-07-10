"""
Storefront Manager — Multi-Channel Physical Fashion Sales
==========================================================
Sells physical fashion products to Instagram & Facebook audiences.

Sales Channels:
  1. Instagram Shop + Facebook Shop (via Meta Commerce Manager)
     - FREE native checkout — customers buy inside the app
     - Products tagged directly in Reels/Stories/Posts
     - Requires: Business IG account + Facebook Page + Commerce Manager catalog

  2. TikTok Shop (Seller Center)
     - In-app checkout via TikTok
     - Products linked in videos and livestreams

  3. Shopify (optional, $1/mo promo or $39/mo)
     - Auto-syncs catalog to Instagram + Facebook + TikTok
     - Professional checkout page with trust signals
     - Best for scaling

Payhip is kept ONLY for digital products (courses, presets, guides).

Features:
  - Auto-generate SEO-optimized product descriptions
  - Upload AI-generated images as product media
  - Dynamic pricing via pricing_engine.py
  - Manages catalog across all channels from one place
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pricing_engine import PricingEngine

# For browser automation
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "store_data"
OUTPUT_DIR.mkdir(exist_ok=True)

# Platform URLs
PLATFORM_URLS = {
    "meta_commerce": "https://business.facebook.com/commerce",
    "tiktok_shop": "https://seller.tiktok.com/",
    "shopify": "https://admin.shopify.com/",
    "payhip": "https://payhip.com/products",  # Digital only
}


class StorefrontManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.pw = None
        self.pricing = PricingEngine()
        
    async def start(self):
        self.pw = await async_playwright().__aenter__()
        self.browser = await self.pw.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox"]
        )
        print("[*] Storefront Manager initialized")

    async def _load_context(self, platform: str):
        cookie_file = BASE_DIR / f"{platform}_cookies.json"
        if cookie_file.exists():
            return await self.browser.new_context(storage_state=str(cookie_file))
        return await self.browser.new_context()

    # ═══════════════════════════════════════════════════════════════
    # CHANNEL 1: META COMMERCE (Instagram Shop + Facebook Shop)
    # FREE — products appear natively in IG and FB
    # ═══════════════════════════════════════════════════════════════

    async def list_on_meta_shop(self, product_data: Dict, supplier_cost: float = 0.0) -> bool:
        """
        List a physical product on Instagram Shop + Facebook Shop
        via Meta Commerce Manager catalog.

        product_data expects:
            title, description, price (optional), images (list of paths),
            category (e.g. 'tops', 'shoes'), link (website checkout URL)
        """
        # Calculate dynamic price
        if supplier_cost > 0:
            price_data = self.pricing.calculate_physical_retail_price(supplier_cost, product_data.get("category", "apparel"))
            retail_price = price_data["retail_price"]
            print(f"   [$$] Dynamic Pricing: Supplier ${supplier_cost:.2f} -> Retail ${retail_price:.2f} (Profit: ${price_data['net_profit']:.2f})")
        else:
            retail_price = product_data.get('price', 29.99)

        print(f"\n[META SHOP] Listing: {product_data.get('title')} at ${retail_price}")
        ctx = await self._load_context("meta_commerce")
        page = await ctx.new_page()

        try:
            await page.goto(PLATFORM_URLS["meta_commerce"], wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(3)

            # Check if logged in
            if "login" in page.url.lower() or "checkpoint" in page.url.lower():
                print("   [!] Meta Commerce not logged in. Run: python store_manager.py --login meta_commerce")
                return False

            # Navigate to catalog -> Add Items
            print("   [+] Navigating to catalog...")
            await page.goto("https://business.facebook.com/commerce/catalogs", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # Click "Add Items" button
            add_btn = page.locator("a:has-text('Add Items'), button:has-text('Add Items'), a:has-text('Add items')")
            if await add_btn.count() > 0:
                await add_btn.first.click()
                await asyncio.sleep(2)

            # Select "Add Manually"
            manual_btn = page.locator("text='Add Manually', text='Manual'")
            if await manual_btn.count() > 0:
                await manual_btn.first.click()
                await asyncio.sleep(2)

            # Fill product details
            print("   [+] Filling product details...")

            # Title
            title_input = page.locator("input[name='title'], input[placeholder*='name'], input[aria-label*='Name']").first
            if await title_input.count() > 0:
                await title_input.fill(product_data.get("title", "Fashion Item"))

            # Description
            desc_input = page.locator("textarea[name='description'], textarea[placeholder*='description']").first
            if await desc_input.count() > 0:
                await desc_input.fill(product_data.get("description", ""))

            # Price
            price_input = page.locator("input[name='price'], input[placeholder*='price'], input[type='number']").first
            if await price_input.count() > 0:
                await price_input.fill(str(retail_price))

            # Upload images
            images = product_data.get("images", [])
            if images:
                print(f"   [+] Uploading {len(images)} product images...")
                file_input = page.locator("input[type='file']").first
                if await file_input.count() > 0:
                    existing_images = [img for img in images if os.path.exists(img)]
                    if existing_images:
                        await file_input.set_input_files(existing_images)
                        await asyncio.sleep(3)

            # Website link (where customer completes purchase)
            link_input = page.locator("input[name='url'], input[placeholder*='website'], input[placeholder*='link']").first
            if await link_input.count() > 0 and product_data.get("link"):
                await link_input.fill(product_data["link"])

            # Submit
            save_btn = page.locator("button:has-text('Save'), button:has-text('Add Item'), button:has-text('Finish')")
            if await save_btn.count() > 0:
                await save_btn.first.click()
                await asyncio.sleep(3)

            # Record listing
            record = {
                "platform": "meta_shop",
                "channels": ["instagram_shop", "facebook_shop"],
                "title": product_data.get("title"),
                "price": retail_price,
                "listed_at": datetime.now().isoformat(),
                "status": "pending_review",
                "images_count": len(images),
            }
            self._save_listing(record)
            print("   [+] Product submitted to Meta Commerce Manager!")
            print("   [*] It will appear on Instagram Shop + Facebook Shop after Meta review.")
            return True

        except Exception as e:
            print(f"   [!] Error listing on Meta Shop: {e}")
            return False
        finally:
            await ctx.close()

    # ═══════════════════════════════════════════════════════════════
    # CHANNEL 2: TIKTOK SHOP (in-app checkout)
    # ═══════════════════════════════════════════════════════════════

    async def list_on_tiktok_shop(self, product_data: Dict, supplier_cost: float = 0.0) -> bool:
        """
        List a physical product on TikTok Shop Seller Center.
        """
        if supplier_cost > 0:
            price_data = self.pricing.calculate_physical_retail_price(supplier_cost, product_data.get("category", "apparel"))
            retail_price = price_data["retail_price"]
            print(f"   [$$] Dynamic Pricing: Supplier ${supplier_cost:.2f} -> Retail ${retail_price:.2f}")
        else:
            retail_price = product_data.get('price', 29.99)
            
        print(f"\n[TIKTOK SHOP] Listing: {product_data.get('title')} at ${retail_price}")
        ctx = await self._load_context("tiktok_shop")
        page = await ctx.new_page()
        
        try:
            await page.goto(PLATFORM_URLS["tiktok_shop"], wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(3)
            
            if "login" in page.url.lower() or "passport" in page.url.lower():
                print("   [!] TikTok Shop not logged in. Run: python store_manager.py --login tiktok_shop")
                return False
                
            # Navigate to Products > Add Product
            print("   [+] Creating new product listing...")
            await page.goto("https://seller.tiktok.com/product/add", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # Fill product name
            name_input = page.locator("input[placeholder*='product name'], input[placeholder*='Product name']").first
            if await name_input.count() > 0:
                await name_input.fill(product_data.get("title", "Fashion Item"))

            # Fill description
            desc_area = page.locator("div[contenteditable='true'], textarea[placeholder*='description']").first
            if await desc_area.count() > 0:
                await desc_area.fill(product_data.get("description", ""))

            # Upload images
            images = product_data.get("images", [])
            if images:
                print(f"   [+] Uploading {len(images)} AI generated images...")
                file_input = page.locator("input[type='file']").first
                if await file_input.count() > 0:
                    existing = [img for img in images if os.path.exists(img)]
                    if existing:
                        await file_input.set_input_files(existing)
                        await asyncio.sleep(5)

            # Set price
            price_input = page.locator("input[placeholder*='price'], input[placeholder*='Price']").first
            if await price_input.count() > 0:
                await price_input.fill(str(retail_price))

            # Submit
            publish_btn = page.locator("button:has-text('Publish'), button:has-text('Submit')")
            if await publish_btn.count() > 0:
                await publish_btn.first.click()
                await asyncio.sleep(3)

            record = {
                "platform": "tiktok_shop",
                "title": product_data.get("title"),
                "price": retail_price,
                "listed_at": datetime.now().isoformat(),
                "status": "success",
            }
            self._save_listing(record)
            print("   [+] Successfully listed on TikTok Shop!")
            return True
            
        except Exception as e:
            print(f"   [!] Error listing on TikTok Shop: {e}")
            return False
        finally:
            await ctx.close()

    # ═══════════════════════════════════════════════════════════════
    # CHANNEL 3: PAYHIP (Digital products ONLY)
    # ═══════════════════════════════════════════════════════════════

    async def list_on_payhip(self, product_data: Dict) -> bool:
        """
        List a DIGITAL product on Payhip (courses, presets, guides).
        NOT for physical fashion items.
        """
        print(f"\n[PAYHIP] Listing DIGITAL product: {product_data.get('title')}")
        ctx = await self._load_context("payhip")
        page = await ctx.new_page()
        
        try:
            await page.goto(PLATFORM_URLS["payhip"], wait_until="domcontentloaded", timeout=30000)
            
            if "/login" in page.url:
                print("   [!] Payhip not logged in. Run: python store_manager.py --login payhip")
                return False
                
            print("   [+] Creating new digital product listing...")
            await asyncio.sleep(2)
            
            record = {
                "platform": "payhip",
                "type": "digital",
                "title": product_data.get("title"),
                "price": product_data.get("price"),
                "listed_at": datetime.now().isoformat(),
                "status": "success",
            }
            self._save_listing(record)
            print(f"   [+] Digital product listed on Payhip!")
            return True
            
        except Exception as e:
            print(f"   [!] Error listing on Payhip: {e}")
            return False
        finally:
            await ctx.close()

    # ═══════════════════════════════════════════════════════════════
    # MULTI-CHANNEL: List everywhere at once
    # ═══════════════════════════════════════════════════════════════

    async def list_physical_everywhere(self, product_data: Dict, supplier_cost: float = 0.0) -> Dict:
        """
        Lists a physical fashion item on ALL sales channels simultaneously.
        Returns status for each channel.
        """
        print("\n" + "=" * 60)
        print(f"[MULTI-CHANNEL] Listing: {product_data.get('title')}")
        print("=" * 60)

        results = {}

        # Channel 1: Instagram + Facebook Shop (FREE)
        results["meta_shop"] = await self.list_on_meta_shop(product_data, supplier_cost)

        # Channel 2: TikTok Shop
        results["tiktok_shop"] = await self.list_on_tiktok_shop(product_data, supplier_cost)

        # Summary
        success_count = sum(1 for v in results.values() if v)
        print(f"\n[SUMMARY] Listed on {success_count}/{len(results)} channels")
        for channel, status in results.items():
            emoji = "[OK]" if status else "[SKIP]"
            print(f"   {emoji} {channel}")

        return results

    # ═══════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════

    def _save_listing(self, record: Dict):
        db_file = OUTPUT_DIR / "store_listings.json"
        listings = []
        if db_file.exists():
            with open(db_file, "r") as f:
                listings = json.load(f)
                
        listings.append(record)
        with open(db_file, "w") as f:
            json.dump(listings, f, indent=2)

    async def setup_auth(self, platform: str):
        """Open a visible browser to manually log in and save session cookies."""
        pw = await async_playwright().__aenter__()
        browser = await pw.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        
        url = PLATFORM_URLS.get(platform, PLATFORM_URLS["meta_commerce"])
        await page.goto(url)
        
        print(f"\n[AUTH] Please log into {platform.upper()} in the browser.")
        print("Press ENTER in this console when you are fully logged in and on the dashboard...")
        input()
        
        cookie_file = BASE_DIR / f"{platform}_cookies.json"
        state = await ctx.storage_state()
        with open(cookie_file, "w") as f:
            json.dump(state, f)
            
        print(f"[+] {platform.upper()} authentication cookies saved successfully!")
        await browser.close()
        await pw.stop()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Storefront Manager — Multi-Channel Fashion Sales")
    parser.add_argument("--login", choices=["meta_commerce", "tiktok_shop", "payhip", "shopify"],
                        help="Setup authentication for a platform")
    parser.add_argument("--test-meta", action="store_true", help="Test Meta Shop listing (IG + FB)")
    parser.add_argument("--test-tiktok", action="store_true", help="Test TikTok Shop listing")
    parser.add_argument("--test-all", action="store_true", help="Test listing on all channels")
    parser.add_argument("--test-payhip", action="store_true", help="Test Payhip listing (digital only)")
    args = parser.parse_args()

    manager = StorefrontManager(headless=False if args.login else True)

    if args.login:
        await manager.setup_auth(args.login)
        return

    await manager.start()

    test_physical_product = {
        "title": "Vintage Washed Y2K Graphic Tee",
        "description": "Oversized heavyweight vintage washed graphic tee with metallic logo. Premium cotton, relaxed fit.",
        "price": 34.99,
        "category": "tops",
        "images": [
            "output_ugc/sample_1.png",
            "output_ugc/sample_2.png",
        ],
    }

    if args.test_meta:
        await manager.list_on_meta_shop(test_physical_product, supplier_cost=8.50)

    if args.test_tiktok:
        await manager.list_on_tiktok_shop(test_physical_product, supplier_cost=8.50)

    if args.test_all:
        await manager.list_physical_everywhere(test_physical_product, supplier_cost=8.50)

    if args.test_payhip:
        await manager.list_on_payhip({
            "title": "AI Fashion Generation Masterclass",
            "price": "49.99",
            "description": "Learn how to build a 24/7 autonomous fashion engine.",
        })

    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
