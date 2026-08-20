"""
AGENT BRAIN — OBSCURA AUTONOMOUS ENGINE
=========================================
The multi-model fashion business brain that runs 24/7.

BUSINESS MODELS:
  A. OWN BRAND     — Private label fashion under OBSCURA GARMENTS
  B. CURATION      — Merge pieces from multiple suppliers into styled outfits
  C. AGENCY        — Find brands with bad content, pitch AI photo upgrades
  D. RESELLING     — Source trending items, put on models, sell at markup
  E. DESIGN STUDIO — Sell custom designs to clothing brands (like rith_studio)

PHASES:
  1. Scrape trends (Meta Ads, TikTok, Google Trends)
  2. Generate UGC content (AI models wearing real products)
  3. Build carousels (multi-slide social posts)
  4. Post to socials (anti-shadowban protected)
  5. Hunt factory leads (direct manufacturers)
  6. Update storefront (Supabase → OBSCURA website)
  7. Fulfill orders (CJ Dropshipping, Apliiq)
  8. Spy on competitors (steal their suppliers)
  9. Scout brands (find clients who need content help)

Usage:
  python agent_brain_local.py                    # Full autonomous loop
  python agent_brain_local.py --generate-only    # Just generate content
  python agent_brain_local.py --scrape-only      # Just scrape trends
  python agent_brain_local.py --scout-only       # Just find brand leads
  python agent_brain_local.py --status           # Show current state
"""

import os
import sys
import json
import time
import asyncio
import random
from datetime import datetime
from pathlib import Path

from agent_memory import AgentMemory
from supabase_client import upload_product_to_storefront

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "brain_log.txt"


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[{}] {}".format(timestamp, msg)
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


