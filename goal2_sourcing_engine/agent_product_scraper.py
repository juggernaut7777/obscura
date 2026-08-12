"""
Agent Platform Product Scraper — USFans / CNFans / CSSBuy
==========================================================
Scrapes trending and new products from Chinese agent platforms
using Playwright browser automation (Zero API).

Extracts: product name, price, image URL, agent link, category
Outputs JSON catalog for the ad generation pipeline.

Usage:
  python agent_product_scraper.py                    # Scrape all platforms
  python agent_product_scraper.py --platform usfans  # Scrape specific platform
  python agent_product_scraper.py --category shoes   # Scrape specific category
"""
import os
import json
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Optional

OUTPUT_DIR = os.path.join(os.getcwd(), "output", "scraped_products")
INPUT_SOURCING_DIR = os.path.join(os.getcwd(), "input_sourcing")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(INPUT_SOURCING_DIR, exist_ok=True)

# ==========================================
# PLATFORM CONFIGURATIONS
# ==========================================
PLATFORMS = {
    "usfans": {
        "name": "USFans",
        "base_url": "https://www.usfans.com",
        "search_url": "https://www.usfans.com/search?keyword={query}",
        "trending_url": "https://www.usfans.com/trending",
        "cookie_file": os.path.expanduser("~/.usfans_cookies.json"),
    },
    "cnfans": {
        "name": "CNFans",
        "base_url": "https://www.cnfans.com",
        "search_url": "https://www.cnfans.com/search?keyword={query}",
        "trending_url": "https://www.cnfans.com/trending",
        "cookie_file": os.path.expanduser("~/.cnfans_cookies.json"),
    },
    "cssbuy": {
        "name": "CSSBuy",
        "base_url": "https://www.cssbuy.com",
        "search_url": "https://www.cssbuy.com/search?keyword={query}",
        "trending_url": "https://www.cssbuy.com/trending",
        "cookie_file": os.path.expanduser("~/.cssbuy_cookies.json"),
    },
}

# Categories to scrape (maps to agent platform search terms)
SCRAPE_CATEGORIES = {
    "shoes": [
        "chunky platform sneaker", "archive combat boots", "black leather mules",
        "designer distressed sneaker", "opium style boots",
    ],
    "hoodies": [
        "heavyweight washed hoodie", "vintage zip up hoodie", "distressed hoodie",
        "acid wash zip up", "oversized black hoodie", "gothic graphic hoodie"
    ],
    "tshirts": [
        "washed vintage graphic tee", "oversized heavyweight tee", "box fit shirt",
        "distressed t-shirt", "minimalist luxury blank tee",
    ],
    "pants": [
        "flared cargo pants", "washed black baggy jeans", "parachute pants",
        "multi pocket techwear pants", "distressed denim wide leg",
    ],
    "jackets": [
        "distressed bomber jacket", "faux leather racing jacket", "cropped black puffer",
        "vintage washed denim jacket", "techwear windbreaker",
    ],
    "accessories": [
        "silver chain necklace", "studded designer belt", "balaclava",
        "chunky silver ring", "crossbody tactical bag", "shield sunglasses",
    ],
}


class AgentPlatformScraper:
    """Scrapes product listings from Chinese agent platforms."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.pw = None
        self.all_products: List[Dict] = []
        self.session = None
        self.validator = None  # Gemini visual validator

    async def start(self):
        from playwright.async_api import async_playwright
        self.pw = await async_playwright().__aenter__()
        self.browser = await self.pw.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox"]
        )
        import aiohttp
        self.session = aiohttp.ClientSession()
        
        # Init Gemini Visual Validator
        # gemini-3.1-flash-lite = 500 RPD per key, 15 RPM
        # With 2 keys = 1000 RPD total
        try:
            import google.generativeai as genai
            from dotenv import load_dotenv
            load_dotenv()
            self.gemini_keys = []
            key1 = os.getenv("GEMINI_API_KEY")
            key2 = os.getenv("GEMINI_API_KEY_2")
            if key1: self.gemini_keys.append(key1)
            if key2: self.gemini_keys.append(key2)
            
            if self.gemini_keys:
                # Start with key 2 if available (spreads usage)
                self._current_key_idx = min(1, len(self.gemini_keys) - 1)
                genai.configure(api_key=self.gemini_keys[self._current_key_idx])
                self.validator = genai.GenerativeModel('gemini-2.5-flash-lite')
                print(f"[+] Gemini Validator: gemini-2.5-flash-lite ({len(self.gemini_keys)} keys, using key #{self._current_key_idx + 1})")
            else:
                print("[!] No GEMINI_API_KEY found, validation disabled")
        except Exception as e:
            print(f"[!] Gemini init failed: {e}")

    def _rotate_key(self):
        """Switch to the next API key when rate limited."""
        import google.generativeai as genai
        self._current_key_idx = (self._current_key_idx + 1) % len(self.gemini_keys)
        genai.configure(api_key=self.gemini_keys[self._current_key_idx])
        self.validator = genai.GenerativeModel('gemini-2.5-flash-lite')
        print(f"      [KEY] Rotated to key #{self._current_key_idx + 1}")

    async def validate_product(self, image_path: str, title: str, category: str) -> dict:
        """
        Triple-Check Truth Detector:
        Sends the downloaded image + seller's title + expected category to Gemini.
        Returns {'valid': True/False, 'reason': '...', 'detected_gender': 'male/female'}
        """
        if not self.validator or not os.path.exists(image_path):
            return {"valid": True, "reason": "No validator", "detected_gender": "unknown"}
        
        try:
            from PIL import Image
            img = Image.open(image_path)
            
            prompt = f"""You are a fashion product quality control expert.

