"""
REDDIT SOURCING AGENT
=====================
Scrapes top replica subreddits (r/QualityReps, r/DesignerReps) for Weidian, Taobao, and Yupoo links.
Sends a "🔥 REDDIT RADAR" alert to Discord with 1-click Kakobuy links.
"""

import os
import re
import json
import time
import asyncio
import urllib.parse
from datetime import datetime
from playwright.async_api import async_playwright

DISCORD_REVIEW_CHANNEL = os.getenv("DISCORD_REVIEW_CHANNEL", "")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

# Subreddits to scan
SUBREDDITS = ["QualityReps", "DesignerReps", "FashionReps"]

# Search queries for the aesthetic
QUERIES = [
    "corteiz spreadsheet",
    "margiela finds",
    "balenciaga best batch",
    "acne studios tee",
    "loewe spreadsheet",
    "chrome hearts finds"
]

async def send_discord_alert(post_title, post_url, extracted_links):
    """Send the discovered links to Discord."""
    try:
        import aiohttp
    except ImportError:
        return

    if not DISCORD_TOKEN or not DISCORD_REVIEW_CHANNEL:
        print("[!] Discord credentials not set.")
        return

    lines = [
        f"🔥 **REDDIT RADAR ALERT** 🔥",
        f"**Found in:** {post_title}",
        f"🔗 **Source:** <{post_url}>",
        ""
    ]

    for link_type, url in extracted_links:
        if "weidian.com" in url or "taobao.com" in url:
            encoded = urllib.parse.quote(url, safe='')
            kakobuy_url = f"https://www.kakobuy.com/item/details?url={encoded}"
            lines.append(f"🛒 **Kakobuy ({link_type}):** {kakobuy_url}")
            lines.append(f"   Raw: <{url}>")
        else:
            lines.append(f"📂 **Yupoo Album:** <{url}>")

    if len(lines) == 4:
        return # No links found

    message_text = "\n".join(lines)
    url = f"https://discord.com/api/v10/channels/{DISCORD_REVIEW_CHANNEL}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json={"content": message_text}) as resp:
            if resp.status == 200:
                print(f"[+] Sent Discord alert for: {post_title}")
            else:
                print(f"[!] Failed to send Discord alert: {resp.status} {await resp.text()}")

async def scrape_reddit():
    print("[*] Starting Reddit Sourcing Agent...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for subreddit in SUBREDDITS:
            for query in QUERIES:
                print(f"[*] Scanning r/{subreddit} for '{query}'...")
                search_url = f"https://old.reddit.com/r/{subreddit}/search?q={urllib.parse.quote(query)}&restrict_sr=on&sort=new&t=month"
                
                try:
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Extract top 3 post links
                    post_links = await page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('.search-result-header > a')).slice(0, 3).map(a => {
                            return { title: a.innerText, url: a.href };
                        });
                    }''')

                    for post in post_links:
                        print(f"  [-] Checking post: {post['title']}")
                        await page.goto(post['url'], wait_until="domcontentloaded", timeout=20000)
                        
                        # Extract text content
                        content = await page.evaluate('() => document.body.innerText')
                        
                        extracted = []
                        # Find Weidian links
                        weidian_matches = set(re.findall(r'(https?://weidian\.com/[^\s)]+)', content))
                        for w in weidian_matches: extracted.append(("Weidian", w))
                        
                        # Find Taobao links
                        taobao_matches = set(re.findall(r'(https?://item\.taobao\.com/[^\s)]+)', content))
                        for t in taobao_matches: extracted.append(("Taobao", t))

                        # Find Yupoo links
                        yupoo_matches = set(re.findall(r'(https?://[a-zA-Z0-9-]+\.x\.yupoo\.com/[^\s)]+)', content))
                        for y in yupoo_matches: extracted.append(("Yupoo", y))

                        if extracted:
                            print(f"  [+] Found {len(extracted)} links! Sending alert...")
                            await send_discord_alert(post['title'], post['url'], extracted)
                        
                        await asyncio.sleep(2) # Be nice to Reddit
                        
                except Exception as e:
                    print(f"[!] Error scanning {query}: {e}")
                
                await asyncio.sleep(5)
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_reddit())
