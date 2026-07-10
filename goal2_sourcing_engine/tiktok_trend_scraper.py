"""
TikTok Trend Scraper — Predictive Product Discovery
=====================================================
Scrapes the TikTok Creative Center for trending products,
hashtags, and ad creatives BEFORE they saturate the market.

Uses Playwright to navigate the public TikTok Creative Center
(no API key required).

Outputs: trending keywords, rising hashtags, winning ad formats
"""
import os
import json
import asyncio
import re
from datetime import datetime
from typing import List, Dict

OUTPUT_DIR = os.path.join(os.getcwd(), "output", "trends")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# TikTok Creative Center URLs (public, no login required)
TIKTOK_CREATIVE_CENTER = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"
TIKTOK_TRENDING_PRODUCTS = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/product/pc/en"
TIKTOK_TOP_ADS = "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en"

# Fashion-related hashtag seeds to monitor
FASHION_HASHTAGS = [
    "tiktokmademebuyit", "fashionfinds", "shoefinds",
    "streetwear", "grwm", "ootd", "sneakerhead",
    "luxuryfashion", "affordablefashion",
    "budgetfinds", "aliexpressfinds", "fashiontok", "shoetok",
]

# Categories to track
PRODUCT_CATEGORIES = [
    "Shoes & Footwear", "Clothing & Apparel", "Bags & Accessories",
    "Jewelry & Watches", "Beauty & Personal Care",
]


