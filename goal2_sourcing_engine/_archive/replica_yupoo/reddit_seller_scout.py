"""
Reddit Seller Scout
====================
Mines r/FashionReps, r/DesignerReps, r/RepLadies for:
  1. Trending Yupoo seller subdomains → adds to SELLERS list
  2. Direct Yupoo album URLs → auto-triggers contact sheet scraping
  3. Trending product searches (what people are asking for)

Uses Reddit's public JSON API — no API key, no account required.
"""
import os
import re
import json
import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REDDIT_SELLERS_CACHE = os.path.join(BASE_DIR, "data", "reddit_discovered_sellers.json")
os.makedirs(os.path.dirname(REDDIT_SELLERS_CACHE), exist_ok=True)

# Subreddits to mine
SUBREDDITS = [
    "FashionReps",
    "DesignerReps",
    "RepLadies",
    "QualityReps",
    "Repsneakers",
]

# Patterns to find Yupoo links in Reddit posts/comments
YUPOO_PATTERN = re.compile(
    r'https?://([a-zA-Z0-9\-]+)\.x\.yupoo\.com(?:/[^\s\)\]\>\"\'\,]*)?',
    re.IGNORECASE
)
WEIDIAN_PATTERN = re.compile(
    r'https?://(?:weidian\.com|k\.youshop10\.com|detail\.tmall\.com)[^\s\)\]\>\"\'\,]*',
    re.IGNORECASE
)

# Keywords that indicate a quality post worth mining
HOT_KEYWORDS = [
    "hoodie", "tracksuit", "cargo", "set", "jacket", "puffer", "fleece",
    "bag", "tote", "crossbody", "backpack", "wallet", "belt",
    "balenciaga", "essentials", "fear of god", "corteiz", "palace", "supreme",
    "acne", "loewe", "stone island", "cp company", "moncler",
    "w2c", "find", "seller", "best seller", "rep", "haul", "qc", "pickup"
]

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))


def load_discovered_sellers() -> Dict[str, Any]:
    """Load previously discovered sellers from cache."""
    if os.path.exists(REDDIT_SELLERS_CACHE):
        try:
            with open(REDDIT_SELLERS_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"sellers": {}, "products": [], "last_scraped": None}


