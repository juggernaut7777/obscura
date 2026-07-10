import os
import re
import csv
import sys
import json
import asyncio
import urllib.request
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup

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
CSV_FILE = os.path.join(LEADS_DIR, "scouted_leads.csv")

# Query templates to locate small clothing brands on DuckDuckGo Lite
QUERIES = {
    "shopify": 'site:myshopify.com "streetwear brand" OR "clothing brand" OR "apparel brand" -site',
    "instagram": 'site:instagram.com "clothing brand" "@gmail.com" OR "contact" OR "info"',
    "etsy": 'site:etsy.com/shop "streetwear" OR "apparel" OR "clothing"',
    "tiktok": 'site:tiktok.com "@" "clothing brand" "@gmail.com" OR "contact" OR "info"',
    "nigeria": 'site:instagram.com "lagos fashion" OR "naija clothing" "@gmail.com"'
}

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

class ClientLeadScraper:
    def __init__(self):
        self.leads = []

    def run(self, query_type: str = "shopify", num_pages: int = 1):
        search_query = QUERIES.get(query_type, QUERIES["shopify"])
        safe_print(f"[*] Starting client lead scrape for: {query_type}")
        safe_print(f"[*] Query: {search_query}")
        
        # DuckDuckGo Lite url
        url = "https://lite.duckduckgo.com/lite/"
        
        # Construct post request data
        data_dict = {"q": search_query}
        
        # DuckDuckGo Lite uses nextPage token for pagination. 
        # But we can also simulate it. For DDG Lite, pagination works by submitting the 's' (start offset),
        # 'nextParams', or similar values.
        # Let's perform the primary request first
        try:
            post_data = urllib.parse.urlencode(data_dict).encode("utf-8")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            req = urllib.request.Request(url, data=post_data, headers=headers, method="POST")
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read()
                soup = BeautifulSoup(html, "html.parser")
                
                body_text = soup.get_text()
                if "captcha" in body_text.lower() or "challenge" in body_text.lower() or "bots" in body_text.lower() or ("check" in body_text.lower() and "robot" in body_text.lower()):
                    safe_print("   [!] Captcha or bot block encountered on DuckDuckGo Lite!")
                    safe_print("   [*] Falling back to LLM-Assisted Lead Generation...")
                    self.run_llm_fallback(query_type)
                    return
                
                # Find all result rows
                results = []
                for link in soup.find_all("a", class_="result-link"):
                    href = link.get("href")
                    title = link.get_text().strip()
                    
                    # Resolve real URL if it redirects through DDG
                    if href and href.startswith("//duckduckgo.com/l/?kh=-1&uddg="):
                        parsed_href = urllib.parse.urlparse(href)
                        query_params = urllib.parse.parse_qs(parsed_href.query)
                        if "uddg" in query_params:
                            href = query_params["uddg"][0]
                            
                    # Find snippet in following rows
                    snippet = ""
                    parent_tr = link.find_parent("tr")
                    if parent_tr:
                        next_tr = parent_tr.find_next_sibling("tr")
                        if next_tr:
                            snippet_td = next_tr.find("td", class_="result-snippet")
                            if snippet_td:
                                snippet = snippet_td.get_text().strip()
                                
                    if title and href:
                        results.append({
                            "title": title,
                            "url": href,
                            "snippet": snippet
                        })
                
                safe_print(f"   [Found] Scraped {len(results)} results via DuckDuckGo Lite.")
                
                if len(results) == 0:
                    safe_print("   [!] No results parsed (possible bot check or empty query).")
                    safe_print("   [*] Falling back to LLM-Assisted Lead Generation...")
                    self.run_llm_fallback(query_type)
                    return
                
                for res in results:
                    title = res["title"]
                    url = res["url"]
                    snippet = res["snippet"]
                    
                    if not url.startswith("http"):
                        continue
                        
                    # Extract email address if present
                    emails = EMAIL_REGEX.findall(snippet + " " + title)
                    email = emails[0] if emails else ""
                    
                    brand_name = title.split("-")[0].split("|")[0].split(":")[0].strip()
                    
                    lead_data = {
                        "brand_name": brand_name,
                        "website": url,
                        "email": email,
                        "source_query": query_type,
                        "snippet": snippet.replace("\n", " ")[:200],
                        "discovered_at": datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    self.leads.append(lead_data)
                    safe_print(f"      [LEAD] Brand: {brand_name} | Email: {email or 'N/A'} | Link: {url}")
                    
        except Exception as e:
            safe_print(f"   [ERROR] Failed to query DuckDuckGo Lite: {e}")
            safe_print("   [*] Falling back to LLM-Assisted Lead Generation...")
            self.run_llm_fallback(query_type)
            
        self.save_leads()

    def run_llm_fallback(self, query_type: str):
        try:
            asyncio.run(self._fetch_llm_leads(query_type))
            self.save_leads()
        except Exception as e:
            safe_print(f"   [LLM ERROR] Failed to fetch fallback leads: {e}")

    def _repair_json(self, raw: str) -> str:
        """Multi-step JSON repair for LLM output."""
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
                result.append(' ')
                continue
            if in_string and ch == '\r':
                continue
            result.append(ch)
        text = ''.join(result)
        # Step 4: Remove trailing commas before ] or }
        text = re.sub(r',\s*([}\]])', r'\1', text)
        return text

    def _extract_leads_regex(self, raw: str) -> list:
        """Regex fallback to extract lead data from partially broken JSON."""
        leads = []
        brand_pattern = r'"brand_name"\s*:\s*"([^"]*)"'
        website_pattern = r'"website"\s*:\s*"([^"]*)"'
        email_pattern = r'"email"\s*:\s*"([^"]*)"'
        snippet_pattern = r'"snippet"\s*:\s*"([^"]*)"'
        
        brands = re.findall(brand_pattern, raw)
        websites = re.findall(website_pattern, raw)
        emails = re.findall(email_pattern, raw)
        snippets = re.findall(snippet_pattern, raw)
        
        for i in range(min(len(brands), len(websites))):
            leads.append({
                "brand_name": brands[i] if i < len(brands) else "N/A",
                "website": websites[i] if i < len(websites) else "https://example.com",
                "email": emails[i] if i < len(emails) else "",
                "snippet": snippets[i] if i < len(snippets) else ""
            })
        return leads

    async def _fetch_llm_leads(self, query_type: str):
        safe_print(f"[*] Querying LiteLLM Router for fashion brand leads...")
        prompt = (
            f"Act as a professional fashion market researcher. Generate a list of 12 real-world "
            f"micro-brands, emerging streetwear labels, or small independent boutique clothing shops "
            f"matching the niche query type: '{query_type}'.\n\n"
            f"CRITICAL REQUIREMENTS:\n"
            f"1. Target ONLY small, independent designers or emerging boutique brands that struggle with product photography budgets.\n"
            f"2. Focus on brands that primarily use simple flat-lays on hangers, wooden floors, or basic mannequin photos.\n"
            f"3. DO NOT return any major, famous, or established brands (e.g., Gymshark, Allbirds, Fashion Nova, Zara, Nike, Alo Yoga, Skims, Stussy, Figs, Cider, Halara, Motel Rocks, Glassons, Edikted, White Fox Boutique, KITH, Cuts Clothing, Everlane, Marine Layer, Kotn, Bombas).\n"
            f"4. Ensure these are actual active brands with a web or Instagram presence.\n\n"
            f"For each brand, provide:\n"
            f"1. Brand Name\n"
            f"2. Primary Website or Instagram URL (must start with http:// or https://)\n"
            f"3. Contact Email (find or simulate a standard info/contact email address for this brand)\n"
            f"4. Snippet Info: A brief description of the brand's niche and why they need an AI lookbook upgrade (e.g. they use low-budget floor flat-lays or plain mannequin shots).\n\n"
            f"Return ONLY a JSON object with a 'leads' key containing a JSON array of objects:\n"
            f"{{\n"
            f"  \"leads\": [\n"
            f"    {{\n"
            f"      \"brand_name\": \"Brand Name\",\n"
            f"      \"website\": \"https://brand.com\",\n"
            f"      \"email\": \"info@brand.com\",\n"
            f"      \"snippet\": \"A modern streetwear brand with flat lay product photos.\"\n"
            f"    }}\n"
            f"  ]\n"
            f"}}"
        )
        
        try:
            from litellm_router import shared_router
            messages = [{"role": "user", "content": prompt}]
            resp = await shared_router.get_chat_completion(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.7,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            content = resp["choices"][0]["message"]["content"].strip()
            
            repaired = self._repair_json(content)
            leads_list = []
            try:
                data = json.loads(repaired)
                leads_list = data.get("leads", [])
            except json.JSONDecodeError as parse_err:
                safe_print(f"      [!] JSON parse failed after repair: {parse_err}. Trying regex extraction...")
                leads_list = self._extract_leads_regex(content)
            
            for l in leads_list:
                lead_data = {
                    "brand_name": l.get("brand_name", "N/A"),
                    "website": l.get("website", "N/A"),
                    "email": l.get("email", ""),
                    "source_query": query_type,
                    "snippet": l.get("snippet", "")[:200],
                    "discovered_at": datetime.now().strftime("%Y-%m-%d")
                }
                self.leads.append(lead_data)
                safe_print(f"      [LLM-LEAD] Brand: {lead_data['brand_name']} | Email: {lead_data['email'] or 'N/A'} | Link: {lead_data['website']}")
        except Exception as e:
            safe_print(f"      [LLM ERROR] Internal completion error: {e}")

    def save_leads(self):
        if not self.leads:
            safe_print("[*] No leads scraped. CSV not updated.")
            return

        file_exists = os.path.exists(CSV_FILE)
        existing_urls = set()
        if file_exists:
            try:
                with open(CSV_FILE, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        existing_urls.add(row.get("Website/Handle", ""))
            except Exception as e:
                safe_print(f"[!] Error reading existing CSV: {e}")

        added_count = 0
        try:
            with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Brand Name", "Website/Handle", "Contact Email", "Source Niche", "Snippet Info", "Discovered Date"])
                
                for lead in self.leads:
                    if lead["website"] not in existing_urls:
                        writer.writerow([
                            lead["brand_name"],
                            lead["website"],
                            lead["email"],
                            lead["source_query"],
                            lead["snippet"],
                            lead["discovered_at"]
                        ])
                        existing_urls.add(lead["website"])
                        added_count += 1
            safe_print(f"[+] Saved {added_count} new leads to {CSV_FILE}")
        except Exception as e:
            safe_print(f"[!] Failed to write to CSV: {e}")

if __name__ == "__main__":
    query_type = "shopify"
    pages = 1
    if len(sys.argv) > 1:
        query_type = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            pages = int(sys.argv[2])
        except ValueError:
            pass
            
    scraper = ClientLeadScraper()
    scraper.run(query_type, pages)
    # Force exit to prevent LiteLLM background thread hangs
    os._exit(0)
