"""
Reddit Premium Brand Discovery Engine
=======================================
Mines Reddit fashion subreddits for brand recommendations and product finds.
Discovers NEW brands organically from community discussions, then validates
if they have scrapeable Shopify stores.

Outputs: data/discovered_premium_brands.json

Usage:
    python reddit_brand_discovery.py              # Full discovery run
    python reddit_brand_discovery.py --test        # Dry run (no saves)
    python reddit_brand_discovery.py --subreddit streetwear  # Single sub
"""
import os
import re
import sys
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
from collections import Counter

import httpx
from dotenv import load_dotenv

load_dotenv()

# Force UTF-8 stdout/stderr on Windows to prevent cp1252 charmap encoding errors
if sys.platform.startswith("win"):
    import io
    if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass  # Already wrapped or buffer unavailable

# Safe print for Windows (fallback wrapper)
def safe_print(msg: str):
    print(msg, flush=True)

# ── Config ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DISCOVERED_BRANDS_FILE = os.path.join(DATA_DIR, "discovered_premium_brands.json")
DISCOVERY_HISTORY_FILE = os.path.join(DATA_DIR, "reddit_discovery_history.json")

# Discord webhook for notifications (reuse existing)
DISCORD_WEBHOOK = os.environ.get("DISCORD_SCOUT_WEBHOOK", "")

# ── Target Subreddits ───────────────────────────────────────────
# These are fashion-focused subs where real users discuss quality brands
FASHION_SUBREDDITS = [
    "streetwear",
    "malefashionadvice",
    "femalefashionadvice",
    "rawdenim",
    "BuyItForLife",
    "techwearclothing",
    "japanesestreetwear",
    "avantgardefashion",
    "QualityReps",           # Users discuss the ORIGINALS they rep
    "fashionreps",           # Same — originals get named
    "sneakers",
    "goodyearwelt",
]

# ── Premium Signal Keywords ─────────────────────────────────────
# Words that indicate a brand discussion is about PREMIUM quality items
PREMIUM_SIGNALS = [
    # Quality indicators
    "quality", "heavyweight", "premium", "luxury", "grail", "worth the price",
    "best quality", "high quality", "top tier", "worth it", "investment piece",
    "insane quality", "fire quality", "underrated", "slept on",
    # Price signals
    "$200", "$250", "$300", "$350", "$400", "$450", "$500",
    "200 dollars", "300 dollars", "400 dollars", "500 dollars",
    # Material signals
    "cashmere", "merino", "selvedge", "raw denim", "genuine leather",
    "full grain", "goodyear welt", "heavyweight cotton", "500gsm", "400gsm",
    "japanese denim", "italian leather", "hand sewn",
    # Fashion category signals
    "lookbook", "editorial", "campaign", "drop", "collection",
    "copped", "just got", "pickup", "haul", "review",
]

# ── Known Premium Brands Database ──────────────────────────────
# Cross-reference list — brands we already know are premium
# Used to validate Reddit mentions and find NEW brands we DON'T know
KNOWN_PREMIUM_BRANDS = {
    # Already in our LEGIT_BRANDS (safe, legal Chinese brands)
    "enshadower", "catsstac", "nosucism", "roaringwild", "bjhg", "umamiism", "fmacm", "attempt", "medm",
    # Safe premium independent Western/Japanese brands (with no/low replica motivation or sold through authorized Shopify stores)
    "represent", "aime leon dore", "ald", "kith", "rhude", "maharishi", "norse projects", "story mfg",
    "18east", "engineered garments", "bode", "pop trading", "dime", "brain dead", "pleasures", "online ceramics",
    "todd snyder", "buck mason", "taylor stitch", "portuguese flannel", "pas normal studios", "drole de monsieur", "casablanca",
    "kapital", "visvim", "needles", "acne studios", "ami paris", "lemaire", "jil sander", "maison margiela",
    "a kind of guise", "universal works", "folk", "sns herning", "real mccoys", "the real mccoys", "iron heart", "flat head",
    "studio dartisan", "pure blue japan", "momotaro", "noah", "apc", "a.p.c."
}

# ── Replica Brand Blacklist ─────────────────────────────────────
# High-risk counterfeit/replica brands that we MUST NEVER search or dropship
REPLICA_BRAND_BLACKLIST = {
    "nike", "adidas", "bape", "stussy", "stüssy", "jordan", "air jordan", "supreme",
    "essentials", "fear of god", "fog", "chrome hearts", "off-white", "off white",
    "balenciaga", "louis vuitton", "gucci", "prada", "travis scott", "yeezy",
    "asics", "puma", "vans", "converse", "a bathing ape", "moncler", "canada goose",
    "stone island", "palm angels", "vetements", "gallery dept", "gallery dept.",
    "dior", "fendi", "versace", "givenchy", "valentino", "burberry", "celine",
    "saint laurent", "ysl", "chanel", "hermes", "amiri", "corteiz", "palace"
}