The seller listed this product as: "{title}"
Expected category: "{category}"

Look at this image and answer these questions:
1. Does this image actually show the product described in the title? (YES/NO)
2. Is this a real, high-quality product photo suitable for an editorial fashion shoot? (YES/NO)
3. What gender is this product for? (male/female/unisex)
4. What type of garment/item is it? (shoe/top/bottom/outerwear/accessory/NOT_FASHION)

Return ONLY a JSON object:
{{"match": true/false, "quality": true/false, "gender": "male/female/unisex", "type": "shoe/top/bottom/outerwear/accessory", "reason": "brief explanation"}}

REJECT if: the image is a screenshot, a cloud, a landscape, blurry, low-res, not fashion, or doesn't match the title."""

            # Try with key rotation on rate limit
            response = None
            for attempt in range(len(self.gemini_keys)):
                try:
                    response = self.validator.generate_content([prompt, img])
                    break
                except Exception as rate_err:
                    if "429" in str(rate_err) and len(self.gemini_keys) > 1:
                        self._rotate_key()
                    else:
                        raise rate_err
            
            if not response:
                return {"valid": False, "reason": "All keys exhausted"}
            
            text = response.text.strip()
            
            import json as json_mod
            # Try to parse JSON from response
            try:
                result = json_mod.loads(text)
            except ValueError:
                import re as re_mod
                match = re_mod.search(r'\{.*\}', text, re_mod.DOTALL)
                if match:
                    result = json_mod.loads(match.group(0))
                else:
                    return {"valid": False, "reason": f"Unparseable: {text[:100]}"}
            
            is_valid = result.get("match", False) and result.get("quality", False)
            return {
                "valid": is_valid,
                "reason": result.get("reason", ""),
                "detected_gender": result.get("gender", "unknown"),
                "detected_type": result.get("type", "unknown")
            }
            
        except Exception as e:
            print(f"      [!] Validation error: {e}")
            return {"valid": True, "reason": f"Error: {e}", "detected_gender": "unknown"}

    async def _load_context(self, cookie_file: str):
        if os.path.exists(cookie_file):
            return await self.browser.new_context(storage_state=cookie_file)
        return await self.browser.new_context()

    async def scrape_platform(
        self,
        platform_key: str,
        categories: Optional[List[str]] = None,
        max_per_category: int = 10
    ) -> List[Dict]:
        """
        Scrape products from a specific agent platform.
        """
        platform = PLATFORMS.get(platform_key)
        if not platform:
            print(f"[!] Unknown platform: {platform_key}")
            return []

        print(f"\n[>>] Scraping {platform['name']}...")
        ctx = await self._load_context(platform["cookie_file"])
        page = await ctx.new_page()
        products = []

        cats = categories or list(SCRAPE_CATEGORIES.keys())

        for cat_name in cats:
            keywords = SCRAPE_CATEGORIES.get(cat_name, [cat_name])
            for keyword in keywords[:2]:  # Limit to 2 keywords per category
                try:
                    search_url = platform["search_url"].format(query=keyword.replace(" ", "+"))
                    print(f"   [*] Searching: '{keyword}'...")
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(5000)

                    # Extract product cards from the page
                    page_products = await self._extract_products(page, platform_key, cat_name)
                    products.extend(page_products[:max_per_category])

                    print(f"      Found {len(page_products)} products")
                    await asyncio.sleep(2)  # Rate limiting

                except Exception as e:
                    print(f"      [!] Error scraping '{keyword}': {e}")
                    continue

        await ctx.close()
        print(f"   [+] {platform['name']}: {len(products)} products scraped")
        return products

    async def _extract_products(
        self, page, platform_key: str, category: str
    ) -> List[Dict]:
        """
        Extract product data from the current page.
        Tries multiple CSS selectors to handle different platform layouts.
        """
        products = []

        # Common selectors for agent platform product cards
        selectors = [
            ".product-card", ".goods-item", ".search-item",
            "[class*='product']", "[class*='goods']", ".item-card",
            ".product-list-item", ".search-result-item"
        ]

        for selector in selectors:
            cards = await page.query_selector_all(selector)
            if cards:
                for card in cards[:15]:
                    try:
                        product = await self._parse_product_card(
                            card, platform_key, category
                        )
                        if product:
                            products.append(product)
                    except Exception:
                        continue
                break

        # Fallback: extract from page content if no cards found
        if not products:
            products = await self._fallback_extract(page, platform_key, category)

        return products

    async def _parse_product_card(
        self, card, platform_key: str, category: str
    ) -> Optional[Dict]:
        """Parse a single product card element."""
        # Try to extract title
        title_el = await card.query_selector(
            "h3, h4, .title, .name, [class*='title'], [class*='name'], a"
        )
        title = await title_el.inner_text() if title_el else ""
        title = title.strip()[:100]

        if not title or len(title) < 3:
            return None

        # Try to extract price
        price_el = await card.query_selector(
            ".price, [class*='price'], span[class*='amount']"
        )
        price_text = await price_el.inner_text() if price_el else "0"
        price = self._parse_price(price_text)

        # Try to extract image
        img_el = await card.query_selector("img")
        img_url = ""
        if img_el:
            img_url = (await img_el.get_attribute("src") or
                       await img_el.get_attribute("data-src") or "")

        # Try to extract link
        link_el = await card.query_selector("a")
        product_url = ""
        if link_el:
            href = await link_el.get_attribute("href") or ""
            if href.startswith("/"):
                product_url = PLATFORMS[platform_key]["base_url"] + href
            elif href.startswith("http"):
                product_url = href

        # Detect Gender (initial guess from text)
        gender = "female" # Default
        male_keywords = ["men", "male", "man", "his", "m1", "m2", "boy"]
        if any(mk in title.lower() or mk in category.lower() for mk in male_keywords):
            gender = "male"

        # Download Image
        local_path = ""
        if img_url:
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:30]
            filename = f"{gender}_{category}_{safe_title}_{int(datetime.now().timestamp())}.png"
            local_path = os.path.join(INPUT_SOURCING_DIR, filename)
            success = await self._download_image(img_url, local_path)
            if not success:
                local_path = ""

        # === TRUTH DETECTOR: Validate image matches title ===
        if local_path and self.validator:
            print(f"      [VALIDATOR] Checking '{title[:40]}' vs image...")
            check = await self.validate_product(local_path, title, category)
            
            if not check["valid"]:
                print(f"      [REJECTED] {check['reason']}")
                # Delete the garbage image
                try:
                    os.remove(local_path)
                except OSError:
                    pass
                return None  # Skip this product entirely
            
            # Use Gemini's detected gender (more accurate than text guessing)
            if check.get("detected_gender") in ["male", "female"]:
                gender = check["detected_gender"]
                # Rename file with correct gender if it changed
                new_filename = f"{gender}_{category}_{safe_title}_{int(datetime.now().timestamp())}.png"
                new_path = os.path.join(INPUT_SOURCING_DIR, new_filename)
                if new_path != local_path:
                    try:
                        os.rename(local_path, new_path)
                        local_path = new_path
                    except OSError:
                        pass
            
            print(f"      [APPROVED] {check['reason']} (Gender: {gender})")

        return {
            "productName": title,
            "price": str(price),
            "category": category,
            "gender": gender,
            "productImage": img_url,
            "localImagePath": local_path,
            "productUrl": product_url,
            "source": platform_key,
            "scraped_at": datetime.now().isoformat(),
        }

    async def _download_image(self, url: str, path: str) -> bool:
        """Download product image to local storage."""
        if not url: return False
        if url.startswith("//"): url = "https:" + url
        
        try:
            async with self.session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    with open(path, "wb") as f:
                        f.write(await resp.read())
                    return True
        except Exception as e:
            print(f"      [!] Download failed: {e}")
        return False

    async def _fallback_extract(
        self, page, platform_key: str, category: str
    ) -> List[Dict]:
        """Fallback: extract product info from raw page text."""
        products = []
        try:
            content = await page.content()
            # Look for JSON data embedded in the page
            json_matches = re.findall(
                r'"productName"\s*:\s*"([^"]+)".*?"price"\s*:\s*"?(\d+\.?\d*)"?',
                content
            )
            for name, price in json_matches[:10]:
                products.append({
                    "productName": name,
                    "price": price,
                    "category": category,
                    "productImage": "",
                    "productUrl": page.url,
                    "source": platform_key,
                    "scraped_at": datetime.now().isoformat(),
                })
        except Exception:
            pass
        return products

    def _parse_price(self, price_text: str) -> float:
        """Extract numeric price from text like '$22.50' or '¥189'."""
        numbers = re.findall(r"[\d.]+", price_text)
        if numbers:
            price = float(numbers[0])
            if price > 500:
                price = price / 7.2  # Rough CNY→USD
            return round(price, 2)
        return 0.0

    async def scrape_all(
        self,
        platforms: Optional[List[str]] = None,
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """Scrape from all (or specified) platforms."""
        target_platforms = platforms or list(PLATFORMS.keys())
        all_products = []

        for pk in target_platforms:
            products = await self.scrape_platform(pk, categories)
            all_products.extend(products)

        # Deduplicate by name similarity
        seen = set()
        unique = []
        for p in all_products:
            key = p["productName"][:25].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(p)

        self.all_products = unique
        return unique

    def save_catalog(self, filename: str = "agent_catalog.json") -> str:
        """Save scraped products to JSON."""
        path = os.path.join(OUTPUT_DIR, filename)
        catalog = {
            "scraped_at": datetime.now().isoformat(),
            "total_products": len(self.all_products),
            "products": self.all_products,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Catalog saved: {path} ({len(self.all_products)} products)")
        return path

    async def login_platform(self, platform_key: str):
        """Open visible browser for manual login to save cookies."""
        platform = PLATFORMS.get(platform_key)
        if not platform:
            print(f"Unknown platform: {platform_key}")
            return

        from playwright.async_api import async_playwright
        pw = await async_playwright().__aenter__()
        browser = await pw.chromium.launch(headless=False, slow_mo=500)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto(platform["base_url"])

        print(f"\n[AUTH] Log into {platform['name']} in the browser.")
        print("   Press ENTER after you're logged in...")
        input()

        state = await ctx.storage_state()
        with open(platform["cookie_file"], "w") as f:
            json.dump(state, f)
        print(f"   [+] {platform['name']} cookies saved!")

        await browser.close()
        await pw.stop()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()
        if self.session:
            await self.session.close()


# ==========================================
# AFFILIATE LINK BUILDER
# ==========================================
AFFILIATE_CODES = {
    "usfans": os.getenv("USFANS_AFFILIATE_CODE", ""),
    "cnfans": os.getenv("CNFANS_AFFILIATE_CODE", ""),
    "cssbuy": os.getenv("CSSBUY_AFFILIATE_CODE", ""),
}


def add_affiliate_link(product: dict) -> dict:
    """Append affiliate tracking code to product URL."""
    source = product.get("source", "")
    code = AFFILIATE_CODES.get(source, "")
    url = product.get("productUrl", "")

    if code and url:
        separator = "&" if "?" in url else "?"
        product["affiliateUrl"] = f"{url}{separator}ref={code}"
    else:
        product["affiliateUrl"] = url

    return product


# ==========================================
# CLI
# ==========================================
async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agent Platform Scraper")
    parser.add_argument("--platform", choices=list(PLATFORMS.keys()), help="Specific platform")
    parser.add_argument("--category", choices=list(SCRAPE_CATEGORIES.keys()), help="Specific category")
    parser.add_argument("--login", help="Login to a platform (opens browser)")
    args = parser.parse_args()

    scraper = AgentPlatformScraper(headless=True)

    if args.login:
        await scraper.login_platform(args.login)
        return

    await scraper.start()

    platforms = [args.platform] if args.platform else None
    categories = [args.category] if args.category else None

    products = await scraper.scrape_all(platforms, categories)

    # Add affiliate links
    products = [add_affiliate_link(p) for p in products]
    scraper.all_products = products

    # Save
    scraper.save_catalog()
    await scraper.close()

    # Print summary
    print(f"\n{'='*60}")
    print(f"  SCRAPE SUMMARY")
    print(f"{'='*60}")
    by_source = {}
    for p in products:
        src = p["source"]
        by_source[src] = by_source.get(src, 0) + 1
    for src, count in by_source.items():
        print(f"  {PLATFORMS[src]['name']}: {count} products")
    print(f"  Total: {len(products)} unique products")


if __name__ == "__main__":
    asyncio.run(main())
