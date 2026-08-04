"""
Autonomous Lead Hunter v2
==============================================
Full pipeline:
  1. Scrapes Meta Ad Library for ads in a niche
  2. Uses Gemini Vision AI to SCORE each ad (1-10) on multiple quality signals
  3. Extracts brand contact info (email from website, social handle)
  4. Generates a premium AI sample replacement using Nano Banana Pro
  5. Optionally sends a cold email with the sample attached

Usage:
  python lead_hunter.py "handbags"
  python lead_hunter.py "streetwear" --email       # Also send cold emails
  python lead_hunter.py "sneakers" --scan-only     # Just find leads, no generation
"""
import os
import sys
import re
import json
import asyncio
import smtplib
import requests
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from dotenv import load_dotenv

# Import the existing Meta Scraper
from meta_ad_scraper import MetaAdScraper
# Import the existing Sample Generator and Tracker
import lead_tracker
import sample_generator

# Import VisionEvaluator encoding logic
from vision_evaluator import VisionEvaluator

load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================
# Quality threshold: ads scoring BELOW this are considered "bad" leads
BAD_AD_THRESHOLD = 5

# Cold email settings (configure in .env)
SMTP_HOST = os.getenv("SMTP_HOST", "")          # e.g. smtp.gmail.com
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")           # your outreach email
SMTP_PASS = os.getenv("SMTP_PASS", "")           # app password
SENDER_NAME = os.getenv("SENDER_NAME", "Creative Studio")


