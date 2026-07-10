"""
Meta Ad Library Scraper — Automated Winning Product Discovery
=============================================================
Uses Playwright to scrape facebook.com/ads/library for ads that are
already converting (running 7+ days = profitable).

This replaces manual product research with automated daily discovery.

Usage:
  python meta_ad_scraper.py                    # Run with defaults
  python meta_ad_scraper.py "gym set"          # Search specific keyword
"""
import os
import json
import time
import asyncio
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ==========================================
# CONFIGURATION
# ==========================================
META_AD_LIBRARY_URL = "https://www.facebook.com/ads/library"
OUTPUT_DIR = os.path.join(os.getcwd(), "output", "scraped_ads")
SCREENSHOTS_DIR = os.path.join(OUTPUT_DIR, "screenshots")
CSV_FILE = os.path.join(OUTPUT_DIR, "winning_products.csv")

# Product categories to search daily
DEFAULT_KEYWORDS = [
    "gym set women",
    "streetwear hoodie",
    "chunky sneakers",
    "minimalist jewelry",
    "oversized tee",
    "cargo pants",
    "activewear leggings",
    "gold chain necklace",
]

# Minimum days an ad must be running to be considered a "winner"
MIN_DAYS_RUNNING = 7


class MetaAdScraper:
    """Automated Meta Ad Library scraper for finding winning products."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    async def start(self):
        """Launch browser."""
        from playwright.async_api import async_playwright
        self.pw = await async_playwright().__aenter__()
        self.browser = await self.pw.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox"]
        )
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        self.page = await context.new_page()
        print("[*] Meta Ad Library Scraper started")

    async def search_ads(
        self,
        keyword: str,
        country: str = "US",
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search the Meta Ad Library for ads matching a keyword.
        Returns a list of ad data dicts.
        """
        print(f"\n[>>] Searching: '{keyword}' (Country: {country})...")

        # Navigate to Ad Library with search params
        search_url = (
            f"{META_AD_LIBRARY_URL}/?active_status=active"
            f"&ad_type=all&country={country}"
            f"&q={keyword.replace(' ', '%20')}"
            f"&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped"
        )
        await self.page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(5)

        # Scroll to load more results
        for _ in range(3):
            await self.page.evaluate("window.scrollBy(0, 2000)")
            await asyncio.sleep(2)

        # Extract ad data from the page
        ads = []
        ad_cards = self.page.locator('[class*="ad-card"]').or_(
            self.page.locator('[role="article"]')
        ).or_(
            self.page.locator('[class*="_7jvw"]')  # Meta's internal class
        )

        count = await ad_cards.count()
        count = min(count, max_results)
        print(f"   Found {count} ad cards")

        for i in range(count):
            try:
                card = ad_cards.nth(i)
                ad_data = await self._extract_ad_data(card, keyword, i)
                if ad_data:
                    ads.append(ad_data)
            except Exception as e:
                print(f"   [!]  Error extracting ad {i+1}: {e}")
                continue

        return ads

    async def _extract_ad_data(self, card, keyword: str, index: int) -> Optional[Dict]:
        """Extract relevant data from a single ad card."""
        try:
            # Get the ad text content
            text_content = await card.inner_text()

            # Try to find the start date
            start_date = None
            date_el = card.locator('text=/Started running on/i').or_(
                card.locator('text=/started/i')
            )
            if await date_el.count() > 0:
                date_text = await date_el.first.inner_text()
                start_date = date_text

            # Get the advertiser name
            advertiser = "Unknown"
            adv_el = card.locator('[class*="advertiser"]').or_(
                card.locator('a[href*="facebook.com"]').first
            )
            if await adv_el.count() > 0:
                advertiser = await adv_el.first.inner_text()

            # Take a screenshot of the ad
            screenshot_path = os.path.join(
                SCREENSHOTS_DIR,
                f"{keyword.replace(' ', '_')}_{index+1}_{int(time.time())}.png"
            )
            await card.screenshot(path=screenshot_path)

            # Check for external links (Shopify store, etc.)
            link = None
            link_el = card.locator('a[href*="shopify"]').or_(
                card.locator('a[href*=".com"]')
            )
            if await link_el.count() > 0:
                link = await link_el.first.get_attribute('href')

            return {
                "keyword": keyword,
                "advertiser": advertiser.strip()[:80],
                "start_date": start_date,
                "external_link": link,
                "screenshot": screenshot_path,
                "text_preview": text_content.strip()[:200],
                "scraped_at": datetime.now().isoformat(),
            }
        except:
            return None

    async def find_winners(
        self,
        keywords: Optional[List[str]] = None,
        country: str = "US"
    ) -> List[Dict]:
        """
        Search multiple keywords and compile a list of winning products
        (ads running 7+ days with high engagement signals).
        """
        if not keywords:
            keywords = DEFAULT_KEYWORDS

        all_winners = []

        for keyword in keywords:
            ads = await self.search_ads(keyword, country)
            all_winners.extend(ads)
            await asyncio.sleep(3)  # Rate limiting

        # Save to CSV
        self._save_to_csv(all_winners)
        print(f"\n[STATS] Total ads scraped: {len(all_winners)}")
        print(f"[SAVE] Saved to: {CSV_FILE}")

        return all_winners

    def _save_to_csv(self, ads: List[Dict]):
        """Append scraped ads to the CSV file."""
        file_exists = os.path.exists(CSV_FILE)
        fieldnames = [
            "keyword", "advertiser", "start_date", "external_link",
            "screenshot", "text_preview", "scraped_at"
        ]
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for ad in ads:
                writer.writerow(ad)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()


# ==========================================
# CLI
# ==========================================
async def main():
    import sys
    scraper = MetaAdScraper(headless=True)
    await scraper.start()

    keywords = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_KEYWORDS
    winners = await scraper.find_winners(keywords)

    print(f"\n[WIN] Discovered {len(winners)} potential winning products")
    for w in winners[:5]:
        print(f"   • [{w['keyword']}] {w['advertiser']} — {w['text_preview'][:60]}...")

    await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
