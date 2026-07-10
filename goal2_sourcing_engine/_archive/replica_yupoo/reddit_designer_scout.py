import os
import sys
import re
import json
import time
import httpx
from datetime import datetime
from pathlib import Path

# Force UTF-8 stdout/stderr on Windows
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def safe_print(msg: str):
    print(msg, flush=True)

class RedditDesignerScout:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.base_dir = Path("c:/Users/USER/ai ugc and sales/goal2_sourcing_engine")
        self.output_file = self.base_dir / "data" / "reddit_discovered_stores.json"
        
    def fetch_search_results(self, subreddit: str, query: str) -> list:
        safe_print(f"[*] Searching r/{subreddit} for: '{query}'...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # ── Strategy 1: old.reddit.com JSON ──
        for domain in ["old.reddit.com", "www.reddit.com"]:
            url = f"https://{domain}/r/{subreddit}/search.json"
            params = {
                "q": query,
                "restrict_sr": "1",
                "sort": "relevance",
                "t": "all",
                "limit": 10
            }
            try:
                with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
                    resp = client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        posts = data.get("data", {}).get("children", [])
                        if posts:
                            safe_print(f"    [+] Found {len(posts)} posts via JSON ({domain}).")
                            return posts
            except Exception as e:
                pass
            time.sleep(1.0)
            
        # ── Strategy 2: Search RSS Feed (bypass 403/429 blocks) ──
        safe_print("    [!] JSON blocked. Trying RSS search fallback...")
        rss_url = f"https://www.reddit.com/r/{subreddit}/search.rss"
        params = {"q": query, "restrict_sr": "on", "sort": "relevance", "t": "all"}
        try:
            with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
                resp = client.get(rss_url, params=params)
                if resp.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    entries = root.findall(".//atom:entry", ns) or root.findall(".//entry")
                    posts = []
                    for entry in entries:
                        title_el = entry.find("atom:title", ns) or entry.find("title")
                        content_el = entry.find("atom:content", ns) or entry.find("content")
                        link_el = entry.find("atom:link", ns) or entry.find("link")
                        
                        title = title_el.text if title_el is not None else ""
                        content = content_el.text if content_el is not None else ""
                        permalink = link_el.get("href") if link_el is not None else ""
                        
                        posts.append({
                            "data": {
                                "title": title,
                                "selftext": content,
                                "permalink": permalink.replace("https://reddit.com", "") if permalink else "",
                                "score": 10
                            }
                        })
                    safe_print(f"    [+] Found {len(posts)} posts via RSS.")
                    return posts
        except Exception as e:
            safe_print(f"    [-] RSS fallback failed: {e}")
            
        return []

    def extract_links(self, text: str) -> list:
        if not text:
            return []
        
        # Regex to find Taobao, Weidian, and 1688 URLs
        patterns = [
            r'https?://[a-zA-Z0-9.-]*weidian\.com/[a-zA-Z0-9_.-/?=&]*',
            r'https?://[a-zA-Z0-9.-]*taobao\.com/[a-zA-Z0-9_.-/?=&]*',
            r'https?://[a-zA-Z0-9.-]*tmall\.com/[a-zA-Z0-9_.-/?=&]*',
            r'https?://[a-zA-Z0-9.-]*1688\.com/[a-zA-Z0-9_.-/?=&]*'
        ]
        
        found = []
        for pat in patterns:
            matches = re.findall(pat, text)
            for m in matches:
                # Clean markdown links (like [link](url))
                clean_url = m.split(')')[0].split(']')[0].strip()
                if clean_url not in found:
                    found.append(clean_url)
        return found

    def fetch_comments_links(self, subreddit: str, permalink: str) -> list:
        if not permalink:
            return []
        # Extract post_id from permalink (e.g. /r/streetwearstartup/comments/xyz123/some_title/)
        match = re.search(r'/comments/([a-z0-9]+)', permalink)
        if not match:
            return []
        post_id = match.group(1)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }
        rss_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.rss"
        try:
            with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
                resp = client.get(rss_url)
                if resp.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    entries = root.findall(".//atom:entry", ns) or root.findall(".//entry")
                    comments_text = []
                    for entry in entries:
                        content_el = entry.find("atom:content", ns) or entry.find("content")
                        if content_el is not None and content_el.text:
                            comments_text.append(content_el.text)
                    
                    combined_text = "\n".join(comments_text)
                    return self.extract_links(combined_text)
        except Exception:
            pass
        return []

    def run_scout(self):
        subreddits = ["streetwearstartup", "streetwear", "blanktees", "fashion"]
        queries = [
            "blanks",
            "heavyweight blanks",
            "blank hoodie",
            "unbranded",
            "wholesale blanks",
            "independent streetwear"
        ]
        
        discovered_items = []
        seen_urls = set()
        
        for sub in subreddits:
            for q in queries:
                posts = self.fetch_search_results(sub, q)
                for post in posts[:5]:  # Limit comment checking to top 5 posts to prevent rate limits
                    post_data = post.get("data", {})
                    title = post_data.get("title", "")
                    selftext = post_data.get("selftext", "")
                    permalink = f"https://reddit.com{post_data.get('permalink', '')}"
                    score = post_data.get("score", 0)
                    
                    combined_text = f"{title}\n{selftext}"
                    links = self.extract_links(combined_text)
                    
                    # Fetch links from comments as well
                    comment_links = self.fetch_comments_links(sub, post_data.get('permalink', ''))
                    if comment_links:
                        links.extend(comment_links)
                    
                    # Deduplicate links
                    links = list(set(links))
                    
                    if links:
                        for url in links:
                            if url not in seen_urls:
                                seen_urls.add(url)
                                discovered_items.append({
                                    "url": url,
                                    "source_post_title": title,
                                    "source_post_url": permalink,
                                    "subreddit": sub,
                                    "search_query": q,
                                    "discovered_at": datetime.now().isoformat(),
                                    "score": score
                                })
                
                time.sleep(2.0) # Respect rate limits
                
        # Save results
        if discovered_items:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            existing = []
            if self.output_file.exists():
                try:
                    existing = json.loads(self.output_file.read_text(encoding="utf-8"))
                except Exception:
                    existing = []
                    
            # Merge
            existing_urls = {item["url"] for item in existing}
            new_additions = 0
            for item in discovered_items:
                if item["url"] not in existing_urls:
                    existing.append(item)
                    new_additions += 1
                    
            self.output_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
            safe_print(f"\n[OK] Scout finished! Found {len(discovered_items)} links. Added {new_additions} NEW links to database.")
            safe_print(f"     Database location: {self.output_file}")
        else:
            safe_print("\n[-] Scout finished. No links discovered this cycle.")

if __name__ == "__main__":
    scout = RedditDesignerScout()
    scout.run_scout()
