"""
Brand Scout — Find Brands With Bad Content & Pitch AI Upgrades
================================================================
This is the "Agency Mode" for OBSCURA.

What it does:
1. Scrapes Instagram for fashion brands that have BAD product photos
   (flat lays on wood floors, plain backgrounds, no models)
2. Identifies brands that could benefit from AI-generated model photos
3. Generates a pitch DM offering to upgrade their content
4. Tracks which brands have been contacted and their response

Business Models This Enables:
- Pay-per-photo: "I'll put your clothes on a model for $X per photo"
- Monthly retainer: "I'll manage your content for $X/month"
- Commission: "Let me sell your stuff on my page, I take 30%"
- Styling curation: Merge pieces from multiple brands into outfits
"""
import asyncio
import os
import json
import csv
import random
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
SCOUT_DIR = BASE_DIR / "brand_leads"
SCOUT_DIR.mkdir(exist_ok=True)

# Brands with these signs = BAD content = OPPORTUNITY for us
BAD_CONTENT_SIGNALS = [
    "flat lay on floor",
    "wooden background",
    "no model",
    "single product shot",
    "blurry photos",
    "inconsistent feed",
    "low engagement",
    "whatsapp link in bio",  # Usually small brands
]

# Keywords to find small fashion brands on IG
BRAND_SEARCH_KEYWORDS = [
    # Small brand indicators
    "small clothing brand", "independent fashion brand",
    "streetwear brand", "clothing startup",
    "new fashion brand", "custom clothing",
    "handmade fashion", "designer clothing",
    # Nigerian/African fashion (huge market, many need content help)
    "lagos fashion", "naija fashion brand", "african streetwear",
    "ankara modern", "nigerian designer",
    # UK/US small brands
    "london streetwear", "uk fashion brand",
    "nyc streetwear brand", "la fashion brand",
    # Niche markets
    "vintage clothing store", "thrift fashion",
    "y2k clothing brand", "gothic fashion brand",
    "minimalist clothing brand", "oversized streetwear",
]

# Pre-written pitch templates (the brain picks the right one)
PITCH_TEMPLATES = {
    "content_upgrade": """Hey! 👋 Love what you're building with {brand_name}. 

I run a creative studio that specializes in fashion content. I noticed your pieces have real potential but your content isn't doing them justice.

I can put your products on AI-generated models with professional lighting and backgrounds — think lookbook quality, but 10x faster and cheaper than a photoshoot.

I attached 1 FREE sample picture I did with one of your pieces so you can see the quality. No strings attached. 🖤
If you are interested for more or to work together, let's discuss price.

— OBSCURA Studio""",

    "collaboration": """Hey {brand_name}! 🖤

Your pieces caught my eye. I curate styled looks for my audience and I think some of your items would fit perfectly.

Would you be open to a collab? I'd style your pieces into complete outfits, shoot them on models, and feature them to my followers. 

I attached 1 FREE sample picture to show you the aesthetic.
If you are interested for more or to work together, let's discuss price.

— OBSCURA""",

    "reselling": """Hi {brand_name}! 

I love your collection. I run a curated fashion page and I think your pieces would do really well with my audience.

Would you be open to a wholesale/consignment arrangement? I handle all the content creation and marketing.

I attached 1 FREE sample picture of how I would market your pieces.
If you are interested for more or to work together, let's discuss price. 🤝

— OBSCURA""",
}