# ── Brand Name Extraction Patterns ─────────────────────────────
# Regex patterns to extract brand names from Reddit text
BRAND_MENTION_PATTERNS = [
    r"(?:just (?:copped|got|bought|picked up)|wearing|rocking|loving|favorite brand is|recommend)\s+(?:some\s+)?([A-Z][A-Za-z\s&'.()-]{2,30}?)(?:\s+(?:hoodie|jacket|pants|tee|shirt|coat|sneakers|boots|bag|shorts|joggers|sweater))",
    r"([A-Z][A-Za-z\s&'.()-]{2,25}?)\s+(?:quality|is (?:fire|insane|worth|amazing|underrated|slept on))",
    r"(?:check out|try|look at|recommend)\s+([A-Z][A-Za-z\s&'.()-]{2,25}?)(?:\s|,|\.|!)",
    r"\b([A-Z][A-Za-z]{2,20}(?:\s+[A-Z][A-Za-z]{2,15})?)\s+(?:\$\d{2,4}|costs?\s+\$)",
]

# Words that are NOT brand names (false positive filter)
NOT_BRAND_WORDS = {
    "the", "this", "that", "these", "those", "what", "which", "where",
    "when", "how", "who", "any", "some", "all", "every", "each",
    "you", "your", "they", "their", "its", "his", "her", "our",
    "just", "really", "very", "super", "pretty", "quite", "absolutely",
    "great", "good", "best", "worst", "nice", "cool", "fire", "amazing",
    "love", "like", "hate", "want", "need", "got", "get", "bought",
    "price", "quality", "fit", "size", "color", "style", "vibe",
    "hoodie", "jacket", "pants", "shirt", "tee", "coat", "sneaker",
    "edit", "update", "deleted", "removed", "comment", "post", "thread",
    "reddit", "anyone", "everyone", "someone", "nobody", "help", "thanks",
    "question", "opinion", "thought", "feedback", "review", "rating",
    "men", "women", "male", "female", "unisex", "oversized", "slim",
    "new", "old", "vintage", "retro", "modern", "classic",
    "yes", "no", "idk", "imo", "tbh", "ngl", "lol", "lmao",
}


# ═════════════════════════════════════════════════════════════════
#  CORE FUNCTIONS
# ═════════════════════════════════════════════════════════════════

