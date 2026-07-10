import os
import re
import csv
import sys
import asyncio
import httpx
import random
from bs4 import BeautifulSoup
from datetime import datetime

# Safe print for Windows
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

# Folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEADS_DIR = os.path.join(BASE_DIR, "brand_leads")
os.makedirs(LEADS_DIR, exist_ok=True)
CSV_FILE = os.path.join(LEADS_DIR, "scraping_jobs.csv")

# Subreddits related to web scraping, coding, Python, and freelance jobs
SUBREDDITS = ["webscraping", "scraping", "python", "node", "freelance"]

# Keywords indicating they are looking for a scraper, getting blocked, or need assistance
INTENT_KEYWORDS = [
    "cloudflare", "bypass", "captcha", "anti-bot", "blocked", "datadome",
    "need a scraper", "hire a scraper", "scraping project", "write a scraper",
    "datadome bypass", "turnstile", "imperva", "distil", "scraping help"
]

async def fetch_subreddit_posts_html(subreddit: str) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    
    url = f"https://old.reddit.com/r/{subreddit}/new/"
    safe_print(f"[*] Scanning r/{subreddit} via HTML Scrape...")
    
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                things = soup.find_all("div", class_="thing")
                
                posts = []
                for thing in things:
                    author = thing.get("data-author", "Unknown")
                    title_a = thing.find("a", class_="title")
                    title = title_a.get_text() if title_a else ""
                    link = title_a.get("href") if title_a else ""
                    if link.startswith("/r/"):
                        link = f"https://reddit.com{link}"
                        
                    posts.append({
                        "author": author,
                        "title": title,
                        "link": link
                    })
                safe_print(f"   [r/{subreddit}] Successfully loaded {len(posts)} posts from HTML.")
                return posts
            else:
                safe_print(f"   [r/{subreddit}] Failed with status code: {resp.status_code}")
    except Exception as e:
        safe_print(f"   [r/{subreddit}] HTML attempt failed: {e}")
        
    return []

def filter_intent_posts(posts: list) -> list:
    leads = []
    for post in posts:
        title = post.get("title", "")
        author = post.get("author", "")
        link = post.get("link", "")
        
        if not author or author.lower() in ["deleted", "automoderator"]:
            continue
            
        full_text = title.lower()
        
        matched_kw = None
        for kw in INTENT_KEYWORDS:
            if kw in full_text:
                matched_kw = kw
                break
                
        if matched_kw:
            # Clean title
            job_title = title.split("-")[0].split("|")[0].split(":")[0].strip()
            
            leads.append({
                "job_title": f"[Reddit] {job_title}",
                "job_url": link,
                "snippet": f"User u/{author} posted about: {title}",
                "matched_keyword": matched_kw,
                "discovered_at": datetime.now().strftime("%Y-%m-%d")
            })
            
    return leads

async def draft_proposals(leads: list):
    if not leads:
        return
        
    safe_print(f"\n[*] Drafting AI proposals for {len(leads)} Reddit leads...")
    
    try:
        from litellm_router import shared_router
    except ImportError:
        safe_print("[!] LiteLLM router wrapper not found. Using fallback proposals.")
        for lead in leads:
            lead["proposal"] = (
                f"Hi! If you are getting blocked by Cloudflare or Turnstile, standard Playwright/Selenium will fail. "
                f"You need to use playwright-stealth and configure your fingerprints properly. "
                f"I've built custom bypass scrapers for this; feel free to PM me the target URL, and I can run a free test extraction for you."
            )
        return

    for lead in leads:
        prompt = (
            f"Draft a short, helpful, and highly professional response to a Reddit user experiencing issues bypass blocking systems during scraping.\n\n"
            f"User Post Title: '{lead['job_title']}'\n"
            f"Post content snippet: '{lead['snippet']}'\n\n"
            f"Strategy:\n"
            f"- Acknowledge their issue (getting blocked or dealing with cloudflare/anti-bots).\n"
            f"- Propose a technical explanation/fix: Using Playwright-Stealth, dynamic finger-printing override, and rotating residential proxies.\n"
            f"- Offer to test a quick run on their target site for free to demonstrate our working bypass system.\n"
            f"- Keep it extremely polite, professional, and concise. Do not use generic bot greetings.\n"
            f"Return ONLY the comment/message text."
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            resp = await shared_router.get_chat_completion(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.7,
                max_tokens=2048
            )
            lead["proposal"] = resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            safe_print(f"   [!] LiteLLM failed for lead: {lead['job_title']}. Error: {e}")
            lead["proposal"] = (
                f"Hi! If you are getting blocked by Cloudflare or Turnstile, standard Playwright/Selenium will fail. "
                f"You need to use playwright-stealth and configure your fingerprints properly. "
                f"I've built custom bypass scrapers for this; feel free to PM me the target URL, and I can run a free test extraction for you."
            )

def save_leads(leads: list):
    if not leads:
        return

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
            
            for lead in leads:
                if lead["job_url"] not in existing_urls:
                    writer.writerow([
                        lead["job_title"],
                        lead["job_url"],
                        lead["snippet"],
                        lead.get("proposal", ""),
                        lead["discovered_at"]
                    ])
                    existing_urls.add(lead["job_url"])
                    added_count += 1
        safe_print(f"[+] Saved {added_count} new scraping jobs from Reddit to {CSV_FILE}")
    except Exception as e:
        safe_print(f"[!] Failed to write to CSV: {e}")

async def main():
    all_leads = []
    
    for sub in SUBREDDITS:
        posts = await fetch_subreddit_posts_html(sub)
        leads = filter_intent_posts(posts)
        safe_print(f"   [FOUND] {len(leads)} matching posts in r/{sub}")
        all_leads.extend(leads)
        await asyncio.sleep(2.0 + random.random() * 2.0)
        
    if not all_leads:
        safe_print("[*] No target threads found on Reddit in this run.")
        return
        
    await draft_proposals(all_leads)
    save_leads(all_leads)

if __name__ == "__main__":
    asyncio.run(main())
    # Force exit to prevent LiteLLM background thread hangs
    os._exit(0)
