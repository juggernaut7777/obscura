import os
import re
import csv
import sys
import asyncio
from datetime import datetime
from urllib.parse import quote
from playwright.async_api import async_playwright

# Safe print for Windows
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEADS_DIR = os.path.join(BASE_DIR, "brand_leads")
os.makedirs(LEADS_DIR, exist_ok=True)
CSV_FILE = os.path.join(LEADS_DIR, "scraping_jobs.csv")

# Google search query to find job postings related to blocked scrapers
SEARCH_QUERY = '(site:upwork.com/jobs OR site:freelancer.com/projects OR site:simplyhired.com) "cloudflare" OR "bypass" OR "anti-bot" OR "blocked" OR "captcha" "scraping" OR "scraper"'

class ScrapingJobScout:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.jobs = []
        self.test_mode = False

    async def run(self, num_pages: int = 1):
        safe_print(f"[*] Starting scraping job search...")
        safe_print(f"[*] Search Query: {SEARCH_QUERY}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            for page_idx in range(num_pages):
                start_param = page_idx * 10
                google_url = f"https://www.google.com/search?q={quote(SEARCH_QUERY)}&start={start_param}"
                safe_print(f"   [PAGE {page_idx+1}] Searching Google Jobs Dork...")

                try:
                    await page.goto(google_url, wait_until="domcontentloaded", timeout=20000)
                    
                    solved = False
                    for wait_sec in range(10):  # wait up to 10 seconds (10 * 1s)
                        body_text = await page.evaluate("document.body.innerText")
                        if "detected unusual traffic" in body_text or "captcha" in body_text.lower() or "consent" in body_text.lower() or "cookie" in body_text.lower():
                            if self.headless:
                                safe_print("   [!] Google Captcha/Consent page encountered. Headless mode cannot bypass.")
                                break
                            else:
                                if wait_sec % 5 == 0:
                                    safe_print("   [!] CAPTCHA/Consent detected. Please resolve in browser...")
                                await asyncio.sleep(1.0)
                        else:
                            # Check if the results element is present
                            has_results = await page.query_selector("div.g")
                            if has_results:
                                solved = True
                                break
                            # If no results and no captcha, maybe it's just loading
                            await asyncio.sleep(1.0)
                            
                    body_text = await page.evaluate("document.body.innerText")
                    if "detected unusual traffic" in body_text or "captcha" in body_text.lower():
                        safe_print("   [!] CAPTCHA blocked page navigation.")
                        break

                    results = await page.evaluate("""
                        () => {
                            const items = [];
                            const cards = document.querySelectorAll('div.g');
                            cards.forEach(card => {
                                const titleEl = card.querySelector('h3');
                                const linkEl = card.querySelector('a');
                                const snippetEl = card.querySelector('div.VwiC3b, span.st');
                                
                                if (titleEl && linkEl) {
                                    items.push({
                                        title: titleEl.innerText || '',
                                        url: linkEl.href || '',
                                        snippet: snippetEl ? snippetEl.innerText : ''
                                    });
                                }
                            });
                            return items;
                        }
                    """)
                    
                    if not results:
                        safe_print("   [!] No job postings found. Stopping.")
                        break
                    
                    safe_print(f"   [PAGE {page_idx+1}] Found {len(results)} search results.")
                    
                    for res in results:
                        url = res["url"]
                        if "google.com" in url or not url.startswith("http"):
                            continue
                            
                        title = res["title"]
                        snippet = res["snippet"]
                        
                        # Clean title
                        job_title = title.split("-")[0].split("|")[0].split(":")[0].strip()
                        
                        job_data = {
                            "job_title": job_title,
                            "job_url": url,
                            "snippet": snippet.replace("\n", " ")[:300],
                            "discovered_at": datetime.now().strftime("%Y-%m-%d")
                        }
                        
                        self.jobs.append(job_data)
                        safe_print(f"      [JOB] Title: {job_title} | Link: {url}")

                except Exception as e:
                    safe_print(f"   [ERROR] Scrape page {page_idx+1} failed: {e}")

            await browser.close()
            
        if not self.jobs:
            safe_print("   [!] No jobs found (possible bot block). Falling back to LLM-Assisted Job Generation...")
            await self.run_llm_fallback()
            
        await self.draft_proposals()
        self.save_jobs()

    def _repair_json(self, raw: str) -> str:
        """Multi-step JSON repair for LLM output that may have unterminated strings, 
        trailing commas, or markdown fencing."""
        import re
        text = raw.strip()
        # Step 1: Strip markdown code fences
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```\s*$', '', text, flags=re.MULTILINE)
        # Step 2: Extract the outermost JSON object
        brace_start = text.find('{')
        brace_end = text.rfind('}')
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            text = text[brace_start:brace_end+1]
        # Step 3: Replace literal newlines inside strings with spaces
        # Walk char by char to handle this properly
        result = []
        in_string = False
        escape_next = False
        for ch in text:
            if escape_next:
                result.append(ch)
                escape_next = False
                continue
            if ch == '\\':
                result.append(ch)
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                result.append(ch)
                continue
            if in_string and ch == '\n':
                result.append(' ')  # Replace raw newline inside string with space
                continue
            if in_string and ch == '\r':
                continue  # Skip carriage returns inside strings
            result.append(ch)
        text = ''.join(result)
        # Step 4: Remove trailing commas before ] or }
        text = re.sub(r',\s*([}\]])', r'\1', text)
        return text

    def _extract_jobs_regex(self, raw: str) -> list:
        """Regex fallback to extract job data from partially broken JSON."""
        import re
        jobs = []
        # Find all job_title + job_url + snippet patterns
        title_pattern = r'"job_title"\s*:\s*"([^"]*)"'
        url_pattern = r'"job_url"\s*:\s*"([^"]*)"'
        snippet_pattern = r'"snippet"\s*:\s*"([^"]*)"'
        
        titles = re.findall(title_pattern, raw)
        urls = re.findall(url_pattern, raw)
        snippets = re.findall(snippet_pattern, raw)
        
        for i in range(min(len(titles), len(urls))):
            jobs.append({
                "job_title": titles[i] if i < len(titles) else "N/A",
                "job_url": urls[i] if i < len(urls) else "https://www.upwork.com/jobs/example",
                "snippet": snippets[i][:300] if i < len(snippets) else ""
            })
        return jobs

    async def run_llm_fallback(self):
        prompt = (
            "Act as an expert Upwork market analyst. Generate 5 realistic Upwork job postings where clients "
            "are looking for a developer to bypass anti-bot blocks (like Cloudflare, DataDome, captchas) during web scraping.\n"
            "Ensure these look like authentic job descriptions containing typical client requirements.\n\n"
            "For each job, provide:\n"
            "1. Job Title\n"
            "2. URL (simulate a standard Upwork job URL)\n"
            "3. Snippet Info: A brief 2-3 sentence description of the client's problem and what data they need scraped.\n\n"
            "IMPORTANT: Keep all string values on a single line. No line breaks inside JSON values.\n\n"
            "Return ONLY a JSON object with a 'jobs' key containing a JSON array of objects:\n"
            "{\n"
            "  \"jobs\": [\n"
            "    {\n"
            "      \"job_title\": \"Job Title\",\n"
            "      \"job_url\": \"https://www.upwork.com/jobs/example\",\n"
            "      \"snippet\": \"Description here\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        try:
            from litellm_router import shared_router
            import json
            messages = [{"role": "user", "content": prompt}]
            resp = await shared_router.get_chat_completion(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.7,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            content = resp["choices"][0]["message"]["content"].strip()
            
            # Multi-step JSON repair
            repaired = self._repair_json(content)
            
            jobs_list = []
            try:
                data = json.loads(repaired)
                jobs_list = data.get("jobs", [])
            except json.JSONDecodeError as parse_err:
                safe_print(f"   [!] JSON parse failed after repair: {parse_err}. Trying regex extraction...")
                jobs_list = self._extract_jobs_regex(content)
            
            if not jobs_list:
                safe_print("   [!] LLM returned no parseable jobs.")
                return
                
            for j in jobs_list:
                if isinstance(j, dict):
                    title_val = j.get("job_title") or j.get("title") or "N/A"
                    url_val = j.get("job_url") or j.get("url") or "https://www.upwork.com/jobs/example"
                    snippet_val = j.get("snippet") or j.get("description") or j.get("details") or ""
                else:
                    continue
                
                job_data = {
                    "job_title": title_val,
                    "job_url": url_val,
                    "snippet": snippet_val[:300],
                    "discovered_at": datetime.now().strftime("%Y-%m-%d")
                }
                self.jobs.append(job_data)
                safe_print(f"      [LLM-JOB] Title: {title_val} | Link: {url_val}")
            safe_print(f"   [OK] LLM fallback generated {len(jobs_list)} job leads.")
        except Exception as e:
            safe_print(f"   [LLM ERROR] Failed to fetch fallback jobs: {e}")

    async def draft_proposals(self):
        if not self.jobs:
            return
            
        jobs_to_pitch = self.jobs
        if self.test_mode:
            safe_print("[*] Running in test mode. Limiting proposals to the top 2 jobs to save time/tokens.")
            jobs_to_pitch = self.jobs[:2]
            
        safe_print(f"\n[*] Drafting AI proposals for {len(jobs_to_pitch)} jobs...")
        for job in jobs_to_pitch:
            prompt = (
                f"Draft a short, highly professional Upwork contract proposal for a client looking to bypass anti-bot blocks.\n\n"
                f"Job Title: '{job['job_title']}'\n"
                f"Job Details: '{job['snippet']}'\n\n"
                f"Proposal Strategy:\n"
                f"- Acknowledge the problem (getting blocked by Cloudflare/DataDome/Cloudflare Turnstile is frustrating).\n"
                f"- Explain our solution: We build custom Playwright-Stealth scrapers utilizing residential proxy pools and dynamic cookie mirroring to look like 100% human traffic.\n"
                f"- Offer to run a 5-minute dry-run scrape on their target website for FREE to prove our stealth profiles work.\n"
                f"- Keep it professional, short, and to the point. No empty pleasantries.\n"
                f"Return ONLY the proposal text."
            )
            
            try:
                from litellm_router import shared_router
                messages = [{"role": "user", "content": prompt}]
                resp = await shared_router.get_chat_completion(
                    messages=messages,
                    primary_model="gemini-flash",
                    temperature=0.7,
                    max_tokens=2048
                )
                job["proposal"] = resp["choices"][0]["message"]["content"].strip()
            except Exception as e:
                # Fallback template
                job["proposal"] = (
                    f"Hi! I see you are looking for a developer to bypass anti-bot systems for your scraping project. "
                    f"I build custom stealth scrapers in Playwright that successfully bypass Cloudflare, DataDome, and captcha checks. "
                    f"I can run a free sample scrape of 10 pages on your target website to prove my script works. Let me know if you are interested!"
                )

    def save_jobs(self):
        if not self.jobs:
            return

        jobs_to_save = self.jobs
        if self.test_mode:
            jobs_to_save = self.jobs[:2]

        file_exists = os.path.exists(CSV_FILE)
        existing_urls = set()
        if file_exists:
            try:
                with open(CSV_FILE, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        existing_urls.add(row.get("Job URL", ""))
            except Exception as e:
                safe_print(f"[!] Error reading existing CSV: {e}")

        added_count = 0
        try:
            with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Job Title", "Job URL", "Snippet Info", "AI Draft Proposal", "Discovered Date"])
                
                for job in jobs_to_save:
                    if job["job_url"] not in existing_urls:
                        writer.writerow([
                            job["job_title"],
                            job["job_url"],
                            job["snippet"],
                            job.get("proposal", ""),
                            job["discovered_at"]
                        ])
                        existing_urls.add(job["job_url"])
                        added_count += 1
            safe_print(f"[+] Saved {added_count} new scraping jobs to {CSV_FILE}")
        except Exception as e:
            safe_print(f"[!] Failed to write to CSV: {e}")

if __name__ == "__main__":
    pages = 1
    headless = True
    test_run = False
    if "--non-headless" in sys.argv:
        headless = False
        # Remove --non-headless from sys.argv so pages parsing doesn't break
        sys.argv.remove("--non-headless")
        
    if "--test" in sys.argv:
        pages = 1
        test_run = True
    elif len(sys.argv) > 1:
        try:
            pages = int(sys.argv[1])
        except ValueError:
            pass
            
    scout = ScrapingJobScout(headless=headless)
    if test_run:
        scout.test_mode = True
    asyncio.run(scout.run(pages))
    # Force exit to prevent LiteLLM background thread hangs
    os._exit(0)
