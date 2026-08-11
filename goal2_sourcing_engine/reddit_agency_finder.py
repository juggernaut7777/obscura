import os
import re
import csv
import sys
import json
import asyncio
import httpx
from datetime import datetime
from dotenv import load_dotenv

# Load env variables
load_dotenv()

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
CSV_FILE = os.path.join(LEADS_DIR, "agency_leads.csv")

# Targeted subreddits where agency owners discuss sales/leads
SUBREDDITS = ["agency", "sales", "marketing", "copywriting"]

# Keywords indicating they are looking for clients/leads (broader keywords for higher match rates)
INTENT_KEYWORDS = [
    "get clients", "getting clients", "find leads", "finding leads",
    "cold email", "cold outreach", "struggling to find", "lead generation",
    "new clients", "client acquisition", "agency growth", "sales funnel",
    "client", "lead", "outreach", "sales", "revenue", "outbound", "pitch"
]

async def fetch_subreddit_posts(subreddit: str, limit: int = 50) -> list:
    url_template = f"https://old.reddit.com/r/{subreddit}/new.json?limit={limit}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    }
    
    safe_print(f"[*] Scanning r/{subreddit} for agency leads...")
    
    # ── Strategy 1: JSON API ──
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url_template)
            if resp.status_code == 200:
                data = resp.json()
                posts = data.get("data", {}).get("children", [])
                if posts:
                    safe_print(f"   [r/{subreddit}] JSON OK")
                    return posts
    except Exception as e:
        safe_print(f"   [r/{subreddit}] JSON attempt failed: {e}")
        
    # ── Strategy 2: RSS Feed Fallback (never blocks) ──
    safe_print(f"   [r/{subreddit}] Falling back to RSS feed...")
    try:
        rss_url = f"https://www.reddit.com/r/{subreddit}/new.rss?limit={limit}"
        async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
            resp = await client.get(rss_url)
            if resp.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall(".//atom:entry", ns) or root.findall(".//entry")
                posts = []
                for entry in entries[:limit]:
                    title_el = entry.find("atom:title", ns)
                    if title_el is None:
                        title_el = entry.find("title")
                    content_el = entry.find("atom:content", ns)
                    if content_el is None:
                        content_el = entry.find("content")
                    author_el = entry.find(".//atom:author/atom:name", ns)
                    if author_el is None:
                        author_el = entry.find(".//author/name")
                    link_el = entry.find("atom:link", ns)
                    if link_el is None:
                        link_el = entry.find("link")
                    
                    title = title_el.text if title_el is not None else ""
                    content = content_el.text if content_el is not None else ""
                    author = author_el.text if author_el is not None else "Unknown"
                    author = author.replace("/u/", "").replace("u/", "")
                    permalink = link_el.attrib.get("href", "") if link_el is not None else ""
                    
                    posts.append({
                        "data": {
                            "title": title,
                            "selftext": content,
                            "author": author,
                            "permalink": permalink.replace("https://www.reddit.com", ""),
                            "created_utc": datetime.now().timestamp()
                        }
                    })
                if posts:
                    safe_print(f"   [r/{subreddit}] RSS feed loaded {len(posts)} posts successfully.")
                    return posts
    except Exception as e:
        safe_print(f"   [r/{subreddit}] RSS attempt failed: {e}")
        
    return []




def filter_intent_posts(posts: list) -> list:
    leads = []
    for post in posts:
        post_data = post.get("data", {})
        title = post_data.get("title", "")
        selftext = post_data.get("selftext", "")
        author = post_data.get("author", "")
        permalink = post_data.get("permalink", "")
        created_utc = post_data.get("created_utc", 0)
        
        # Skip deleted or automod posts
        if not author or author.lower() in ["deleted", "automoderator"]:
            continue
            
        full_text = (title + " " + selftext).lower()
        
        # Check if any keyword matches
        matched_kw = None
        for kw in INTENT_KEYWORDS:
            if kw in full_text:
                matched_kw = kw
                break
                
        if matched_kw:
            leads.append({
                "username": f"u/{author}",
                "post_title": title,
                "post_url": f"https://reddit.com{permalink}",
                "matched_keyword": matched_kw,
                "created_date": datetime.fromtimestamp(created_utc).strftime("%Y-%m-%d"),
                "post_text": selftext[:300] + "..." if len(selftext) > 300 else selftext
            })
            
    return leads

async def draft_pitch_with_ai(lead: dict) -> str:
    """Uses Gemini via LiteLLM router to draft a hyper-personalized Reddit pitch."""
    prompt = (
        f"Draft a hyper-personalized Reddit private message pitching a 'Reddit Lead Monitoring Tool'.\n\n"
        f"The user ({lead['username']}) posted a thread titled: '{lead['post_title']}'.\n"
        f"Context from post: '{lead['post_text']}'\n\n"
        f"Pitch Strategy:\n"
        f"- Reference their post naturally (don't sound like a spam bot).\n"
        f"- Sympathize with their struggle to find clients.\n"
        f"- Offer to send them 3 warm leads we just scraped for their niche for FREE to prove value.\n"
        f"- Keep it conversational, short, and friendly. No sales speak.\n"
        f"Return ONLY the drafted message content."
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
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # Fallback template
        return (
            f"Hey {lead['username']}! Saw your thread about '{lead['post_title']}'. "
            f"I run a tool that monitors Reddit for B2B leads in real-time. "
            f"Would you be open to me sending you 3 warm client leads for free this week to check it out? "
            f"Let me know what your niche is. Cheers!"
        )

async def main():
    test_mode = "--test" in sys.argv
    all_leads = []
    
    for sub in SUBREDDITS:
        posts = await fetch_subreddit_posts(sub, limit=30 if test_mode else 100)
        leads = filter_intent_posts(posts)
        safe_print(f"   [FOUND] {len(leads)} potential buyers in r/{sub}")
        all_leads.extend(leads)
        await asyncio.sleep(1.0)
        
    if not all_leads:
        safe_print("[*] No target agency owners found in this run.")
        return

    # Draft AI pitches for a subset of leads, or all leads when not testing
    limit_ai = 3 if test_mode else len(all_leads)
    safe_print(f"\n[*] Drafting AI pitches for the top {limit_ai} leads...")
    
    for idx, lead in enumerate(all_leads[:limit_ai]):
        safe_print(f"   -> Pitching u/{lead['username']} for: '{lead['post_title'][:40]}...'")
        pitch = await draft_pitch_with_ai(lead)
        lead["draft_pitch"] = pitch
        
    # Write to CSV
    file_exists = os.path.exists(CSV_FILE)
    written = 0
    try:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Username", "Post Title", "Post URL", "Matched Keyword", "Created Date", "AI Draft Pitch"])
            
            for lead in all_leads[:limit_ai]:
                writer.writerow([
                    lead["username"],
                    lead["post_title"],
                    lead["post_url"],
                    lead["matched_keyword"],
                    lead["created_date"],
                    lead.get("draft_pitch", "")
                ])
                written += 1
        safe_print(f"[+] Successfully saved {written} warm agency leads to {CSV_FILE}")
    except Exception as e:
        safe_print(f"[!] Failed to write to CSV: {e}")

if __name__ == "__main__":
    asyncio.run(main())
    # Force exit to prevent LiteLLM background thread hangs
    os._exit(0)