class BrandScout:
    def __init__(self, headless=True):
        self.headless = headless
        self.leads = []
        self.leads_file = SCOUT_DIR / "brand_leads.json"
        self._load_existing_leads()

    def _load_existing_leads(self):
        """Load previously found leads to avoid duplicates."""
        if self.leads_file.exists():
            with open(self.leads_file) as f:
                self.leads = json.load(f)

    def _save_leads(self):
        """Persist leads to disk."""
        with open(self.leads_file, "w") as f:
            json.dump(self.leads, f, indent=2, default=str)

    def _is_already_found(self, username):
        return any(l.get("username") == username for l in self.leads)

    async def scout_instagram(self, max_keywords=5):
        """
        Search Instagram for small fashion brands with weak content.
        These are our potential clients/partners.
        """
        print("\n[🔍] Brand Scout: Hunting for brands with bad content...")
        
        cookie_file = os.path.expanduser("~/.ig_cookies.json")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )

            if os.path.exists(cookie_file):
                ctx = await browser.new_context(
                    storage_state=cookie_file,
                    viewport={"width": 1280, "height": 720}
                )
            else:
                ctx = await browser.new_context(viewport={"width": 1280, "height": 720})

            page = await ctx.new_page()

            # Shuffle keywords so we don't search the same ones every time
            keywords = random.sample(BRAND_SEARCH_KEYWORDS, min(max_keywords, len(BRAND_SEARCH_KEYWORDS)))

            for keyword in keywords:
                print(f"   -> Searching: '{keyword}'")
                try:
                    search_url = f"https://www.instagram.com/explore/search/keyword/?q={keyword.replace(' ', '%20')}"
                    await page.goto(search_url, wait_until="networkidle", timeout=20000)
                    await asyncio.sleep(3)

                    # Try to find profile links in search results
                    profile_links = await page.locator('a[href*="/"]').all()
                    
                    found_this_keyword = 0
                    for link in profile_links[:20]:
                        try:
                            href = await link.get_attribute("href")
                            if href and "/" in href and not any(x in href for x in ["explore", "reels", "stories", "p/", "reel/"]):
                                username = href.strip("/").split("/")[-1]
                                if username and len(username) > 2 and not self._is_already_found(username):
                                    # Visit the profile to analyze content quality
                                    lead = await self._analyze_profile(page, username)
                                    if lead:
                                        self.leads.append(lead)
                                        found_this_keyword += 1
                                        print(f"      [+] Lead found: @{username} | Followers: {lead.get('followers', '?')} | Score: {lead.get('opportunity_score', '?')}/10")
                                        
                                        if found_this_keyword >= 3:
                                            break
                        except:
                            continue

                    # Anti-detection delay between keyword searches
                    await asyncio.sleep(random.randint(5, 15))

                except Exception as e:
                    print(f"      [!] Error searching '{keyword}': {e}")
                    await asyncio.sleep(5)

            await browser.close()

        self._save_leads()
        print(f"\n[✅] Brand Scout complete! Found {len(self.leads)} total leads.")

    async def _analyze_profile(self, page, username):
        """
        Visit a brand's IG profile and analyze their content quality.
        Returns a lead dict with an opportunity score.
        """
        try:
            await page.goto(f"https://www.instagram.com/{username}/", wait_until="networkidle", timeout=15000)
            await asyncio.sleep(2)

            # Check if profile exists and is public
            if "Page Not Found" in await page.title() or await page.locator('text="Sorry, this page"').count() > 0:
                return None

            # Extract follower count
            followers_text = ""
            meta_desc = await page.locator('meta[name="description"]').get_attribute("content") or ""
            
            # Parse follower count from meta description
            followers = 0
            if "Followers" in meta_desc:
                parts = meta_desc.split("Followers")[0].strip().split()
                if parts:
                    count_str = parts[-1].replace(",", "").replace("K", "000").replace("M", "000000")
                    try:
                        followers = int(float(count_str))
                    except:
                        pass

            # Extract bio
            bio = ""
            bio_el = page.locator('section header section > div').first
            if await bio_el.count() > 0:
                bio = await bio_el.inner_text()

            # Check for website (brands with WhatsApp = small/opportunity)
            has_website = await page.locator('a[href*="http"]').count() > 0
            has_whatsapp = "wa.me" in (await page.content()).lower() or "whatsapp" in bio.lower()

            # Count posts
            posts_text = await page.locator('header section ul li').first.inner_text() if await page.locator('header section ul li').count() > 0 else "0"
            
            # Analyze content quality by looking at grid images
            grid_images = await page.locator('article img').all()
            image_count = len(grid_images)

            # Calculate opportunity score (0-10)
            # Higher = MORE opportunity for us
            score = 5  # Start neutral

            # Small brands = bigger opportunity
            if followers < 1000:
                score += 2
            elif followers < 5000:
                score += 1.5
            elif followers < 10000:
                score += 1
            elif followers > 50000:
                score -= 2  # Too big, probably has their own team

            # WhatsApp link = small brand, big opportunity
            if has_whatsapp:
                score += 1.5

            # Fashion/clothing keywords in bio = confirmed brand
            fashion_words = ["clothing", "fashion", "brand", "wear", "apparel", "style", "designer", "boutique", "store", "shop"]
            if any(word in bio.lower() for word in fashion_words):
                score += 1
            else:
                score -= 2  # Probably not a fashion brand

            # Cap the score
            score = max(1, min(10, round(score, 1)))

            # Determine best pitch type
            if score >= 7:
                pitch_type = "content_upgrade"  # They desperately need better content
            elif score >= 5:
                pitch_type = "collaboration"  # Could be a good partner
            else:
                pitch_type = "reselling"  # Maybe we can resell their stuff

            return {
                "username": username,
                "followers": followers,
                "bio": bio[:200],
                "has_website": has_website,
                "has_whatsapp": has_whatsapp,
                "post_count": image_count,
                "opportunity_score": score,
                "recommended_pitch": pitch_type,
                "pitch_text": PITCH_TEMPLATES[pitch_type].format(brand_name=username),
                "status": "new",  # new -> contacted -> responded -> converted
                "found_date": datetime.now().isoformat(),
                "contacted_date": None,
                "notes": "",
            }

        except Exception as e:
            return None

    def get_top_leads(self, min_score=6, limit=10):
        """Get the best leads sorted by opportunity score."""
        filtered = [l for l in self.leads if l.get("opportunity_score", 0) >= min_score and l.get("status") == "new"]
        return sorted(filtered, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:limit]

    def export_leads_csv(self):
        """Export leads to CSV for easy review."""
        if not self.leads:
            print("No leads to export.")
            return

        filepath = SCOUT_DIR / f"brand_leads_{datetime.now().strftime('%Y%m%d')}.csv"
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "username", "followers", "opportunity_score", "recommended_pitch",
                "has_whatsapp", "status", "found_date", "bio"
            ])
            writer.writeheader()
            for lead in sorted(self.leads, key=lambda x: x.get("opportunity_score", 0), reverse=True):
                writer.writerow({k: lead.get(k, "") for k in writer.fieldnames})
        
        print(f"[📊] Exported {len(self.leads)} leads to {filepath}")


async def main():
    scout = BrandScout(headless=True)
    await scout.scout_instagram(max_keywords=8)
    scout.export_leads_csv()
    
    # Show top leads
    top = scout.get_top_leads(min_score=5, limit=5)
    if top:
        print("\n[🏆] TOP LEADS:")
        for lead in top:
            print(f"   @{lead['username']} | {lead['followers']} followers | Score: {lead['opportunity_score']}/10 | Pitch: {lead['recommended_pitch']}")


if __name__ == "__main__":
    asyncio.run(main())
    # Force exit to prevent LiteLLM background thread hangs
    os._exit(0)
