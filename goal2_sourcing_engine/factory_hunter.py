"""
OBSCURA Factory Hunter
======================
This script automates the search for high-end, private label clothing 
manufacturers directly on Instagram and TikTok.

Instead of using dropshipping middlemen, this finds real Chinese/Vietnamese 
factories that are trying to advertise their low MOQs directly to brands.
"""
import asyncio
import os
import csv
from datetime import datetime
from playwright.async_api import async_playwright

IG_COOKIE_FILE = os.path.expanduser("~/.ig_cookies.json")
TIKTOK_COOKIE_FILE = os.path.expanduser("~/.tiktok_cookies.json")

# Keywords that real factories use on social media
SEARCH_TERMS = [
    "clothing manufacturer china",
    "streetwear manufacturer low moq",
    "custom hoodie factory",
    "apparel factory guangzhou",
    "private label clothing factory"
]

class FactoryHunter:
    def __init__(self):
        self.results = []

    async def _load_context(self, browser, cookie_file: str):
        if os.path.exists(cookie_file):
            return await browser.new_context(
                storage_state=cookie_file,
                viewport={"width": 1920, "height": 1080}
            )
        print(f"⚠️ Warning: {cookie_file} not found. Run login_socials.bat first.")
        return await browser.new_context()

    async def hunt_on_instagram(self, browser):
        print("\n[🔍] Hunting for factories on Instagram...")
        ctx = await self._load_context(browser, IG_COOKIE_FILE)
        page = await ctx.new_page()

        try:
            for term in SEARCH_TERMS:
                print(f"   -> Searching IG for: {term}")
                search_url = f"https://www.instagram.com/explore/tags/{term.replace(' ', '')}/"
                await page.goto(search_url, wait_until="networkidle")
                await asyncio.sleep(5)
                
                # We extract the bio or text of the top posts
                # For simplicity in this v1, we just find accounts with "manufacturer" or "factory" in the name
                links = await page.locator("a").all()
                for link in links:
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    if href and "/p/" not in href and ("factory" in href.lower() or "mfg" in href.lower() or "clothing" in href.lower()):
                        username = href.replace("/", "")
                        if username and username not in [r["handle"] for r in self.results]:
                            self.results.append({
                                "platform": "Instagram",
                                "handle": username,
                                "search_term": term,
                                "url": f"https://instagram.com/{username}"
                            })
                            print(f"      [+] Found potential factory: @{username}")
                            
        except Exception as e:
            print(f"   [!] Error on IG: {e}")
        finally:
            await ctx.close()

    async def hunt_on_tiktok(self, browser):
        print("\n[🔍] Hunting for factories on TikTok...")
        ctx = await self._load_context(browser, TIKTOK_COOKIE_FILE)
        page = await ctx.new_page()

        try:
            for term in SEARCH_TERMS:
                print(f"   -> Searching TikTok for: {term}")
                search_url = f"https://www.tiktok.com/search/user?q={term.replace(' ', '%20')}"
                await page.goto(search_url, wait_until="networkidle")
                await asyncio.sleep(5)
                
                # Extract users
                user_cards = await page.locator('[data-e2e="search-user-info-container"]').all()
                for card in user_cards[:5]: # Top 5 per term
                    username = await card.locator("h4").first.inner_text()
                    desc = await card.locator("p").first.inner_text()
                    
                    if username and username not in [r["handle"] for r in self.results]:
                        self.results.append({
                            "platform": "TikTok",
                            "handle": username,
                            "search_term": term,
                            "url": f"https://tiktok.com/@{username}"
                        })
                        print(f"      [+] Found potential factory: @{username} | Bio: {desc[:30]}...")

        except Exception as e:
            print(f"   [!] Error on TikTok: {e}")
        finally:
            await ctx.close()

    def export_leads(self):
        filename = f"factory_leads_{datetime.now().strftime('%Y%m%d')}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["platform", "handle", "search_term", "url"])
            writer.writeheader()
            writer.writerows(self.results)
        print(f"\n[✅] Hunt complete! Saved {len(self.results)} direct factory leads to {filename}")
        print("     Next Step: DM them on WhatsApp/IG to ask for their catalog and dropship rates.")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        hunter = FactoryHunter()
        await hunter.hunt_on_instagram(browser)
        await hunter.hunt_on_tiktok(browser)
        hunter.export_leads()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