class LocalBrain:
    """The autonomous local orchestrator."""

    def __init__(self):
        self.memory = AgentMemory()
        self.session_start = datetime.now()
        self.actions = 0
        
        # Load Manifesto
        self.manifesto = ""
        manifesto_path = BASE_DIR / "FASHION_MANIFESTO.md"
        if manifesto_path.exists():
            with open(manifesto_path, "r", encoding="utf-8") as f:
                self.manifesto = f.read()
            log("[BRAIN] Fashion Manifesto loaded. All rules active.")
        else:
            log("[!] WARNING: Fashion Manifesto not found!")

        # Initialize Gemini Director (The Real Intelligence)
        from gemini_director import GeminiDirector
        self.director = GeminiDirector()
        log("[BRAIN] Gemini Director (Multimodal Intelligence) initialized.")

        # Initialize Critic
        from fashion_critic import FashionCritic
        self.critic = FashionCritic(self.manifesto)
        log("[BRAIN] Fashion Critic (Gatekeeper) initialized.")

    # ─── PHASE 1: SCRAPING ───

    async def scrape_trends(self):
        """Run Meta Ad Library + TikTok trend scrapers."""
        log("[BRAIN] Phase 1: Scraping trends...")

        # Meta Ad Library
        try:
            from meta_ad_scraper import MetaAdScraper
            scraper = MetaAdScraper(headless=True)
            await scraper.start()

            # MASSIVE keyword list covering every angle of fashion
            keywords = [
                # Core streetwear
                "streetwear", "aesthetic clothing", "y2k fashion",
                "oversized hoodie", "graphic tee", "cargo pants",
                "baggy jeans men", "vintage wash", "zip up hoodie",
                # Women's fashion
                "two piece set women", "maxi skirt y2k", "gym sets women",
                "pleated skirt", "crop top set", "bodycon dress",
                "women's streetwear shorts", "mesh top outfit",
                # Men's fashion
                "men's casual button down", "polo shirt old money",
                "linen pants men", "varsity jacket", "bomber jacket men",
                "track pants men", "designer inspired men",
                # Shoes & accessories
                "chunky sneakers", "platform shoes", "designer belt",
                "statement jewelry", "mini bag", "sunglasses fashion",
                # Trending aesthetics
                "old money aesthetic", "quiet luxury", "gorpcore",
                "dark academia", "coastal grandmother", "mob wife aesthetic",
                "coquette fashion", "clean girl aesthetic",
                # Seasonal
                "summer outfit", "festival fashion", "winter layering",
                "vacation outfit", "wedding guest outfit",
                # High-engagement niches
                "fashion haul", "outfit of the day", "style inspo",
                "wardrobe essentials", "capsule wardrobe",
                # African/Nigerian fashion (huge market)
                "ankara fashion", "african streetwear", "lagos fashion",
            ]
            keyword = random.choice(keywords)

            log("[SCRAPE] Meta Ad Library: '{}'".format(keyword))
            ads = await scraper.search_ads(keyword, country="US", max_results=10)
            await scraper.close()

            if ads:
                log("[+] Found {} ads for '{}'".format(len(ads), keyword))
                # Save to memory
                for ad in ads[:5]:
                    self.memory.add_product({
                        "name": ad.get("advertiser", "Unknown"),
                        "keyword": keyword,
                        "source": "meta_ads",
                        "link": ad.get("external_link", ""),
                        "screenshot": ad.get("screenshot", ""),
                    })
            else:
                log("[!] No ads found for '{}'".format(keyword))

        except Exception as e:
            log("[!] Meta scraper error: {}".format(e))

        # TikTok Trends
        try:
            from tiktok_trend_scraper import TikTokTrendScraper
            tt_scraper = TikTokTrendScraper(headless=True)
            await tt_scraper.start()
            trends = await tt_scraper.scrape_all()
            tt_scraper.save_report()
            await tt_scraper.close()

            hashtag_count = len(trends.get("hashtags", []))
            product_count = len(trends.get("products", []))
            log("[+] TikTok: {} hashtags, {} products".format(hashtag_count, product_count))

        except Exception as e:
            log("[!] TikTok scraper error: {}".format(e))

        # Agent Product Sourcing (CNFans / USFans)
        try:
            log("[BRAIN] Sourcing products from supplier agents...")
            import subprocess
            # Scrape 2 random categories
            for cat in random.sample(["t-shirts", "hoodies", "pants", "shoes", "dresses", "skirts", "sets"], 2):
                log("   [*] Sourcing category: {}".format(cat))
                subprocess.run(
                    [sys.executable, "agent_product_scraper.py", "--platform", "cnfans", "--category", cat],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    timeout=300
                )
            log("[+] Product sourcing complete!")
        except Exception as e:
            log("[!] Sourcing error: {}".format(e))

        self.actions += 1

    # ─── PHASE 2: CONTENT GENERATION ───

    async def generate_content(self, count=1):
        """Generate UGC images using actual model + product reference images."""
        log(f"[BRAIN] Phase 2: Generating {count} campaign(s)...")

        sys.path.insert(0, str(BASE_DIR))
        try:
            from agent_tools_vps import tool_generate_ad
            
            # Find input products
            input_dir = BASE_DIR / "input_sourcing"
            products = []
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                products.extend([str(p) for p in input_dir.glob(ext)])
            
            if not products:
                log("[!] No products found in input_sourcing/")
                return

            # Find actual model IDs from character sheet files
            models_dir = BASE_DIR / "models" / "character_sheets"
            model_ids = []
            if models_dir.exists():
                for face_file in sorted(models_dir.glob("*_face.png")):
                    mid = face_file.stem.replace("_face", "")
                    model_ids.append(mid)
            if not model_ids:
                model_ids = ["f1"]
            
            log(f"[BRAIN] Available: {len(products)} products, {len(model_ids)} models ({model_ids})")

            for i, product_path in enumerate(products[:count]):
                product_name = Path(product_path).stem
                # Detect Gender and Type using the Critic
                target_gender = "female" # Default
                if product_name.startswith("male_"):
                    target_gender = "male"
                
                product_type = self.critic.detect_product_type(product_name)
                
                # Filter models by gender
                matching_models = [m for m in model_ids if (m.startswith("f") and target_gender == "female") or (m.startswith("m") and target_gender == "male")]
                
                if not matching_models:
                    log(f"[!] No matching models for {target_gender} product: {product_name}")
                    continue
                    
                model_id = random.choice(matching_models)
                
                # CALL THE DIRECTOR: Let Gemini visually design the shoot
                log(f"   [*] Consulting Gemini 2.5 Flash Director for {product_name}...")
                plan = await self.director.design_shoot(product_path, Path(models_dir) / f"{model_id}_face.png")
                
                if not plan or not plan.get("front_prompt"):
                    log(f"[!] Director failed to design shoot for {product_name}")
                    continue

                log(f"[DIRECTOR] Vision for {product_name}:")
                log(f"   Location: {plan.get('location', 'Unknown')}")
                log(f"   Styling: {plan.get('styling_plan', 'None')}")

                result = await tool_generate_ad(
                    product_name=product_name,
                    product_type=plan.get("product_type", "garment"),
                    product_image_path=product_path,
                    model_id=model_id,
                    ad_styles=["streetwear"],
                    memory=self.memory,
                    polished_prompt_from_director=plan.get("front_prompt") 
                )

                if result.get("success"):
                    # VISUAL VALIDATION: Let Gemini check the result
                    gen_path = result.get("image_path")
                    if gen_path and os.path.exists(gen_path):
                        verdict = await self.director.validate_generation(product_path, gen_path)
                        log(f"[VERDICT] {verdict}")
                        
                        if "APPROVED" in verdict.upper():
                            log(f"[+] Campaign {i + 1} APPROVED and moved to review_pending.")
                            self.memory.data["performance"]["total_posts"] += 1
                        else:
                            log(f"[!] Campaign {i + 1} REJECTED by Validator: {verdict}")
                    else:
                        log(f"[!] Campaign {i + 1} COMPLETE but image missing for validation.")
                else:
                    log(f"[!] Campaign {i + 1} FAILED: {result.get('error', 'unknown')}")
                
                # Wait 5 minutes between products to avoid bans
                if i < count - 1:
                    log("[WAIT] Sleeping 5 minutes before next product...")
                    await asyncio.sleep(300)

            self.memory.save()

        except Exception as e:
            log(f"[!] Generation error: {e}")
            import traceback
            traceback.print_exc()

        self.actions += 1

    # ─── PHASE 3: CAROUSEL ASSEMBLY ───

    def build_carousels(self):
        """Assemble generated images into carousel packages."""
        log("[BRAIN] Phase 3: Building carousels...")

        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "carousel_builder_v2.py"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=60
            )
            log("[+] Carousel builder output:")
            for line in result.stdout.strip().split("\n")[-5:]:
                log("  " + line)

        except Exception as e:
            log("[!] Carousel error: {}".format(e))

        self.actions += 1

    # ─── PHASE 4: SOCIAL POSTING (Anti-Shadowban Protected) ───

    async def post_content(self, platform="instagram"):
        """Post assembled carousel to social media with anti-shadowban protections."""
        log("[BRAIN] Phase 4: Posting to {}...".format(platform))

        # ── ANTI-SHADOWBAN: Check daily post limits ──
        today = datetime.now().strftime("%Y-%m-%d")
        post_key = "posts_today_{}".format(platform)
        posts_today = self.memory.data.get(post_key, {}).get(today, 0)
        MAX_POSTS_PER_DAY = 3  # Never exceed 3 posts per platform per day
        
        if posts_today >= MAX_POSTS_PER_DAY:
            log("   [SHIELD] Already posted {}x to {} today. Skipping to avoid shadowban.".format(posts_today, platform))
            return

        carousel_dir = BASE_DIR / "carousel_ready"
        if not carousel_dir.exists():
            log("[!] No carousels ready. Run build_carousels first.")
            return

        # Find the latest carousel
        carousels = sorted(carousel_dir.iterdir(), reverse=True)
        if not carousels:
            log("[!] No carousel folders found.")
            return

        latest = carousels[0]
        manifest_path = latest / "manifest.json"

        if not manifest_path.exists():
            log("[!] No manifest in {}".format(latest.name))
            return

        with open(manifest_path) as f:
            manifest = json.load(f)

        slide_paths = [str(latest / s["filename"]) for s in manifest["slides"]]
        caption = manifest.get("caption", "")

        log("[POST] Carousel: {} ({} slides)".format(latest.name, len(slide_paths)))
        log("[POST] Caption preview: {}...".format(caption[:80]))

        # ── ANTI-SHADOWBAN: Human-like pre-post delay ──
        pre_delay = random.randint(30, 120)  # 30s - 2min random wait before posting
        log("   [SHIELD] Human-like delay: {}s before posting...".format(pre_delay))
        await asyncio.sleep(pre_delay)

        try:
            from social_autoposter import SocialPoster
            poster = SocialPoster(headless=True)
            await poster.start()

            if platform == "instagram":
                success = await poster.post_to_instagram(slide_paths, caption, "clothing")
            elif platform == "tiktok":
                # TikTok needs video, use first image for now
                success = await poster.post_to_tiktok(slide_paths[0], caption, "clothing")
            elif platform == "pinterest":
                success = await poster.post_to_pinterest(
                    slide_paths[0],
                    title=manifest.get("product", "Fashion"),
                    description=caption
                )
            else:
                success = False

            await poster.close()

            if success:
                log("[+] Posted to {} successfully!".format(platform))
                self.memory.mark_product_posted(
                    {"name": manifest.get("product", "unknown")},
                    platform
                )
                # Track daily posts for anti-shadowban
                if post_key not in self.memory.data:
                    self.memory.data[post_key] = {}
                self.memory.data[post_key][today] = posts_today + 1
                self.memory.save()
            else:
                log("[!] Post to {} failed".format(platform))

        except Exception as e:
            log("[!] Posting error: {}".format(e))

        self.actions += 1

    # ─── PHASE 5: LEAD HUNTING ───

    async def hunt_leads(self, niche="streetwear"):
        """Find brands with bad ads and pitch them."""
        log("[BRAIN] Phase 5: Hunting leads in '{}'...".format(niche))

        try:
            from lead_hunter import hunt_for_leads
            await hunt_for_leads(niche, send_emails=False, scan_only=True)
            log("[+] Lead hunt complete!")
        except Exception as e:
            log("[!] Lead hunt error: {}".format(e))

        self.actions += 1

    # ─── PHASE 6: STOREFRONT LISTING (CUSTOM SITE) ───

    async def list_products(self):
        """Push generated fashion products directly to the Obscura Next.js Storefront (via Supabase)."""
        log("[BRAIN] Phase 6: Pushing Products to Custom Storefront...")
        
        try:
            # Find the latest generated products to list
            output_dir = BASE_DIR / "output_ugc"
            # ⚡ Performance optimization
            # Why: Using output_dir.glob() with os.path.getmtime causes N+1 system calls for reading attributes.
            # What: Replaced with os.scandir() to utilize cached file attributes, significantly reducing stat calls.
            image_paths = []
            if output_dir.exists():
                with os.scandir(output_dir) as entries:
                    png_files = [e for e in entries if e.is_file() and e.name.endswith('.png')]
                    recent_entries = sorted(png_files, key=lambda e: e.stat().st_mtime, reverse=True)[:4]
                    image_paths = [e.path for e in recent_entries]

            recent_images = [Path(p) for p in image_paths]
            
            if not image_paths:
                log("   [!] No generated images found to list.")
                return
            
            # Build product data from the most recent generation
            product_name = recent_images[0].stem.split("_")[1] if recent_images else "Fashion Item"
            
            product_data = {
                "title": product_name.replace("_", " ").title(),
                "description": "Premium quality, aesthetically curated fashion. Limited stock.",
                "category": "tops",
                "images": image_paths,
                "price": 85.00
            }
            
            success = upload_product_to_storefront(product_data)
            if success:
                log(f"[POST] Successfully synced '{product_data['title']}' to Obscura website database.")
            else:
                log(f"[!] Failed to sync '{product_data['title']}' to Supabase.")
            log("   [*] Bypassing Meta/TikTok Shops. Socials will be used for organic traffic only.")
            
        except Exception as e:
            log("[!] Storefront error: {}".format(e))
            
        self.actions += 1

    # ─── PHASE 7: ORDER FULFILLMENT ───

    async def fulfill_orders(self):
        """Check for new sales and route them to the supplier."""
        log("[BRAIN] Phase 7: Order Fulfillment Check...")
        
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "auto_fulfillment.py"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=120
            )
            # Log output safely
            if "No pending orders" in result.stdout:
                log("   [*] No pending orders to fulfill.")
            else:
                for line in result.stdout.strip().split("\n")[-4:]:
                    log("   " + line)
        except Exception as e:
            log("[!] Fulfillment error: {}".format(e))
            
        self.actions += 1

    # ─── PHASE 8: COMPETITOR INTELLIGENCE ───

    async def spy_competitors(self):
        """Scrape Meta Ad Library + TikTok Creative Center for winning products, then reverse image search to steal their suppliers."""
        log("[BRAIN] Phase 8: Running Competitor Intelligence...")
        
        try:
            from competitor_spy import CompetitorSpy
            spy = CompetitorSpy(headless=True)
            
            # Spy on Meta Ads — find fashion ads running 30+ days (proven sellers)
            await spy.spy_meta_ad_library()
            
            # Spy on TikTok Creative Center — find viral fashion ads
            await spy.spy_tiktok_creative_center()
            
            # Reverse image search our scraped product images to find suppliers
            input_dir = BASE_DIR / "input_sourcing"
            if input_dir.exists():
                images = [f for f in input_dir.iterdir() if f.suffix in [".png", ".jpg", ".jpeg"]]
                for img in images[:3]:
                    await spy.reverse_image_search(str(img))
            
            spy.export_intel()
            log("[+] Competitor intel gathered! Check competitor_intel/ folder.")
            
        except Exception as e:
            log("[!] Competitor spy error: {}".format(e))
        
        self.actions += 1

    # ─── PHASE 9: BRAND SCOUTING (AGENCY MODEL) ───

    async def scout_brands(self):
        """Find small fashion brands with bad content and pitch them AI photo services."""
        log("[BRAIN] Phase 9: Scouting brands for agency opportunities...")

        try:
            from brand_scout import BrandScout
            scout = BrandScout(headless=True)
            await scout.scout_instagram(max_keywords=5)
            scout.export_leads_csv()

            top_leads = scout.get_top_leads(min_score=5, limit=5)
            if top_leads:
                log("[+] Found {} high-potential brand leads!".format(len(top_leads)))
                for lead in top_leads:
                    log("   @{} | {} followers | Score: {}/10 | Pitch: {}".format(
                        lead['username'], lead['followers'],
                        lead['opportunity_score'], lead['recommended_pitch']
                    ))
            else:
                log("   [*] No high-scoring leads this cycle.")

        except Exception as e:
            log("[!] Brand scout error: {}".format(e))

        self.actions += 1

    # ─── PHASE 10: SELF-IMPROVEMENT (REFLECTION LOOP) ───

    async def reflect_and_adjust(self):
        """Analyze past performance and ask DeepSeek for strategy adjustments."""
        log("[BRAIN] Phase 10: Reflection & Self-Improvement Loop...")
        
        try:
            # 1. Gather metrics
            total_posts = self.memory.data["performance"].get("total_posts", 0)
            avg_engagement = self.memory.data["performance"].get("avg_engagement", 0)
            scraped_products = len(self.memory.data.get("products_scraped", []))
            
            # Simple prompt for DeepSeek
            from deepseek_client import DeepSeekClient
            ds = DeepSeekClient()
            
            prompt = f"""
            You are the core logic engine for an autonomous fashion business.
            Review our current performance:
            - Total Posts Made: {total_posts}
            - Avg Engagement Rate: {avg_engagement}%
            - Products Found via Scraper: {scraped_products}
            
            Based on these metrics, provide 3 short, actionable strategy adjustments we should make to our content or scraping focus in the next cycle. Keep it concise.
            """
            
            advice = ds.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are an elite fashion AI strategist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            ).choices[0].message.content.strip()
            
            log("\n[💡] DEEPSEEK STRATEGY ADJUSTMENT:")
            for line in advice.split("\n"):
                log("   " + line)
                
            # Here we would normally parse the advice and update internal weights (e.g. adjust keyword probabilities)
            # For now, we log the learning.
            self.memory.data["performance"]["last_reflection"] = datetime.now().isoformat()
            self.memory.save()
            
        except Exception as e:
            log(f"[!] Reflection error: {e}")
            
        self.actions += 1

    # ─── MAIN LOOP ───

    async def run(self, mode="full"):
        """Main autonomous loop."""
        log("")
        log("=" * 60)
        log("  [BRAIN] AGENT BRAIN - LOCAL MODE")
        log("  Mode: {}".format(mode.upper()))
        log("  Started: {}".format(self.session_start.strftime("%Y-%m-%d %H:%M")))
        log("=" * 60)

        # Show current state
        log("[STATE] Models: {} | Products scraped: {} | Posts: {}".format(
            self.memory.model_count,
            len(self.memory.data.get("products_scraped", [])),
            self.memory.data["performance"]["total_posts"]
        ))

        if mode == "status":
            log(self.memory.get_state_summary())
            return

        if mode == "scrape-only":
            await self.scrape_trends()
            return

        if mode == "generate-only":
            await self.generate_content(count=1)
            self.build_carousels()
            return

        # Full autonomous loop
        cycle = 0
        while True:
            cycle += 1
            log("")
            log("--- CYCLE {} ---".format(cycle))

            # Step 1: Scrape (every 3rd cycle)
            if cycle % 3 == 1:
                await self.scrape_trends()

            # Step 2: Generate content
            await self.generate_content(count=3)

            # Step 3: Build carousels
            self.build_carousels()

            # Step 4: Post to Instagram (every 2nd cycle)
            if cycle % 2 == 0:
                await self.post_content("instagram")
                # ANTI-SHADOWBAN: Wait 45-90 min between IG and TikTok posts
                cross_delay = random.randint(2700, 5400)
                log("   [SHIELD] Cross-platform cooldown: {}min...".format(cross_delay // 60))
                await asyncio.sleep(cross_delay)
                await self.post_content("tiktok")

            # Step 5: Hunt leads (every 5th cycle)
            if cycle % 5 == 0:
                await self.hunt_leads()

            # Step 6: Storefront management (every 10th cycle)
            if cycle % 10 == 0:
                await self.list_products()

            # Step 7: Order fulfillment (every cycle to ensure fast shipping)
            await self.fulfill_orders()

            # Step 8: Competitor intelligence (every 7th cycle)
            if cycle % 7 == 0:
                await self.spy_competitors()

            # Step 9: Brand scouting / agency mode (every 4th cycle)
            if cycle % 4 == 0:
                await self.scout_brands()

            # Step 10: Self-Improvement Reflection (every 10th cycle)
            if cycle % 10 == 0:
                await self.reflect_and_adjust()

            # Stats
            log("[STATS] Cycle {} complete. Actions: {}".format(cycle, self.actions))

            # ANTI-SHADOWBAN: Long human-like gap between cycles (45-90 min)
            delay = random.randint(2700, 5400)
            log("[WAIT] Next cycle in {}min (anti-shadowban spacing)...".format(delay // 60))
            await asyncio.sleep(delay)


async def main():
    brain = LocalBrain()

    if "--status" in sys.argv:
        await brain.run("status")
    elif "--scrape-only" in sys.argv:
        await brain.run("scrape-only")
    elif "--generate-only" in sys.argv:
        await brain.run("generate-only")
    elif "--scout-only" in sys.argv:
        await brain.run("scout-only")
    else:
        await brain.run("full")


if __name__ == "__main__":
    asyncio.run(main())
