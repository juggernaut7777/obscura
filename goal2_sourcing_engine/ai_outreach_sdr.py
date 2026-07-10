import os
import sys
import asyncio
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Safe print for Windows
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

class AIOutreachSDR:
    def __init__(self, headless: bool = True):
        self.headless = headless

    def _extract_metadata(self, html_content: str) -> dict:
        """Helper to extract title, meta description, headlines, and clean body snippet from HTML."""
        soup = BeautifulSoup(html_content, "html.parser")
        scraped_data = {
            "title": "",
            "meta_description": "",
            "headlines": [],
            "body_snippet": ""
        }
        
        # Title
        if soup.title and soup.title.string:
            scraped_data["title"] = soup.title.string.strip()
            
        # Meta Description (try name=description, then og:description, then twitter:description)
        meta_desc = (
            soup.find("meta", attrs={"name": "description"}) or 
            soup.find("meta", attrs={"property": "og:description"}) or 
            soup.find("meta", attrs={"name": "twitter:description"})
        )
        if meta_desc and meta_desc.has_attr("content"):
            scraped_data["meta_description"] = meta_desc["content"].strip()
            
        # Headlines (H1 & H2)
        headlines = [h.get_text().strip() for h in soup.find_all(["h1", "h2"]) if h.get_text().strip()]
        scraped_data["headlines"] = headlines[:6]
        
        # Body Snippet (Clean text)
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_clean = " ".join(chunk for chunk in chunks if chunk)
        scraped_data["body_snippet"] = text_clean[:1500]
        
        return scraped_data

    async def scrape_landing_page(self, domain: str) -> dict:
        """Crawl the target homepage using Playwright to extract key content and headers."""
        if not domain.startswith("http"):
            url = "https://" + domain
        else:
            url = domain
            
        safe_print(f"[*] Crawling target company website: {url}...")
        
        scraped_data = {
            "title": "",
            "meta_description": "",
            "headlines": [],
            "body_snippet": ""
        }
        
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720}
                )
                page = await context.new_page()
                
                # Navigate with wait_until commit to avoid getting stuck on heavy assets
                await page.goto(url, wait_until="commit", timeout=20000)
                await asyncio.sleep(2.0) # wait for DOM script execution
                
                content = await page.content()
                scraped_data = self._extract_metadata(content)
                
                await browser.close()
                safe_print("[+] Scraped homepage successfully via Playwright.")
                
            except Exception as e:
                safe_print(f"[!] Playwright scrape error: {e}")
                # Fallback to simple HTTP if Playwright fails
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    }
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.get(url, headers=headers, follow_redirects=True)
                        if resp.status_code == 200:
                            scraped_data = self._extract_metadata(resp.text)
                            safe_print("[+] Scraped homepage successfully via HTTP fallback.")
                        else:
                            safe_print(f"[!] HTTP fallback failed: HTTP status {resp.status_code}")
                except Exception as ex:
                    safe_print(f"[!] HTTP fallback failed: {ex}")
                    
        return scraped_data

    async def generate_personalized_pitch(self, company_data: dict, pitched_product: str) -> str:
        """Use Gemini via litellm_router to write a hyper-targeted outreach pitch."""
        safe_print(f"[*] Analyzing content and drafting B2B proposal for: {pitched_product}...")
        
        headlines_str = "\n".join(f"- {h}" for h in company_data["headlines"])
        prompt = (
            f"Act as a world-class B2B Sales Development Representative (SDR) and Copywriter.\n"
            f"Your goal is to write a hyper-personalized B2B cold email proposal to pitch a service.\n\n"
            f"--- TARGET COMPANY DETAILS ---\n"
            f"Website Title: '{company_data['title']}'\n"
            f"Meta Description: '{company_data['meta_description']}'\n"
            f"Homepage Headlines:\n{headlines_str}\n"
            f"About Snippet:\n'{company_data['body_snippet']}'\n\n"
            f"--- OUR PRODUCT/SERVICE TO PITCH ---\n"
            f"Pitched Product: '{pitched_product}'\n\n"
            f"--- EMAIL RULES ---\n"
            f"1. Subject line: Write an engaging, curiosity-driven subject line (e.g. referencing their headline or specific problem).\n"
            f"2. Opener: Start by referencing their value proposition or homepage copy to prove we actually visited their site.\n"
            f"3. Core connection: Bridge their company's goals to why they need our product/service. Explain the specific ROI.\n"
            f"4. Call to Action: Offer a low-friction action (e.g., 'Do you have 5 minutes to see a free mock-up scrape next Tuesday?').\n"
            f"5. Pitch Tone: Friendly, professional, clear, and punchy. No generic templates or fake compliments.\n\n"
            f"Return ONLY the subject line and email body."
        )

        try:
            from litellm_router import shared_router
            messages = [{"role": "user", "content": prompt}]
            resp = await shared_router.get_chat_completion(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.7,
                max_tokens=4096
            )
            return resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            safe_print(f"[!] LiteLLM error: {e}")
            return (
                f"Subject: Quick question regarding {company_data['title'] or 'your site'}\n\n"
                f"Hi team,\n\n"
                f"I visited your website and saw your focus on {company_data['meta_description'][:100]}...\n\n"
                f"I wanted to reach out because we offer a service: {pitched_product} that directly helps companies like yours increase efficiency and bypass tech hurdles.\n\n"
                f"Would you be open to a 5-minute chat to see a free demo we built for you? Let me know. Best!"
            )

async def main():
    if len(sys.argv) < 3:
        safe_print("==================================================")
        safe_print("AI OUTBOUND SDR AGENT - DEMO GENERATOR")
        safe_print("==================================================")
        safe_print("Usage: python ai_outreach_sdr.py [domain] [product_to_pitch]")
        safe_print("Example: python ai_outreach_sdr.py topacney.x.yupoo.com \"AI Lookbook Photos\"")
        return

    domain = sys.argv[1]
    pitched_product = " ".join(sys.argv[2:])
    
    sdr = AIOutreachSDR(headless=True)
    company_data = await sdr.scrape_landing_page(domain)
    
    if not company_data["title"] and not company_data["body_snippet"]:
        safe_print("[!] Failed to gather company metadata. Cannot personalize email.")
        return
        
    pitch_email = await sdr.generate_personalized_pitch(company_data, pitched_product)
    
    safe_print("\n==================================================")
    safe_print("GENERATED PERSONALIZED OUTBOUND EMAIL")
    safe_print("==================================================")
    safe_print(pitch_email)
    safe_print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
    # Force exit to prevent LiteLLM background thread hangs
    os._exit(0)