class BadAdHunter(VisionEvaluator):
    """Evaluates ad screenshots using multi-signal quality scoring."""

    def score_ad(self, image_path: str) -> dict:
        """
        Scores an ad screenshot on multiple quality signals (1-10 each).
        Returns:
        {
            "overall_score": int (1-10),
            "is_bad": bool,
            "product_desc": str,
            "product_niche": str,
            "brand_name": str,
            "weaknesses": [str],
            "signals": {
                "lighting": int,
                "composition": int,
                "background": int,
                "model_styling": int,
                "text_design": int,
            }
        }
        """
        if not self.api_key:
            print("⚠️  No Gemini API key found for vision evaluation.")
            return {"overall_score": 5, "is_bad": False, "product_desc": ""}

        image_part = self._encode_image(image_path)
        if not image_part:
            return {"overall_score": 5, "is_bad": False, "product_desc": ""}

        prompt = """
        You are an expert Creative Director at a top advertising agency.
        Analyze this social media ad screenshot and score it on EACH of these 5 quality signals (1-10 scale, where 1 is terrible and 10 is world-class):

        1. "lighting" — Is the product/model well-lit? Or is it dark, harsh shadows, uneven?
        2. "composition" — Is the framing professional? Or is it awkward crops, too much empty space, cluttered?
        3. "background" — Is the backdrop intentional and aesthetic? Or messy bedroom, plain white, distracting clutter?
        4. "model_styling" — If a person is shown, do they look styled and confident? If product-only, is it well-presented?
        5. "text_design" — Is the text/typography clean and branded? Or is it generic, poorly placed, ugly fonts?

        Also extract:
        - The brand/advertiser name visible in the ad
        - A concise 3-5 word physical description of the main product (e.g. "red leather tote bag")
        - The product niche: one of [clothing, shoes, bags, accessories, beauty, wigs, jewelry, fitness]
        - A list of the top 2-3 specific weaknesses you see

        Answer ONLY with a JSON object in this exact format:
        {
            "signals": {"lighting": 4, "composition": 3, "background": 2, "model_styling": 5, "text_design": 3},
            "overall_score": 3,
            "product_desc": "red leather tote bag",
            "product_niche": "bags",
            "brand_name": "FreshStyle Co",
            "weaknesses": ["harsh overhead lighting", "cluttered bedroom background", "generic Impact font"]
        }
        """

        payload = {
            "contents": [{"parts": [{"text": prompt}, image_part]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        try:
            response = requests.post(f"{self.endpoint}?key={self.api_key}", json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            response_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()

            result = json.loads(response_text)
            score = result.get("overall_score", 5)
            result["is_bad"] = score < BAD_AD_THRESHOLD
            return result

        except Exception as e:
            print(f"⚠️  Vision API error: {e}")
            return {"overall_score": 5, "is_bad": False, "product_desc": ""}


class EmailExtractor:
    """Extracts contact emails from brand websites found in ads."""

    @staticmethod
    async def extract_email_from_url(url: str) -> str:
        """Scrapes a website landing page for a contact/business email using non-blocking aiohttp."""
        if not url:
            return ""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10, allow_redirects=True) as r:
                    text = await r.text()
            # Find all email patterns in the page source
            emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
            # Filter out common junk emails
            junk = ["wixpress", "sentry", "example", "test", "noreply", "cdn", "webpack", "schema"]
            valid = [e for e in emails if not any(j in e.lower() for j in junk)]
            return valid[0] if valid else ""
        except Exception:
            return ""


class ColdEmailer:
    """Sends personalized cold outreach emails with the AI sample attached."""

    def __init__(self):
        self.configured = bool(SMTP_HOST and SMTP_USER and SMTP_PASS)
        if not self.configured:
            print("⚠️  Cold email not configured. Add SMTP_HOST, SMTP_USER, SMTP_PASS to your .env file.")

    def send_sample_email(self, to_email: str, brand_name: str, product_desc: str,
                          weaknesses: list, sample_image_path: str) -> bool:
        """Sends a personalized cold email with the AI-generated sample attached."""
        if not self.configured:
            print("   📧 Skipping email (SMTP not configured).")
            return False

        subject = f"I redesigned your {product_desc} ad — free sample inside"

        weakness_text = ", ".join(weaknesses[:2]) if weaknesses else "the overall visual quality"

        body = f"""Hi {brand_name} team,

I came across your {product_desc} ad and noticed an opportunity to improve {weakness_text}.

I went ahead and created a free sample redesign — see the attached image. No strings attached. I just want to show you what's possible.

If you like what you see, I offer professional product photography and ad creative packages starting at $75 for 5 images.

Would love to chat if you're interested.

Best,
{SENDER_NAME}

P.S. Reply "STOP" if you don't want to hear from me again.
"""

        try:
            msg = MIMEMultipart()
            msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # Attach the sample image
            if sample_image_path and os.path.exists(sample_image_path):
                with open(sample_image_path, "rb") as f:
                    img = MIMEImage(f.read())
                    img.add_header("Content-Disposition", "attachment",
                                   filename=f"your_{product_desc.replace(' ', '_')}_redesign.png")
                    msg.attach(img)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)

            print(f"   📧 ✅ Cold email sent to: {to_email}")
            return True

        except Exception as e:
            print(f"   📧 ❌ Email failed: {e}")
            return False


async def hunt_for_leads(keyword: str, send_emails: bool = False, scan_only: bool = False):
    print(f"\n=============================================")
    print(f"🕵️  AUTONOMOUS LEAD HUNTER v2: '{keyword}'")
    print(f"=============================================")
    print(f"   Mode: {'SCAN ONLY' if scan_only else 'FULL PIPELINE'}")
    print(f"   Cold Email: {'ON' if send_emails else 'OFF'}")
    print(f"   Bad Ad Threshold: Score < {BAD_AD_THRESHOLD}/10")

    # 1. Check bridge (skip if scan-only)
    if not scan_only and not sample_generator.check_bridge():
        print("❌ Bridge offline. Run with --scan-only or start the bridge.")
        return

    # 2. Scrape Meta Ads
    scraper = MetaAdScraper(headless=True)
    await scraper.start()

    print(f"\n📥 Scraping Meta Ad Library for '{keyword}' ads...")
    ads = await scraper.search_ads(keyword, country="US", max_results=15)
    await scraper.close()

    if not ads:
        print("📭 No ads found.")
        return

    print(f"   Found {len(ads)} ads to evaluate.\n")

    # 3. Score each ad with multi-signal Vision AI
    hunter = BadAdHunter()
    emailer = ColdEmailer() if send_emails else None
    email_extractor = EmailExtractor()
    found_leads = 0

    for i, ad in enumerate(ads):
        if found_leads >= 5:
            print("\n🎯 Hit daily lead cap (5). Stopping to stay under rate limits.")
            break

        screenshot = ad.get("screenshot")
        advertiser = ad.get("advertiser", "Unknown")
        external_link = ad.get("external_link", "")

        if not screenshot or not os.path.exists(screenshot):
            continue

        print(f"─── Ad {i+1}/{len(ads)}: {advertiser} ───")

        # Score it
        result = hunter.score_ad(screenshot)
        score = result.get("overall_score", 5)
        signals = result.get("signals", {})
        weaknesses = result.get("weaknesses", [])
        product_desc = result.get("product_desc", "")
        product_niche = result.get("product_niche", keyword)
        brand_name = result.get("brand_name", advertiser)

        # Print scorecard
        print(f"   📊 SCORE: {score}/10  {'🔴 BAD' if result.get('is_bad') else '🟢 GOOD'}")
        if signals:
            print(f"      💡 Lighting: {signals.get('lighting','?')}/10 | "
                  f"📐 Composition: {signals.get('composition','?')}/10 | "
                  f"🖼️ Background: {signals.get('background','?')}/10")
            print(f"      👗 Styling: {signals.get('model_styling','?')}/10 | "
                  f"🔤 Typography: {signals.get('text_design','?')}/10")
        if weaknesses:
            print(f"      ⚠️  Weaknesses: {', '.join(weaknesses)}")

        if not result.get("is_bad") or not product_desc:
            print(f"   ✅ Ad is acceptable quality. Skipping.\n")
            continue

        print(f"   🛍️  Product: {product_desc} ({product_niche})")

        # 4. Extract contact email from their website
        contact_email = ""
        if external_link:
            print(f"   🔍 Scraping email from: {external_link[:50]}...")
            contact_email = await email_extractor.extract_email_from_url(external_link)
            if contact_email:
                print(f"   📧 Found email: {contact_email}")
            else:
                print(f"   📧 No email found on landing page.")

        # 5. Generate replacement sample (unless scan-only)
        sample_path = ""
        if not scan_only:
            print(f"   ✨ Generating premium replacement via Nano Banana Pro...")
            generated = sample_generator.generate_sample(
                product_description=product_desc,
                niche=product_niche,
                image_path=screenshot
            )
            if generated:
                sample_path = generated[0]

        # 6. Add to CRM
        lead_tracker.add_lead(
            brand=brand_name,
            platform="meta",
            handle=contact_email if contact_email else "search_fb_page",
            niche=product_niche,
            notes=f"Score:{score}/10 | {product_desc} | Weaknesses: {', '.join(weaknesses[:2])}"
        )
        found_leads += 1

        # 7. Send cold email (if enabled and email found)
        if send_emails and contact_email and sample_path:
            emailer.send_sample_email(
                to_email=contact_email,
                brand_name=brand_name,
                product_desc=product_desc,
                weaknesses=weaknesses,
                sample_image_path=sample_path
            )

        print()

    # Summary
    print(f"═══════════════════════════════════════════")
    print(f"✅ Hunt complete!")
    print(f"   🎯 Bad ads found: {found_leads}")
    print(f"   📁 Samples saved to: output/samples/")
    print(f"   📋 Run 'python lead_tracker.py list' to see your pipeline")
    print(f"   📊 Run 'python lead_tracker.py stats' for conversion stats")
    print(f"═══════════════════════════════════════════")


if __name__ == "__main__":
    kw = "streetwear"
    do_email = False
    do_scan = False

    args = sys.argv[1:]
    for a in args:
        if a == "--email":
            do_email = True
        elif a == "--scan-only":
            do_scan = True
        else:
            kw = a

    asyncio.run(hunt_for_leads(kw, send_emails=do_email, scan_only=do_scan))