async def fetch_subreddit_posts(subreddit: str, sort: str = "hot", limit: int = 100) -> List[Dict]:
    """Fetch posts from a subreddit using Reddit's public JSON/RSS API."""
    posts = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Strategy 1: JSON API (most reliable for structured data)
    for base in [f"https://old.reddit.com/r/{subreddit}/{sort}.json?limit={limit}",
                 f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"]:
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
                resp = await client.get(base)
                if resp.status_code == 200:
                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for child in children:
                        post_data = child.get("data", {})
                        posts.append({
                            "title": post_data.get("title", ""),
                            "selftext": post_data.get("selftext", ""),
                            "url": post_data.get("url", ""),
                            "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                            "score": post_data.get("score", 0),
                            "num_comments": post_data.get("num_comments", 0),
                            "created_utc": post_data.get("created_utc", 0),
                            "subreddit": subreddit,
                        })
                    if posts:
                        safe_print(f"   [r/{subreddit}] JSON OK — {len(posts)} posts")
                        return posts
        except Exception as e:
            safe_print(f"   [r/{subreddit}] JSON attempt failed: {e}")

    # Strategy 2: RSS Fallback
    try:
        rss_url = f"https://www.reddit.com/r/{subreddit}/{sort}.rss?limit={limit}"
        async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
            resp = await client.get(rss_url)
            if resp.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall(".//atom:entry", ns)
                if not entries:
                    entries = root.findall(".//entry")
                for entry in entries[:limit]:
                    # Handle XML namespacing properly to avoid deprecation
                    title_el = entry.find("atom:title", ns)
                    if title_el is None:
                        title_el = entry.find("title")
                    content_el = entry.find("atom:content", ns)
                    if content_el is None:
                        content_el = entry.find("content")
                    link_el = entry.find("atom:link", ns)
                    if link_el is None:
                        link_el = entry.find("link")

                    # RSS content is often HTML — strip tags to get plain text
                    raw_content = ""
                    if content_el is not None and content_el.text:
                        raw_content = re.sub(r'<[^>]+>', ' ', content_el.text)
                        raw_content = re.sub(r'\s+', ' ', raw_content).strip()
                        # Also decode HTML entities
                        import html as html_mod
                        raw_content = html_mod.unescape(raw_content)

                    title_text = ""
                    if title_el is not None and title_el.text:
                        title_text = title_el.text

                    link_href = ""
                    if link_el is not None:
                        link_href = link_el.get("href", "")

                    posts.append({
                        "title": title_text,
                        "selftext": raw_content,
                        "url": link_href,
                        "permalink": link_href,
                        "score": 0,
                        "num_comments": 0,
                        "created_utc": 0,
                        "subreddit": subreddit,
                    })
                if posts:
                    safe_print(f"   [r/{subreddit}] RSS fallback — {len(posts)} posts")
                    return posts
    except Exception as e:
        safe_print(f"   [r/{subreddit}] RSS fallback failed: {e}")

    safe_print(f"   [r/{subreddit}] ⚠️ No posts retrieved")
    return posts


def extract_brand_mentions(text: str) -> List[str]:
    """Extract potential brand names from post text using pattern matching."""
    if not text:
        return []

    found_brands = []

    # Method 1: Check for known premium brand names (case-insensitive)
    text_lower = text.lower()
    for brand in KNOWN_PREMIUM_BRANDS:
        if brand.lower() in text_lower:
            found_brands.append(brand.title())

    # Method 2: Regex pattern matching for unknown brands
    for pattern in BRAND_MENTION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            cleaned = match.strip().strip(".,!?'\"()[]")
            # Filter out false positives
            if len(cleaned) < 2 or len(cleaned) > 35:
                continue
            words = cleaned.lower().split()
            if all(w in NOT_BRAND_WORDS for w in words):
                continue
            if cleaned[0].isupper() or cleaned.isupper():
                found_brands.append(cleaned)

    # Method 3: Look for capitalized multi-word names (brand-like patterns)
    # e.g., "Our Legacy", "Brain Dead", "Todd Snyder"
    cap_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
    cap_matches = re.findall(cap_pattern, text)
    for match in cap_matches:
        match_lower = match.lower()
        if match_lower in KNOWN_PREMIUM_BRANDS:
            found_brands.append(match)
        # If it's mentioned with premium signals nearby, flag it
        elif any(signal in text_lower[max(0, text_lower.find(match_lower)-100):text_lower.find(match_lower)+100]
                 for signal in ["quality", "grail", "worth", "fire", "premium", "copped", "$"]):
            found_brands.append(match)

    # Deduplicate while preserving order and filtering blacklisted brands
    seen = set()
    unique = []
    for b in found_brands:
        key = b.lower().strip()
        if key in REPLICA_BRAND_BLACKLIST:
            continue
        if key not in seen and key not in NOT_BRAND_WORDS:
            seen.add(key)
            unique.append(b)

    return unique


def score_premium_relevance(post: Dict) -> float:
    """Score how relevant a post is for premium brand discovery (0.0 to 1.0)."""
    text = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
    score = 0.0

    # Premium signal matches
    signal_count = sum(1 for signal in PREMIUM_SIGNALS if signal.lower() in text)
    score += min(signal_count * 0.1, 0.5)  # Cap at 0.5 from signals

    # Post engagement (higher = more validated)
    post_score = post.get("score", 0)
    if post_score > 100:
        score += 0.2
    elif post_score > 50:
        score += 0.15
    elif post_score > 10:
        score += 0.1
    elif post_score > 0:
        score += 0.05

    # Comment engagement
    comments = post.get("num_comments", 0)
    if comments > 50:
        score += 0.15
    elif comments > 20:
        score += 0.1
    elif comments > 5:
        score += 0.05

    # Price mention bonus
    if re.search(r'\$[2-5]\d{2}', text):
        score += 0.15

    return min(score, 1.0)


async def check_shopify_store(brand_name: str) -> Optional[str]:
    """Try to find a Shopify store for a brand name. Returns URL or None."""
    # Generate candidate URLs
    slug = re.sub(r'[^a-zA-Z0-9]', '', brand_name.lower())
    slug_hyphen = re.sub(r'[^a-zA-Z0-9]+', '-', brand_name.lower()).strip('-')

    candidates = [
        f"https://{slug}.com",
        f"https://www.{slug}.com",
        f"https://{slug_hyphen}.com",
        f"https://www.{slug_hyphen}.com",
        f"https://shop{slug}.com",
        f"https://{slug}official.com",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for url in candidates:
        try:
            async with httpx.AsyncClient(timeout=8.0, verify=False, follow_redirects=True, headers=headers) as client:
                resp = await client.get(f"{url}/products.json?limit=1")
                if resp.status_code == 200:
                    data = resp.json()
                    products = data.get("products", [])
                    if products:
                        safe_print(f"      [+] Shopify store confirmed: {url}")
                        return url
        except Exception:
            continue

    return None


async def discover_brands(
    subreddits: Optional[List[str]] = None,
    test_mode: bool = False,
    check_shopify: bool = True,
) -> Dict:
    """
    Main discovery function. Scrapes Reddit for brand mentions,
    scores them, and optionally validates Shopify stores.
    """
    if subreddits is None:
        subreddits = FASHION_SUBREDDITS

    safe_print("═══════════════════════════════════════════════════")
    safe_print("  🔍 REDDIT PREMIUM BRAND DISCOVERY ENGINE")
    safe_print("═══════════════════════════════════════════════════")
    safe_print(f"  Scanning {len(subreddits)} subreddits...")
    safe_print(f"  Test mode: {test_mode}")
    safe_print("")

    # Load existing discoveries
    existing = load_discovered_brands()
    all_brand_mentions: Counter = Counter()
    brand_subreddits: Dict[str, Set[str]] = {}
    brand_quotes: Dict[str, List[str]] = {}
    brand_scores: Dict[str, List[float]] = {}

    total_posts = 0
    total_brands_found = 0

    for subreddit in subreddits:
        safe_print(f"\n[🔍] Scanning r/{subreddit}...")

        # Fetch from both hot and top (this week) for breadth
        for sort in ["hot", "top"]:
            posts = await fetch_subreddit_posts(subreddit, sort=sort, limit=50)
            total_posts += len(posts)

            for post in posts:
                text = f"{post.get('title', '')} {post.get('selftext', '')}"
                brands = extract_brand_mentions(text)
                relevance = score_premium_relevance(post)

                for brand in brands:
                    brand_key = brand.lower().strip()
                    all_brand_mentions[brand_key] += 1
                    brand_subreddits.setdefault(brand_key, set()).add(subreddit)
                    brand_scores.setdefault(brand_key, []).append(relevance)

                    # Save a sample quote (max 3 per brand)
                    if brand_key not in brand_quotes:
                        brand_quotes[brand_key] = []
                    if len(brand_quotes[brand_key]) < 3:
                        title = post.get("title", "")[:120]
                        brand_quotes[brand_key].append(f"[r/{subreddit}] {title}")

                    total_brands_found += 1

            # Rate limit between requests (be respectful)
            await asyncio.sleep(2)

    # ── Process Results ──────────────────────────────────────────
    safe_print(f"\n\n{'='*60}")
    safe_print(f"  📊 DISCOVERY RESULTS")
    safe_print(f"{'='*60}")
    safe_print(f"  Posts scanned: {total_posts}")
    safe_print(f"  Total brand mentions: {total_brands_found}")
    safe_print(f"  Unique brands found: {len(all_brand_mentions)}")

    # Build ranked results
    discoveries = []
    for brand_key, mention_count in all_brand_mentions.most_common(100):
        avg_score = sum(brand_scores.get(brand_key, [0])) / max(len(brand_scores.get(brand_key, [1])), 1)
        subs = list(brand_subreddits.get(brand_key, set()))
        quotes = brand_quotes.get(brand_key, [])

        # Determine if this is a NEW discovery vs already known
        is_known = brand_key in KNOWN_PREMIUM_BRANDS
        is_existing = brand_key in {b.get("brand_name", "").lower() for b in existing.get("brands", [])}

        # Confidence score: `mentions * avg_relevance * subreddit_diversity`
        confidence = min(1.0, (mention_count / 10) * avg_score * (len(subs) / 3))

        discovery = {
            "brand_name": brand_key.title(),
            "mention_count": mention_count,
            "avg_relevance_score": round(avg_score, 3),
            "confidence": round(confidence, 3),
            "subreddits": subs,
            "sample_quotes": quotes,
            "is_known": is_known,
            "is_new_discovery": not is_known and not is_existing,
            "shopify_url": None,
            "discovered_at": datetime.now().isoformat(),
        }
        discoveries.append(discovery)

    # Sort by confidence descending
    discoveries.sort(key=lambda x: x["confidence"], reverse=True)

    # ── Shopify Validation (for top NEW discoveries) ─────────────
    if check_shopify and not test_mode:
        new_discoveries = [d for d in discoveries if d["is_new_discovery"] and d["confidence"] > 0.1]
        safe_print(f"\n  🛍️ Checking Shopify stores for {min(len(new_discoveries), 20)} new brands...")

        for disc in new_discoveries[:20]:
            shopify_url = await check_shopify_store(disc["brand_name"])
            if shopify_url:
                disc["shopify_url"] = shopify_url
            await asyncio.sleep(1)  # Rate limit

    # ── Display Results ──────────────────────────────────────────
    safe_print(f"\n  🏆 TOP DISCOVERED BRANDS:")
    safe_print(f"  {'─'*55}")

    for i, disc in enumerate(discoveries[:30], 1):
        status = "✅ Known" if disc["is_known"] else ("🆕 NEW!" if disc["is_new_discovery"] else "📋 Exists")
        shopify = f" | 🛍️ {disc['shopify_url']}" if disc.get("shopify_url") else ""
        safe_print(
            f"  {i:2d}. {disc['brand_name']:<25} "
            f"mentions={disc['mention_count']:3d} "
            f"conf={disc['confidence']:.2f} "
            f"{status}{shopify}"
        )

    # ── Save Results ─────────────────────────────────────────────
    if not test_mode:
        # Merge with existing discoveries
        existing_brands = {b["brand_name"].lower(): b for b in existing.get("brands", [])}
        for disc in discoveries:
            key = disc["brand_name"].lower()
            if key in existing_brands:
                # Update mention count and confidence
                existing_brands[key]["mention_count"] = max(
                    existing_brands[key].get("mention_count", 0),
                    disc["mention_count"]
                )
                existing_brands[key]["confidence"] = max(
                    existing_brands[key].get("confidence", 0),
                    disc["confidence"]
                )
                existing_brands[key]["last_seen"] = datetime.now().isoformat()
                if disc.get("shopify_url"):
                    existing_brands[key]["shopify_url"] = disc["shopify_url"]
            else:
                existing_brands[key] = disc

        output = {
            "last_updated": datetime.now().isoformat(),
            "total_brands": len(existing_brands),
            "brands": list(existing_brands.values()),
        }

        with open(DISCOVERED_BRANDS_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        safe_print(f"\n  💾 Saved {len(existing_brands)} brands to {DISCOVERED_BRANDS_FILE}")

        # Send Discord notification
        if DISCORD_WEBHOOK:
            new_count = sum(1 for d in discoveries if d["is_new_discovery"])
            shopify_count = sum(1 for d in discoveries if d.get("shopify_url"))
            await send_discord_notification(
                f"🔍 **Reddit Brand Discovery Complete**\n"
                f"Posts scanned: {total_posts}\n"
                f"Brands found: {len(discoveries)}\n"
                f"New discoveries: {new_count}\n"
                f"Shopify stores confirmed: {shopify_count}\n"
                f"Top brand: {discoveries[0]['brand_name'] if discoveries else 'None'}"
            )

    return {
        "total_posts_scanned": total_posts,
        "total_unique_brands": len(discoveries),
        "new_discoveries": sum(1 for d in discoveries if d["is_new_discovery"]),
        "shopify_confirmed": sum(1 for d in discoveries if d.get("shopify_url")),
        "top_brands": discoveries[:10],
    }


def load_discovered_brands() -> Dict:
    """Load previously discovered brands."""
    if os.path.exists(DISCOVERED_BRANDS_FILE):
        try:
            with open(DISCOVERED_BRANDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"brands": [], "last_updated": None}


async def send_discord_notification(message: str):
    """Send a notification to Discord webhook."""
    if not DISCORD_WEBHOOK:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(DISCORD_WEBHOOK, json={"content": message})
    except Exception as e:
        safe_print(f"  [!] Discord notification failed: {e}")


# ═════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ═════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Reddit Premium Brand Discovery Engine")
    parser.add_argument("--test", action="store_true", help="Dry run, don't save results")
    parser.add_argument("--subreddit", type=str, help="Only scan a specific subreddit")
    parser.add_argument("--no-shopify", action="store_true", help="Skip Shopify store validation")
    args = parser.parse_args()

    subreddits = [args.subreddit] if args.subreddit else None

    results = asyncio.run(discover_brands(
        subreddits=subreddits,
        test_mode=args.test,
        check_shopify=not args.no_shopify,
    ))

    safe_print(f"\n{'='*60}")
    safe_print(f"  ✅ DISCOVERY COMPLETE")
    safe_print(f"  Posts: {results['total_posts_scanned']}")
    safe_print(f"  Brands: {results['total_unique_brands']}")
    safe_print(f"  New: {results['new_discoveries']}")
    safe_print(f"  Shopify: {results['shopify_confirmed']}")
    safe_print(f"{'='*60}")


if __name__ == "__main__":
    main()
