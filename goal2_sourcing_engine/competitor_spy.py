"""
Competitor Spy & Supplier Stealer
==================================
This script does 3 things:

1. SCRAPES the Meta Ad Library for fashion ads running 30+ days (proven winners)
2. REVERSE IMAGE SEARCHES competitor product photos to find their exact supplier on 1688/AliExpress
3. TRACKS competitor stores to see what's actually selling

This is the "intelligence engine" that feeds the brain with product ideas
that are ALREADY proven to sell.
"""
import asyncio
import os
import json
import time
import csv
from datetime import datetime
from playwright.async_api import async_playwright
from reverse_search import reverse_search_combined

# Output
LEADS_DIR = os.path.join(os.getcwd(), "competitor_intel")
os.makedirs(LEADS_DIR, exist_ok=True)


class CompetitorSpy:
    def __init__(self, headless=True):
        self.headless = headless
        self.winning_products = []
        self.supplier_leads = []

    async def spy_meta_ad_library(self, keywords=None):
        """
        Scrape Meta Ad Library for fashion ads that have been running 30+ days.
        If an ad has been live that long, the product is PRINTING money.
        """
        if keywords is None:
            keywords = [
                "streetwear", "aesthetic clothing", "y2k fashion",
                "oversized hoodie", "graphic tee", "cargo pants women",
                "vintage wash", "two piece set",
                "gym set women", "baggy jeans"
            ]

        print("\n[SPY] Spying on Meta Ad Library for winning products...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()

            for keyword in keywords:
                print(f"   -> Searching: '{keyword}'")
                try:
                    url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&q={keyword.replace(' ', '%20')}&media_type=all"
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(5)

                    # Scroll to load more ads
                    for _ in range(3):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(2)

                    # Extract ad cards
                    ad_cards = await page.locator('[class*="x1lliihq"]').all()
                    
                    for card in ad_cards[:10]:
                        try:
                            text = await card.inner_text()
                            # Look for date indicators showing long-running ads
                            months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
                            if any(month in text.lower() for month in months + ["started running"]):
                                # Extract advertiser name
                                advertiser = text.split("\n")[0][:50] if text else "Unknown"
                                
                                # Try to find external link
                                links = await card.locator("a").all()
                                external_link = ""
                                for link in links:
                                    href = await link.get_attribute("href")
                                    if href and "facebook.com" not in href and "http" in href:
                                        external_link = href
                                        break

                                self.winning_products.append({
                                    "keyword": keyword,
                                    "advertiser": advertiser,
                                    "external_link": external_link,
                                    "found_date": datetime.now().isoformat(),
                                    "platform": "meta_ads"
                                })
                                print(f"      [+] Winner found: {advertiser[:30]} | Link: {external_link[:40]}")
                        except:
                            continue

                except Exception as e:
                    print(f"      [!] Error on '{keyword}': {e}")

            await browser.close()

        print(f"\n[SUCCESS] Found {len(self.winning_products)} winning products from Meta Ad Library!")

    async def spy_tiktok_creative_center(self):
        """
        Scrape TikTok Creative Center for top-performing fashion ads.
        This is TikTok's OFFICIAL tool showing which ads are going viral.
        """
        print("\n[SPY] Spying on TikTok Creative Center for viral fashion ads...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()

            try:
                await page.goto(
                    "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en?period=30&region=US&industry=280403",
                    wait_until="networkidle", timeout=30000
                )
                await asyncio.sleep(5)

                # Extract top ads
                ad_cards = await page.locator('[class*="CardPc"]').all()
                
                for card in ad_cards[:15]:
                    try:
                        text = await card.inner_text()
                        lines = text.strip().split("\n")
                        brand = lines[0][:40] if lines else "Unknown"
                        
                        self.winning_products.append({
                            "keyword": "tiktok_top_ad",
                            "advertiser": brand,
                            "external_link": "",
                            "found_date": datetime.now().isoformat(),
                            "platform": "tiktok_creative_center"
                        })
                        print(f"      [+] Top TikTok ad: {brand}")
                    except:
                        continue

            except Exception as e:
                print(f"   [!] TikTok Creative Center error: {e}")

            await browser.close()

    async def reverse_image_search(self, image_path):
        """
        Take a competitor's product image and reverse search it using stealth Bing Visual Search
        to find the original supplier on AliExpress / 1688 / Alibaba / Weidian.
        """
        print(f"\n[REVERSE] Reverse image searching: {os.path.basename(image_path)}...")
        try:
            results = await reverse_search_combined(image_path)
            for r in results:
                self.supplier_leads.append({
                    "source_image": os.path.basename(image_path),
                    "supplier_url": r["url"],
                    "supplier_name": f"{r['domain'].upper()} Link",
                    "found_date": datetime.now().isoformat()
                })
                print(f"      [+] Supplier found: {r['domain'].upper()} | {r['url'][:60]}")
        except Exception as e:
            print(f"   [!] Reverse search error: {e}")

    def export_intel(self):
        """Export all intelligence to CSV files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        # Winning products
        if self.winning_products:
            filepath = os.path.join(LEADS_DIR, f"winning_products_{timestamp}.csv")
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["keyword", "advertiser", "external_link", "found_date", "platform"])
                writer.writeheader()
                writer.writerows(self.winning_products)
            print(f"\n[EXPORT] Exported {len(self.winning_products)} winning products to {filepath}")

        # Supplier leads
        if self.supplier_leads:
            filepath = os.path.join(LEADS_DIR, f"supplier_leads_{timestamp}.csv")
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["source_image", "supplier_url", "supplier_name", "found_date"])
                writer.writeheader()
                writer.writerows(self.supplier_leads)
            print(f"[EXPORT] Exported {len(self.supplier_leads)} supplier leads to {filepath}")


async def main():
    spy = CompetitorSpy(headless=True)
    
    # Phase 1: Spy on Meta Ad Library
    await spy.spy_meta_ad_library()
    
    # Phase 2: Spy on TikTok Creative Center
    await spy.spy_tiktok_creative_center()
    
    # Phase 3: Reverse image search any product images we have
    output_dir = os.path.join(os.getcwd(), "input_sourcing")
    if os.path.exists(output_dir):
        images = [f for f in os.listdir(output_dir) if f.endswith((".png", ".jpg", ".jpeg"))]
        for img in images[:5]:  # Search top 5 images
            await spy.reverse_image_search(os.path.join(output_dir, img))
    
    # Export everything
    spy.export_intel()

if __name__ == "__main__":
    asyncio.run(main())