def save_discovered_sellers(data: Dict[str, Any]):
    """Save discovered sellers to cache."""
    data["last_scraped"] = datetime.now().isoformat()
    with open(REDDIT_SELLERS_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def fetch_subreddit_hot(subreddit: str, limit: int = 50) -> List[Dict]:
    """
    Fetch hot posts from a subreddit.
    Strategy:
      1. Try old.reddit.com JSON (less restricted, no OAuth)
      2. Fall back to RSS parsing via feedparser
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    }
    
    # ── Strategy 1: old.reddit.com JSON (more permissive than new site) ──
    for url_template in [
        f"https://old.reddit.com/r/{subreddit}/hot.json?limit={limit}",
        f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}&raw_json=1",
    ]:
        try:
            async with httpx.AsyncClient(
                timeout=20.0,
                headers=headers,
                follow_redirects=True,
            ) as client:
                resp = await client.get(url_template)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        posts = data.get("data", {}).get("children", [])
                        if posts:
                            safe_print(f"   [r/{subreddit}] JSON OK ({url_template[:40]})")
                            return [p["data"] for p in posts]
                    except Exception:
                        pass  # Try next strategy
                elif resp.status_code == 429:
                    safe_print(f"   [r/{subreddit}] Rate limited, backing off 5s...")
                    await asyncio.sleep(5)
        except Exception as e:
            safe_print(f"   [r/{subreddit}] JSON attempt failed: {type(e).__name__}")
        await asyncio.sleep(1)

    # ── Strategy 2: RSS feed (always public, no auth) ──
    try:
        rss_url = f"https://www.reddit.com/r/{subreddit}/hot.rss?limit={limit}"
        async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
            resp = await client.get(rss_url)
            if resp.status_code == 200:
                # Parse RSS manually (simple, no feedparser dependency)
                import xml.etree.ElementTree as ET
                try:
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
                        title = title_el.text if title_el is not None else ""
                        content = content_el.text if content_el is not None else ""
                        posts.append({
                            "title": title,
                            "selftext": content,
                            "id": "",
                            "ups": 50,  # Unknown from RSS, use default
                            "subreddit": subreddit,
                        })
                    if posts:
                        safe_print(f"   [r/{subreddit}] RSS OK — got {len(posts)} entries")
                        return posts
                except ET.ParseError:
                    pass
    except Exception as e:
        safe_print(f"   [r/{subreddit}] RSS attempt failed: {type(e).__name__}")

    # ── Strategy 3: Scrape old.reddit.com HTML for links ──
    try:
        html_url = f"https://old.reddit.com/r/{subreddit}/hot/"
        async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
            resp = await client.get(html_url)
            if resp.status_code == 200 and "yupoo" in resp.text.lower():
                # Extract post titles and URLs directly from HTML
                title_pattern = re.compile(r'<a[^>]+class="[^"]*title[^"]*"[^>]*>([^<]+)</a>', re.IGNORECASE)
                titles = title_pattern.findall(resp.text)
                posts = [{"title": t, "selftext": "", "id": "", "ups": 10} for t in titles[:limit]]
                # Also extract all yupoo links from the HTML
                yupoo_text = resp.text
                posts.append({"title": f"r/{subreddit} HTML scrape", "selftext": yupoo_text[:5000], "id": "", "ups": 50})
                safe_print(f"   [r/{subreddit}] HTML scrape OK — {len(posts)} items")
                return posts
    except Exception as e:
        safe_print(f"   [r/{subreddit}] HTML scrape failed: {type(e).__name__}")

    safe_print(f"   [r/{subreddit}] All strategies failed — skipping this subreddit")
    return []


async def fetch_post_comments(subreddit: str, post_id: str, limit: int = 100) -> List[str]:
    """Fetch comment bodies from a single Reddit post."""
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 FashionBot/1.0"}
    texts = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1:
                    comments = data[1].get("data", {}).get("children", [])
                    for c in comments:
                        body = c.get("data", {}).get("body", "")
                        if body:
                            texts.append(body)
    except Exception as e:
        safe_print(f"[REDDIT] Error fetching comments for {post_id}: {e}")
    return texts


def extract_yupoo_sellers_from_text(text: str) -> List[Dict[str, str]]:
    """Extract all unique Yupoo subdomain sellers from a block of text."""
    sellers = []
    matches = YUPOO_PATTERN.findall(text)
    full_matches = YUPOO_PATTERN.finditer(text)
    
    seen = set()
    for m in full_matches:
        subdomain = m.group(1).lower()
        full_url = m.group(0)
        
        if subdomain in seen:
            continue
        seen.add(subdomain)
        
        # Filter out generic yupoo domains
        if subdomain in ("www", "x", "app", "mobile"):
            continue
        
        sellers.append({
            "subdomain": subdomain,
            "base_url": f"https://{subdomain}.x.yupoo.com",
            "albums_url": f"https://{subdomain}.x.yupoo.com/albums",
            "example_link": full_url,
        })
    
    return sellers


import html as html_module

def strip_html(text: str) -> str:
    """Strip HTML tags and decode HTML entities from a string."""
    # Decode HTML entities first (&lt; → <, &amp; → &, etc.)
    text = html_module.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def score_post_relevance(post: Dict) -> float:
    """Score a Reddit post for sourcing relevance (0.0 - 1.0). Used to prioritize comment mining."""
    raw = post.get("title", "") + " " + post.get("selftext", "")
    title = strip_html(raw).lower()
    score = 0.0
    
    # Upvotes signal quality (RSS posts default to 50)
    ups = post.get("ups", 0)
    score += min(ups / 500, 0.3)   # Lower denominator → RSS posts get more score
    
    # Keyword matches
    matches = sum(1 for kw in HOT_KEYWORDS if kw in title)
    score += min(matches * 0.07, 0.4)
    
    # Contains Yupoo links (in title OR body)
    if YUPOO_PATTERN.search(title):
        score += 0.4
    
    return min(score, 1.0)


async def run_reddit_scout(max_sellers: int = 30, min_relevance: float = 0.3) -> Dict[str, Any]:
    """
    Main Reddit sourcing run.
    Returns dict with newly discovered sellers and trending product searches.
    
    Key change: we scan ALL posts for Yupoo links (not just high-score ones).
    Relevance score is only used to decide whether to also mine comments.
    """
    safe_print(f"\n[REDDIT SCOUT] Starting Reddit seller discovery...")
    safe_print(f"   Scanning: {', '.join(['r/' + s for s in SUBREDDITS])}")
    
    cache = load_discovered_sellers()
    known_subdomains = set(cache["sellers"].keys())
    new_sellers = {}
    trending_searches = []
    direct_album_urls = []
    total_posts_scanned = 0
    
    for subreddit in SUBREDDITS:
        safe_print(f"\n   [r/{subreddit}] Fetching hot posts...")
        posts = await fetch_subreddit_hot(subreddit, limit=50)
        safe_print(f"   [r/{subreddit}] Got {len(posts)} posts — scanning all for Yupoo links")
        total_posts_scanned += len(posts)
        
        # ⚡ Bolt: Use a semaphore to limit concurrency for comment fetching to prevent rate limiting
        semaphore = asyncio.Semaphore(5)

        async def fetch_comments_for_post(post):
            relevance = score_post_relevance(post)
            post_id = post.get("id", "")
            if relevance >= min_relevance and post_id:
                async with semaphore:
                    return await fetch_post_comments(subreddit, post_id, limit=50)
            return []

        # ⚡ Bolt: Execute comment fetching concurrently instead of sequentially to eliminate N+1 bottleneck
        all_post_comments = await asyncio.gather(*(fetch_comments_for_post(post) for post in posts))

        for post, comments in zip(posts, all_post_comments):
            title = post.get("title", "")
            raw_body = post.get("selftext", "")
            post_id = post.get("id", "")
            
            # Strip HTML from RSS content before processing
            body = strip_html(raw_body)
            full_text = title + " " + body
            
            # ── Always scan every post for Yupoo seller subdomains ──
            sellers = extract_yupoo_sellers_from_text(full_text)
            for s in sellers:
                subdomain = s["subdomain"]
                if subdomain not in known_subdomains and subdomain not in new_sellers:
                    new_sellers[subdomain] = {
                        **s,
                        "source": f"r/{subreddit}",
                        "post_title": title[:80],
                        "post_score": post.get("ups", 0),
                        "discovered_at": datetime.now().isoformat()
                    }
                    safe_print(f"   [NEW SELLER] {subdomain}.x.yupoo.com  ← r/{subreddit}: '{title[:50]}'")
            
            # ── Always collect direct album/category URLs ──
            for m in YUPOO_PATTERN.finditer(full_text):
                url = m.group(0)
                if "/albums" in url or "/categories" in url:
                    direct_album_urls.append({
                        "url": url,
                        "source": f"r/{subreddit}: {title[:60]}"
                    })
            
            # ── Mine comments on high-relevance posts ──
            for comment in comments:
                comment_text = strip_html(comment)
                sellers_in_comment = extract_yupoo_sellers_from_text(comment_text)
                for s in sellers_in_comment:
                    subdomain = s["subdomain"]
                    if subdomain not in known_subdomains and subdomain not in new_sellers:
                        new_sellers[subdomain] = {
                            **s,
                            "source": f"r/{subreddit} [comment]",
                            "post_title": title[:80],
                            "discovered_at": datetime.now().isoformat()
                        }
                        safe_print(f"   [NEW SELLER via comment] {subdomain}.x.yupoo.com")
            
            # ── Capture trending W2C searches ──
            title_lower = title.lower()
            if any(kw in title_lower for kw in ["w2c", "looking for", "anyone know", "can someone find"]):
                trending_searches.append({
                    "query": title[:100],
                    "ups": post.get("ups", 0),
                    "subreddit": subreddit
                })
        
        # Respect Reddit rate limits
        await asyncio.sleep(1.5)
    
    # Deduplicate direct_album_urls
    seen_urls = set()
    unique_albums = []
    for item in direct_album_urls:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            unique_albums.append(item)
    
    # Update cache
    cache["sellers"].update(new_sellers)
    cache["products"] = unique_albums[-100:]   # Keep last 100 unique album URLs
    cache["trending_searches"] = sorted(trending_searches, key=lambda x: x["ups"], reverse=True)[:20]
    save_discovered_sellers(cache)
    
    # ── Export to CSV Spreadsheet for manual review ──
    csv_path = os.path.join(BASE_DIR, "data", "reddit_discovered_sellers.csv")
    try:
        import csv
        file_exists = os.path.exists(csv_path)
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Subdomain", "Base URL", "Albums URL", "Source", "Post Title", "Discovered At"])
            for sub, info in new_sellers.items():
                writer.writerow([
                    sub, 
                    info.get("base_url", ""), 
                    info.get("albums_url", ""), 
                    info.get("source", ""), 
                    info.get("post_title", ""), 
                    info.get("discovered_at", "")
                ])
        safe_print(f"   [CSV] Exported {len(new_sellers)} new sellers to {csv_path}")
    except Exception as e:
        safe_print(f"   [CSV ERROR] Failed to export to CSV: {e}")
    
    safe_print(f"\n[REDDIT SCOUT] Complete!")
    safe_print(f"   Posts scanned: {total_posts_scanned}")
    safe_print(f"   New sellers discovered: {len(new_sellers)}")
    safe_print(f"   Direct album URLs found: {len(unique_albums)}")
    safe_print(f"   Trending W2C searches: {len(trending_searches)}")
    safe_print(f"   Total known sellers (cumulative): {len(cache['sellers'])}")
    
    return {
        "new_sellers": new_sellers,
        "direct_album_urls": unique_albums,
        "trending_searches": trending_searches,
        "total_known": len(cache["sellers"])
    }


def get_all_discovered_sellers() -> List[Dict]:
    """
    Returns all Reddit-discovered sellers as a list compatible with SELLERS format.
    Called by the scraping engine to expand the target list dynamically.
    """
    cache = load_discovered_sellers()
    sellers = []
    for subdomain, info in cache["sellers"].items():
        sellers.append({
            "id": f"reddit_{subdomain}",
            "name": f"{subdomain} (discovered via {info.get('source', 'Reddit')})",
            "base_url": info["base_url"],
            "categories": {
                "all": info["albums_url"]
            }
        })
    return sellers


def get_direct_album_urls() -> List[str]:
    """Returns all directly discovered Yupoo album URLs from Reddit."""
    cache = load_discovered_sellers()
    return [item["url"] for item in cache.get("products", [])]


if __name__ == "__main__":
    results = asyncio.run(run_reddit_scout())
    
    safe_print("\n=== TOP NEWLY FOUND SELLERS ===")
    for subdomain, info in list(results["new_sellers"].items())[:10]:
        safe_print(f"  {subdomain} — {info.get('post_title', '')[:60]}")
    
    safe_print("\n=== TRENDING W2C SEARCHES ON REDDIT ===")
    for t in results.get("trending_searches", [])[:5]:
        safe_print(f"  [{t['ups']} upvotes] [{t['subreddit']}] {t['query']}")
    
    safe_print("\n=== DIRECT ALBUM URLS FOUND ===")
    for item in results.get("direct_album_urls", [])[:10]:
        safe_print(f"  {item['url']}")
        safe_print(f"    via: {item['source'][:60]}")