class TikTokTrendScraper:
    """Scrapes TikTok Creative Center for trending products and hashtags."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.pw = None
        self.trends: Dict = {
            "hashtags": [],
            "products": [],
            "top_ads": [],
            "scraped_at": "",
        }

    async def start(self):
        from playwright.async_api import async_playwright
        self.pw = await async_playwright().__aenter__()
        self.browser = await self.pw.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox"]
        )

    async def scrape_trending_hashtags(self) -> List[Dict]:
        """Scrape trending hashtags from TikTok Creative Center."""
        print("[HOT] Scraping TikTok Trending Hashtags...")
        ctx = await self.browser.new_context()
        page = await ctx.new_page()
        hashtags = []

        try:
            await page.goto(TIKTOK_CREATIVE_CENTER, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            # Extract hashtag cards
            cards = await page.query_selector_all(
                "[class*='hashtag'], [class*='trend'], .card, tr, [class*='row']"
            )

            for card in cards[:30]:
                try:
                    text = await card.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    if len(lines) >= 1:
                        tag_name = lines[0].replace("#", "").strip()
                        views = lines[1] if len(lines) > 1 else "N/A"

                        # Filter for fashion-related only
                        if any(kw in tag_name.lower() for kw in
                               ["fashion", "shoe", "wear", "fit", "drip", "style",
                                "sneaker", "outfit", "luxury", "designer", "finds",
                                "buy", "haul", "grwm", "ootd"]):
                            hashtags.append({
                                "hashtag": f"#{tag_name}",
                                "views": views,
                                "relevance": "fashion",
                            })
                except Exception:
                    continue

            # Also get overall trending
            all_tags = await page.query_selector_all("[class*='name'], [class*='title']")
            for tag_el in all_tags[:20]:
                try:
                    tag_text = (await tag_el.inner_text()).strip()
                    if tag_text.startswith("#") or len(tag_text) > 3:
                        hashtags.append({
                            "hashtag": f"#{tag_text.replace('#', '')}",
                            "views": "trending",
                            "relevance": "general",
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"   [!] Error scraping hashtags: {e}")
        finally:
            await ctx.close()

        # Deduplicate
        seen = set()
        unique = []
        for h in hashtags:
            key = h["hashtag"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(h)

        print(f"   [+] Found {len(unique)} trending hashtags")
        self.trends["hashtags"] = unique
        return unique

    async def scrape_trending_products(self) -> List[Dict]:
        """Scrape trending products from TikTok Creative Center."""
        print("[PKG] Scraping TikTok Trending Products...")
        ctx = await self.browser.new_context()
        page = await ctx.new_page()
        products = []

        try:
            await page.goto(TIKTOK_TRENDING_PRODUCTS, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            # Try to filter by fashion categories
            for cat in PRODUCT_CATEGORIES[:3]:
                try:
                    cat_btn = page.locator(f"text={cat}")
                    if await cat_btn.count() > 0:
                        await cat_btn.first.click()
                        await asyncio.sleep(2)
                except Exception:
                    pass

            # Extract product cards
            cards = await page.query_selector_all(
                "[class*='product'], [class*='item'], .card, [class*='goods']"
            )

            for card in cards[:20]:
                try:
                    text = await card.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]

                    if lines:
                        product = {
                            "productName": lines[0][:80],
                            "category": "fashion",
                            "metrics": lines[1] if len(lines) > 1 else "",
                            "source": "tiktok_trends",
                            "scraped_at": datetime.now().isoformat(),
                        }
                        products.append(product)
                except Exception:
                    continue

            # Extract images
            imgs = await page.query_selector_all("img[src*='product'], img[src*='item']")
            for i, img in enumerate(imgs[:len(products)]):
                try:
                    src = await img.get_attribute("src") or ""
                    if i < len(products):
                        products[i]["productImage"] = src
                except Exception:
                    pass

        except Exception as e:
            print(f"   [!] Error scraping products: {e}")
        finally:
            await ctx.close()

        print(f"   [+] Found {len(products)} trending products")
        self.trends["products"] = products
        return products

    async def scrape_top_ads(self) -> List[Dict]:
        """Scrape top-performing ad creatives from TikTok."""
        print("[WIN] Scraping TikTok Top Ads...")
        ctx = await self.browser.new_context()
        page = await ctx.new_page()
        ads = []

        try:
            await page.goto(TIKTOK_TOP_ADS, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            # Filter by fashion/apparel if possible
            try:
                filter_btn = page.locator("text=Apparel").or_(
                    page.locator("text=Fashion")
                )
                if await filter_btn.count() > 0:
                    await filter_btn.first.click()
                    await asyncio.sleep(2)
            except Exception:
                pass

            # Extract ad cards
            cards = await page.query_selector_all(
                "[class*='ad-card'], [class*='creative'], .card"
            )

            for card in cards[:15]:
                try:
                    text = await card.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if lines:
                        ad = {
                            "headline": lines[0][:100],
                            "metrics": lines[1] if len(lines) > 1 else "",
                            "format": "video" if any(
                                kw in text.lower() for kw in ["video", "reel", "play"]
                            ) else "image",
                            "source": "tiktok_top_ads",
                        }
                        ads.append(ad)
                except Exception:
                    continue

        except Exception as e:
            print(f"   [!] Error scraping top ads: {e}")
        finally:
            await ctx.close()

        print(f"   [+] Found {len(ads)} top-performing ads")
        self.trends["top_ads"] = ads
        return ads

    async def scrape_all(self) -> Dict:
        """Run all scrapers and compile trend report."""
        self.trends["scraped_at"] = datetime.now().isoformat()

        await self.scrape_trending_hashtags()
        await self.scrape_trending_products()
        await self.scrape_top_ads()

        return self.trends

    def generate_hashtag_sets(self) -> Dict[str, str]:
        """
        Generate copy-paste hashtag sets for each product category
        based on scraped trends.
        """
        fashion_tags = [h["hashtag"] for h in self.trends["hashtags"]
                        if h.get("relevance") == "fashion"][:10]
        general_tags = [h["hashtag"] for h in self.trends["hashtags"]
                        if h.get("relevance") == "general"][:5]

        base = " ".join(FASHION_HASHTAGS[:5])
        trending = " ".join(fashion_tags[:5]) if fashion_tags else ""
        general = " ".join(general_tags[:3]) if general_tags else ""

        sets = {
            "shoes": f"#sneakers #kicks #shoegame {trending} {base}",
            "clothing": f"#fashion #streetwear #ootd {trending} {base}",
            "accessories": f"#jewelry #luxury #accessories {trending} {base}",
            "general": f"{trending} {general} {base}",
        }
        return sets

    def save_report(self, filename: str = "trend_report.json") -> str:
        """Save trend data to JSON."""
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.trends, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Trend report saved: {path}")
        return path

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()


# ==========================================
# CLI
# ==========================================
async def main():
    scraper = TikTokTrendScraper(headless=True)
    await scraper.start()

    trends = await scraper.scrape_all()

    # Generate hashtag sets for captions
    hashtag_sets = scraper.generate_hashtag_sets()

    scraper.save_report()
    await scraper.close()

    # Print summary
    print(f"\n{'='*60}")
    print(f"  TIKTOK TREND REPORT — {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*60}")
    print(f"  Trending Hashtags: {len(trends['hashtags'])}")
    print(f"  Trending Products: {len(trends['products'])}")
    print(f"  Top Ads Analyzed:  {len(trends['top_ads'])}")
    print(f"\n  Generated Hashtag Sets:")
    for cat, tags in hashtag_sets.items():
        print(f"    {cat}: {tags[:60]}...")


if __name__ == "__main__":
    asyncio.run(main())
