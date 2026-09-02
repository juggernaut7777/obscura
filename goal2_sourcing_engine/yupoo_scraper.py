"""
Yupoo Album Scraper — Scrapes a Yupoo seller's catalog and extracts product info + Weidian links.

Yupoo uses two template versions:
  - v1 (classic): album__title, album__main, album__img
  - v2 (modern): album3__title, album3__main, title attributes on <a> tags

Usage:
    from yupoo_scraper import YupooScraper
    scraper = YupooScraper()
    albums = scraper.scrape_seller("goat-official", page=1)
    # albums = [{"title": "...", "album_url": "...", "thumbnail": "...", "weidian_link": "...", ...}, ...]
"""
import os
import re
import json
import time
import logging
import requests
import socket
import ssl
import html as html_mod
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, quote


# ── Safe print for Windows cp1252 ──────────────────────────────────────────
def safe_print(*args, **kwargs):
    """Print that handles Unicode on Windows cp1252 terminals."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        print(text.encode("ascii", "backslashreplace").decode("ascii"), **kwargs)

# ── Logging ────────────────────────────────────────────────────────────────
log = logging.getLogger("yupoo_scraper")

# ── Constants ──────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Regex patterns for marketplace URL extraction (supports Weidian v.weidian/youshop10, Taobao tb.cn, 1688, Tmall)
MARKETPLACE_PATTERN = re.compile(
    r'(https?://(?:'
    r'(?:[a-zA-Z0-9_-]+\.)*weidian\.com/(?:item\.html|fastorder/item\.html)\?[^\s"\'<>]+'
    r'|(?:k\.)?youshop10\.com/[^\s"\'<>]+'
    r'|(?:[a-zA-Z0-9_-]+\.)*taobao\.com/(?:item\.htm|item/detail\.htm)\?[^\s"\'<>]+'
    r'|detail\.tmall\.com/item\.htm\?[^\s"\'<>]+'
    r'|tb\.cn/[^\s"\'<>]+'
    r'|(?:detail|m)\.1688\.com/offer/[^\s"\'<>]+'
    r'))',
    re.IGNORECASE
)


# Price extraction from titles/descriptions
# Expanded patterns: "89¥", "¥289", "￥95", "150 yuan", "120 RMB", "110 CNY",
# "价格 89", "售价89", "price: 89", "$35", "35$", "35usd"
PRICE_PATTERN = re.compile(
    r'(?:(\d+(?:\.\d+)?)\s*(?:¥|\uffe5|yuan|rmb|cny|\$|usd))|'
    r'(?:(?:¥|\uffe5|yuan|rmb|cny|\$|usd)\s*(\d+(?:\.\d+)?))|'
    r'(?:(?:价格|售价|price|cost)\s*[:：]?\s*(\d+(?:\.\d+)?))',
    re.IGNORECASE
)


# Global map to cache DoH resolved IPs
_RESOLVED_YUPPO_IPS = {}
_ORIGINAL_GETADDRINFO = socket.getaddrinfo

# Standard native socket getaddrinfo (disabled monkeypatch for Linux Azure VM compatibility)



class YupooScraper:
    """Scrapes Yupoo seller catalogs to extract album info and Weidian links."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        # Configure residential/datacenter proxy if set in .env to prevent VPS IP rate limits & bans
        proxy = os.getenv("SMART_PROXY_URL") or os.getenv("HTTP_PROXY") or os.getenv("PROXY_URL")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
            safe_print(f"[Yupoo] Session configured with proxy: {proxy}")


    def _resolve_clean_ip(self, host: str) -> Optional[str]:
        """Resolve a host name to an IP address using DNS-over-HTTPS (DoH)."""
        if host in _RESOLVED_YUPPO_IPS:
            return _RESOLVED_YUPPO_IPS[host]

        import urllib.request

        # Use unverified context to bypass local certificate verification issues (e.g. corporate SSL filters)
        context = ssl._create_unverified_context()
        
        # Try Cloudflare DoH first, then Google DoH
        doh_urls = [
            f"https://cloudflare-dns.com/dns-query?name={host}&type=A",
            f"https://dns.google/resolve?name={host}&type=A"
        ]

        for url in doh_urls:
            try:
                req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
                with urllib.request.urlopen(req, timeout=5, context=context) as resp:
                    data = json.loads(resp.read().decode())
                    for ans in data.get("Answer", []):
                        # Type 1 is A record
                        if ans.get("type") == 1:
                            ip = ans.get("data")
                            if ip:
                                _RESOLVED_YUPPO_IPS[host] = ip
                                log.info(f"[Yupoo DNS] Resolved {host} -> {ip} via DoH")
                                return ip
            except Exception as e:
                log.warning(f"[Yupoo DNS] DoH failed for {url}: {e}")
        
        return None

    def normalize_url(self, url: str) -> str:
        """Normalize any Yupoo URL (mobile .m., desktop .x., photos/) to standard HTTPS x.yupoo.com format."""
        if not url:
            return ""
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        if url.startswith("http://"):
            url = "https://" + url[7:]
            
        # Fix .m.yupoo.com -> .x.yupoo.com (prevents SSL hostname mismatch and HTTP 567 CDN block)
        url = re.sub(r'//([^/.]+)\.m\.yupoo\.com', r'//\1.x.yupoo.com', url)
        
        # Fix plain subdomain.yupoo.com -> subdomain.x.yupoo.com
        if not re.search(r'//(?:photo|s|x)\.yupoo\.com', url):
            url = re.sub(r'//([^/.]+)\.yupoo\.com', r'//\1.x.yupoo.com', url)
            
        # Fix m.yupoo.com/photos/subdomain or x.yupoo.com/photos/subdomain
        m_photos = re.search(r'yupoo\.com/photos/([^/]+)(.*)', url)
        if m_photos:
            subdomain = m_photos.group(1)
            rest = m_photos.group(2)
            url = f"https://{subdomain}.x.yupoo.com{rest}"
            
        return url

    def _get_page(self, url: str, timeout: int = 15) -> Optional[str]:
        """Fetch a URL and return HTML content, or None on failure."""
        url = self.normalize_url(url)
        try:
            resp = self.session.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.text
            else:
                safe_print(f"[Yupoo] HTTP {resp.status_code} for {url}")
                return None
        except Exception as e:
            safe_print(f"[Yupoo] Error fetching {url}: {e}")
            return None


    def _extract_price(self, title: str, description: str = "") -> Optional[float]:
        """Extract price in CNY from album title or description.
        
        Searches title first, then falls back to description text.
        Uses expanded regex covering ¥, $, yuan, rmb, 价格, 售价 formats.
        """
        # Try title first (highest priority)
        match = PRICE_PATTERN.search(title)
        if match:
            price_str = match.group(1) or match.group(2) or match.group(3)
            try:
                return float(price_str)
            except (ValueError, TypeError):
                pass
        
        # Fall back to description
        if description:
            match = PRICE_PATTERN.search(description)
            if match:
                price_str = match.group(1) or match.group(2) or match.group(3)
                try:
                    return float(price_str)
                except (ValueError, TypeError):
                    pass
        
        return None

    async def _llm_extract_price(self, title: str, description: str) -> Optional[float]:
        """Use LLM (Gemini via LiteLLM router) to extract price from unstructured text.
        
        Fallback for when regex fails on complex or non-standard price formats.
        """
        try:
            from litellm_router import shared_router
        except ImportError:
            return None
        
        if not shared_router:
            return None
        
        combined = f"Title: {title}\nDescription: {description[:300]}"
        prompt = (
            "Extract the product price in CNY (Chinese Yuan) from this Yupoo album listing. "
            "Return ONLY the numeric price value (e.g. '289' or '89.5'). "
            "If no price is found, return 'NONE'.\n\n"
            f"{combined}"
        )
        
        try:
            result = await shared_router.get_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=20
            )
            if result and result.strip().upper() != 'NONE':
                # Extract numeric value from LLM response
                num_match = re.search(r'(\d+(?:\.\d+)?)', result.strip())
                if num_match:
                    return float(num_match.group(1))
        except Exception:
            pass
        
        return None

    def normalize_subdomain(self, input_str: str) -> str:
        """Normalize subdomain from URL or raw input (handles .m.yupoo.com, .x.yupoo.com, etc.)."""
        if not input_str:
            return ""
        input_str = input_str.strip().lower()
        # Match domain pattern: http(s)://subdomain.m.yupoo.com or subdomain.x.yupoo.com
        match = re.search(r'(?:https?://)?([^/.]+)\.(?:m|x)\.yupoo\.com', input_str)
        if match:
            return match.group(1)
        # Match x.yupoo.com/photos/subdomain
        match2 = re.search(r'yupoo\.com/photos/([^/]+)', input_str)
        if match2:
            return match2.group(1)
        # Plain subdomain string
        return re.sub(r'[^a-zA-Z0-9_-]', '', input_str)

    def _detect_platform(self, url: str) -> str:
        """Detect marketplace platform from URL."""
        if not url:
            return 'unknown'
        url_lower = url.lower()
        if 'weidian.com' in url_lower or 'youshop10.com' in url_lower:
            return 'weidian'
        elif 'taobao.com' in url_lower or 'tb.cn' in url_lower or 'tmall.com' in url_lower:
            return 'taobao'
        elif '1688.com' in url_lower:
            return '1688'
        return 'unknown'


    def get_categories(self, subdomain: str) -> List[Dict]:
        """Get the list of categories for a seller.
        
        Returns:
            List of dicts with keys: id, name, url
        """
        base_url = f"https://{subdomain}.x.yupoo.com"
        html = self._get_page(f"{base_url}/albums")
        if not html:
            return []

        categories = []
        # Pattern 1: Category links with text content (handles newlines and nested li tags)
        cat_matches = re.findall(
            r'href="/categories/(\d+)"[^>]*>\s*(?:<li[^>]*>)?\s*([^<]+)',
            html
        )
        for cat_id, cat_name in cat_matches:
            name = html_mod.unescape(cat_name.strip())
            if name and cat_id != '0':  # Skip the "All" category (gid=0)
                categories.append({
                    'id': cat_id,
                    'name': name,
                    'url': f"{base_url}/categories/{cat_id}",
                })

        # Pattern 2: Categories from show-layout (modern template)
        cat_matches_v2 = re.findall(
            r'href="/categories/(\d+)[^"]*"[^>]*title="([^"]+)"',
            html
        )
        seen_ids = {c['id'] for c in categories}
        for cat_id, cat_name in cat_matches_v2:
            if cat_id not in seen_ids and cat_id != '0':
                categories.append({
                    'id': cat_id,
                    'name': html_mod.unescape(cat_name.strip()),
                    'url': f"{base_url}/categories/{cat_id}",
                })
                seen_ids.add(cat_id)

        return categories

    def scrape_album_list(self, subdomain: str, page: int = 1, category_id: Optional[str] = None) -> Tuple[List[Dict], bool]:
        """Scrape the album listing page for a seller.
        
        Args:
            subdomain: Yupoo seller subdomain (e.g., "goat-official" or full mobile/web URL)
            page: Page number (1-indexed). Each page shows ~48 albums.
            category_id: Optional category ID to filter by.
            
        Returns:
            Tuple of (list of album dicts, has_more_pages bool)
        """
        subdomain = self.normalize_subdomain(subdomain)
        base_url = f"https://{subdomain}.x.yupoo.com"
        
        if category_id:
            url = f"{base_url}/categories/{category_id}?page={page}"
        else:
            url = f"{base_url}/albums?page={page}"
        
        html = self._get_page(url)
        if not html:
            return [], False

        albums = []
        seen_urls = set()

        # ── Strategy 1: Classic template (album__main + album__title) ──────
        classic_albums = re.findall(
            r'href="(/albums/\d+(?:\?[^"]*)?)"',
            html
        )
        classic_titles = re.findall(
            r'class="[^"]*album__title[^"]*"[^>]*>([^<]+)',
            html
        )

        # ── Strategy 2: Modern template (album3__) ────────────────────────
        modern_matches = re.findall(
            r'<a[^>]*href="(/albums/\d+(?:\?[^"]*)?)"[^>]*title="([^"]*)"',
            html
        )
        modern_matches_rev = re.findall(
            r'<a[^>]*title="([^"]*)"[^>]*href="(/albums/\d+(?:\?[^"]*)?)"',
            html
        )
        all_modern = [(url, title) for url, title in modern_matches]
        all_modern += [(url, title) for title, url in modern_matches_rev]

        # ── Strategy 3: Title class elements (newest Yupoo template) ──────
        title_class_elements = re.findall(
            r'<(?:span|p|div)[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)',
            html
        )
        title_class_elements = [
            html_mod.unescape(t.strip()) for t in title_class_elements
            if t.strip() and 'Supplier' not in t and 'yupoo' not in t.lower()
            and len(t.strip()) > 2
        ]

        # ── Strategy 3: Extract image thumbnails ──────────────────────────
        all_imgs = re.findall(
            r'(?:src|data-src)="(https://photo\.yupoo\.com/[^"]+(?:medium|small|square)\.[^"]+)"',
            html
        )

        # ── Build album list from best available data ─────────────────────
        if all_modern:
            for album_path, title in all_modern:
                if album_path in seen_urls:
                    continue
                seen_urls.add(album_path)
                
                title_clean = html_mod.unescape(title.strip())
                price = self._extract_price(title_clean)
                
                albums.append({
                    'title': title_clean,
                    'album_url': f"{base_url}{album_path}",
                    'album_path': album_path,
                    'price_cny': price,
                    'thumbnail': None,
                    'weidian_link': None,
                    'platform': None,
                })
        
        elif classic_albums and title_class_elements and not classic_titles:
            for i, album_path in enumerate(classic_albums):
                if album_path in seen_urls:
                    continue
                seen_urls.add(album_path)
                
                title = html_mod.unescape(title_class_elements[i].strip()) if i < len(title_class_elements) else f"Album {i+1}"
                price = self._extract_price(title)
                
                albums.append({
                    'title': title,
                    'album_url': f"{base_url}{album_path}",
                    'album_path': album_path,
                    'price_cny': price,
                    'thumbnail': None,
                    'weidian_link': None,
                    'platform': None,
                })
        
        elif classic_albums and classic_titles:
            for i, album_path in enumerate(classic_albums):
                if album_path in seen_urls:
                    continue
                seen_urls.add(album_path)
                
                title = html_mod.unescape(classic_titles[i].strip()) if i < len(classic_titles) else f"Album {i+1}"
                price = self._extract_price(title)
                
                albums.append({
                    'title': title,
                    'album_url': f"{base_url}{album_path}",
                    'album_path': album_path,
                    'price_cny': price,
                    'thumbnail': None,
                    'weidian_link': None,
                    'platform': None,
                })

        
        # Fallback: classic albums without titles
        elif classic_albums:
            for i, album_path in enumerate(classic_albums):
                if album_path in seen_urls:
                    continue
                seen_urls.add(album_path)
                
                albums.append({
                    'title': f"Album {i+1}",
                    'album_url': f"{base_url}{album_path}",
                    'album_path': album_path,
                    'price_cny': None,
                    'thumbnail': None,
                    'weidian_link': None,
                    'platform': None,
                })

        # ── Assign thumbnails ─────────────────────────────────────────────
        # Filter to unique thumbnails (deduplicate by hash)
        unique_imgs = []
        seen_hashes = set()
        for img in all_imgs:
            # Extract the hash part: photo.yupoo.com/seller/HASH/size.ext
            hash_match = re.search(r'/([a-f0-9]+)/(?:medium|small|square)', img)
            if hash_match:
                h = hash_match.group(1)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    # Upgrade to medium quality
                    medium_url = re.sub(r'/(small|square)\.', '/medium.', img)
                    unique_imgs.append(medium_url)
        
        for i, album in enumerate(albums):
            if i < len(unique_imgs):
                album['thumbnail'] = unique_imgs[i]

        # ── Detect pagination ─────────────────────────────────────────────
        has_more = bool(re.search(r'page=' + str(page + 1), html))
        # Also check for "next page" or pagination indicators
        if not has_more:
            has_more = bool(re.search(r'class="[^"]*paginat[^"]*"', html, re.IGNORECASE))

        safe_print(f"[Yupoo] {subdomain} page {page}: {len(albums)} albums, has_more={has_more}")
        return albums, has_more

    def scrape_all_pages(self, subdomain: str, category_id: Optional[str] = None, max_pages: int = 8) -> Tuple[List[Dict], bool]:
        """Scrape all pages for a seller/category into a single continuous list of albums."""
        all_albums = []
        seen_urls = set()
        has_more = True
        page = 1
        
        while page <= max_pages and has_more:
            albums, page_has_more = self.scrape_album_list(subdomain, page=page, category_id=category_id)
            if not albums:
                break
            for a in albums:
                url = a.get("album_url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_albums.append(a)
            has_more = page_has_more
            page += 1

        safe_print(f"[Yupoo] Scraped {len(all_albums)} total albums across pages for {subdomain} (has_more={has_more})")
        return all_albums, has_more

    def scrape_album_detail(self, album_url: str) -> Dict:
        """Scrape an individual album detail page to extract Weidian links and full images.
        
        Args:
            album_url: Full URL to the album detail page.
            
        Returns:
            Dict with keys: title, weidian_link, platform, images, description, contact_info
        """
        import urllib.parse
        html = self._get_page(album_url)
        if not html:
            return {'weidian_link': None, 'platform': None, 'images': [], 'description': '', 'contact_info': None}

        # ── 1. Unescape full HTML to handle &#x3D;, &amp;, &equals;, etc. ─────
        html_unescaped = html_mod.unescape(html)

        result = {
            'title': '',
            'weidian_link': None,
            'platform': None,
            'images': [],
            'description': '',
            'contact_info': None,
        }

        # ── 2. Extract Title ──────────────────────────────────────────────
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_unescaped, re.IGNORECASE | re.DOTALL)
        if title_match:
            raw_title = title_match.group(1).split('|')[0].strip()
            result['title'] = html_mod.unescape(raw_title)
        else:
            result['title'] = 'unknown_product'

        # ── 3. Extract External Redirect URLs (x.yupoo.com/external?url=...) ─
        external_redirects = re.findall(r'x\.yupoo\.com/external\?url=([^\s"\'<>]+)', html_unescaped, re.I)
        unwrapped_redirects = []
        for enc_url in external_redirects:
            try:
                unwrapped = urllib.parse.unquote(urllib.parse.unquote(enc_url))
                unwrapped_redirects.append(html_mod.unescape(unwrapped))
            except Exception:
                pass

        search_corpus = html_unescaped + "\n" + "\n".join(unwrapped_redirects)

        # ── 4. Extract Marketplace Links ──────────────────────────────────
        marketplace_links = MARKETPLACE_PATTERN.findall(search_corpus)
        if marketplace_links:
            # Prefer Weidian link, then Taobao, then 1688
            weidian_links = [l for l in marketplace_links if 'weidian.com' in l or 'youshop10.com' in l]
            taobao_links = [l for l in marketplace_links if 'taobao.com' in l or 'tb.cn' in l or 'tmall.com' in l]
            
            if weidian_links:
                best_link = weidian_links[0]
            elif taobao_links:
                best_link = taobao_links[0]
            else:
                best_link = marketplace_links[0]
                
            clean_link = html_mod.unescape(best_link.rstrip('.,;)]}'))
            result['weidian_link'] = clean_link
            result['platform'] = self._detect_platform(clean_link)

        # ── 5. Extract Description ────────────────────────────────────────
        desc_texts = []
        # Pattern 1: Classic showalbum__des
        for dm in re.findall(r'showalbum__des[^>]*>(.*?)</div>', html_unescaped, re.DOTALL):
            txt = re.sub(r'<[^>]+>', ' ', dm).strip()
            txt = re.sub(r'\s+', ' ', txt)
            if txt:
                desc_texts.append(txt)
                
        # Pattern 2: Data attributes (data-name / infoCarry)
        for dm in re.findall(r'data-name=["\']([^"\']+)["\']', html_unescaped):
            txt = html_mod.unescape(dm).replace('$nbsp', ' ').strip()
            if txt and len(txt) > 3:
                desc_texts.append(txt)

        if desc_texts:
            result['description'] = " | ".join(dict.fromkeys(desc_texts))[:500]

        # ── 6. Extract Contact Info (WeChat / WhatsApp / Telegram) ────────
        contact_match = re.search(
            r'(?:wechat|wx|whatsapp|telegram|contact)[:\s\=]*([+\d\w_-]{5,30})',
            html_unescaped, re.IGNORECASE
        )
        if contact_match:
            result['contact_info'] = contact_match.group(0).strip()

        # ── 7. Extract Full-Size Images ───────────────────────────────────
        big_imgs = re.findall(
            r'(?:src|data-src|data-origin-src)="(https://photo\.yupoo\.com/[^"]+(?:big|origin)\.[^"]+)"',
            html
        )
        if big_imgs:
            raw_imgs = list(dict.fromkeys(big_imgs))
        else:
            medium_imgs = re.findall(
                r'(?:src|data-src)="(https://photo\.yupoo\.com/[^"]+medium\.[^"]+)"',
                html
            )
            raw_imgs = list(dict.fromkeys(medium_imgs))

        # Reorder images to ensure front flat lay is index 0 (per user rule)
        result['images'] = self._reorder_images_front_first(raw_imgs)

        return result

    def _reorder_images_front_first(self, images: List[str]) -> List[str]:
        """Ensure front flat lay / primary cover image is positioned at index 0."""
        if not images or len(images) <= 1:
            return images

        # Check for front/cover/main in image filename/URL
        priority_indices = []
        for idx, img_url in enumerate(images):
            url_lower = img_url.lower()
            if 'front' in url_lower or 'cover' in url_lower or 'main' in url_lower:
                priority_indices.append(idx)

        if priority_indices:
            best_idx = priority_indices[0]
            return [images[best_idx]] + [img for i, img in enumerate(images) if i != best_idx]

        return images


    def scrape_seller(self, subdomain: str, max_pages: int = 1, category_id: Optional[str] = None,
                      fetch_details: bool = False, detail_delay: float = 0.5) -> List[Dict]:
        """Full scrape of a seller's catalog.
        
        Args:
            subdomain: Yupoo seller subdomain.
            max_pages: Maximum number of pages to scrape.
            category_id: Optional category filter.
            fetch_details: If True, also fetch each album's detail page for Weidian links.
            detail_delay: Delay between detail page fetches (seconds).
            
        Returns:
            List of album dicts with all extracted data.
        """
        all_albums = []
        
        for page in range(1, max_pages + 1):
            albums, has_more = self.scrape_album_list(subdomain, page=page, category_id=category_id)
            all_albums.extend(albums)
            
            if not has_more or not albums:
                break
            
            time.sleep(0.3)  # Rate limiting between pages

        # Fallback: if root /albums returned 0 items, check if seller has categories
        if not all_albums and not category_id:
            categories = self.get_categories(subdomain)
            if categories:
                safe_print(f"[Yupoo] Root /albums empty for {subdomain}, auto-traversing {len(categories)} categories...")
                for cat in categories[:max_pages * 2]:
                    cat_albums, _ = self.scrape_album_list(subdomain, page=1, category_id=cat['id'])
                    all_albums.extend(cat_albums)
                    if len(all_albums) >= 25:
                        break
                    time.sleep(0.2)

        
        # Optionally fetch detail pages for Weidian links
        if fetch_details and all_albums:
            safe_print(f"[Yupoo] Fetching detail pages for {len(all_albums)} albums...")
            for i, album in enumerate(all_albums):
                detail = self.scrape_album_detail(album['album_url'])
                album['weidian_link'] = detail['weidian_link']
                album['platform'] = detail['platform']
                album['images'] = detail['images']
                album['description'] = detail['description']
                
                if (i + 1) % 10 == 0:
                    safe_print(f"[Yupoo] Progress: {i+1}/{len(all_albums)} detail pages fetched")
                
                time.sleep(detail_delay)
        
        # Summary
        with_links = sum(1 for a in all_albums if a.get('weidian_link'))
        with_prices = sum(1 for a in all_albums if a.get('price_cny'))
        safe_print(f"[Yupoo] {subdomain}: {len(all_albums)} albums total, {with_links} with marketplace links, {with_prices} with prices")
        
        return all_albums

    def download_album_to_staging(self, subdomain: str, album: Dict, staging_dir: Path,
                                   detail: Optional[Dict] = None) -> Dict:
        """Download all high-res images from a Yupoo album to the staging directory.

        This is the CORRECT image sourcing path: images ALWAYS come from Yupoo,
        never from Weidian/Taobao/1688 (which blur brand logos).

        Args:
            subdomain: Yupoo seller subdomain.
            album: Album dict from scrape_album_list or scrape_seller.
            staging_dir: Path to write product folder into (typically input_sourcing/).
            detail: Pre-fetched detail dict. If None, will fetch from album_url.

        Returns:
            Dict with keys: folder_path, images_downloaded, metadata
        """
        # Fetch detail page if not provided
        if detail is None:
            detail = self.scrape_album_detail(album['album_url'])

        yupoo_images = detail.get('images', [])
        if not yupoo_images:
            safe_print(f"[Yupoo DL] No images found in album: {album.get('title', 'unknown')}")
            return {'folder_path': None, 'images_downloaded': 0, 'metadata': None}

        # Build folder name from title
        title = album.get('title', 'unknown_product')
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:80]
        if not slug or len(slug) < 3:
            import hashlib
            slug = f"product_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        folder = staging_dir / slug
        folder.mkdir(parents=True, exist_ok=True)

        # Download images from Yupoo
        # CRITICAL: Yupoo CDN returns HTTP 567 without proper Referer header
        album_url = self.normalize_url(album.get('album_url', ''))
        base_domain = re.match(r'(https?://[^/]+)', album_url)
        referer = base_domain.group(1) + '/' if base_domain else 'https://x.yupoo.com/'

        
        downloaded = []
        for idx, img_url in enumerate(yupoo_images, 1):
            try:
                ext = '.jpg'
                if 'png' in img_url.lower():
                    ext = '.png'
                elif 'webp' in img_url.lower():
                    ext = '.webp'
                fname = f"yupoo_{idx:02d}{ext}"
                img_path = folder / fname

                if img_path.exists() and img_path.stat().st_size > 5000:
                    downloaded.append(fname)
                    continue

                # Set Referer to the seller's Yupoo domain to bypass anti-hotlinking
                headers = {
                    'Referer': referer,
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                }
                
                # Try multiple URL variants: some CDN paths block 'big' but allow origin hash
                urls_to_try = [img_url]
                # If URL ends with /big.jpg, also try the origin hash format
                hash_match = re.search(r'/([a-f0-9]+)/big\.(\w+)', img_url)
                if hash_match:
                    h, ext_part = hash_match.group(1), hash_match.group(2)
                    # Origin format uses the hash as filename
                    origin_url = img_url.replace(f'/{h}/big.{ext_part}', f'/{h}/{h}.{ext_part}')
                    urls_to_try.insert(0, origin_url)
                    # Also try medium as fallback
                    medium_url = img_url.replace('/big.', '/medium.')
                    urls_to_try.append(medium_url)
                
                resp = None
                for try_url in urls_to_try:
                    resp = self.session.get(try_url, timeout=20, headers=headers)
                    if resp.status_code == 200 and len(resp.content) > 5000:
                        break
                
                if resp and resp.status_code == 200 and len(resp.content) > 5000:
                    ext = '.jpg'
                    if 'png' in img_url.lower():
                        ext = '.png'
                    elif 'webp' in img_url.lower():
                        ext = '.webp'
                    fname = f"yupoo_{idx:02d}{ext}"
                    img_path = folder / fname
                    img_path.write_bytes(resp.content)
                    downloaded.append(fname)
                    safe_print(f"  [Yupoo DL] Downloaded {fname} ({len(resp.content)//1024}KB)")
                else:
                    status = resp.status_code if resp else 'no response'
                    safe_print(f"  [Yupoo DL] Skipped image {idx} (status={status})")
            except Exception as e:
                safe_print(f"  [Yupoo DL] Error downloading image {idx}: {e}")
            time.sleep(0.3)  # Rate limit

        if not downloaded:
            safe_print(f"[Yupoo DL] No images downloaded for {title}. Cleaning up.")
            try:
                folder.rmdir()
            except Exception:
                pass
            return {'folder_path': None, 'images_downloaded': 0, 'metadata': None}

        # Build metadata — marketplace link is ORDERING ONLY, not image source
        metadata = {
            "product_name": title,
            "color": "default",
            "price_cny": album.get('price_cny', 0.0),
            "link": album.get('album_url', ''),  # Yupoo album as primary link
            "ordering_link": detail.get('weidian_link') or '',  # Weidian/Taobao for ORDERING ONLY
            "ordering_platform": detail.get('platform') or '',
            "image_source": "yupoo",  # CRITICAL: documents where images came from
            "yupoo_subdomain": subdomain,
            "yupoo_album_url": album.get('album_url', ''),
            "description": detail.get('description', ''),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "yupoo_scraper",
            "author": "autonomous_sourcer",
            "image_count": len(downloaded),
        }

        meta_path = folder / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        safe_print(f"[Yupoo DL] ✅ {title}: {len(downloaded)} images saved to {folder.name}")
        safe_print(f"[Yupoo DL]    Ordering link: {metadata['ordering_link'] or 'none found'}")

        return {
            'folder_path': str(folder),
            'images_downloaded': len(downloaded),
            'metadata': metadata,
        }


# ── CLI Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    subdomain = sys.argv[1] if len(sys.argv) > 1 else "goat-official"
    fetch_details = "--details" in sys.argv
    download_mode = "--download" in sys.argv
    
    # --pick N selects a specific album number to download
    pick_idx = None
    if "--pick" in sys.argv:
        try:
            pick_idx = int(sys.argv[sys.argv.index("--pick") + 1])
        except (IndexError, ValueError):
            safe_print("Usage: --pick <album_number>")
            sys.exit(1)
    
    # --max N limits how many albums to download
    max_download = 1
    if "--max" in sys.argv:
        try:
            max_download = int(sys.argv[sys.argv.index("--max") + 1])
        except (IndexError, ValueError):
            pass

    scraper = YupooScraper()
    
    # Show categories first
    categories = scraper.get_categories(subdomain)
    safe_print(f"\nCategories ({len(categories)}):")
    for c in categories[:10]:
        safe_print(f"  [{c['id']}] {c['name']}")
    
    # Scrape first page (always fetch details for download mode)
    albums = scraper.scrape_seller(subdomain, max_pages=1,
                                    fetch_details=(fetch_details or download_mode))
    
    safe_print(f"\n{'='*60}")
    safe_print(f"RESULTS: {len(albums)} albums from {subdomain}")
    safe_print(f"{'='*60}")
    
    for i, a in enumerate(albums[:20], 1):
        title = a['title'][:60]
        price = f" | CNY {a['price_cny']}" if a['price_cny'] else ""
        link_status = " [HAS LINK]" if a.get('weidian_link') else ""
        img_count = f" [{len(a.get('images', []))} imgs]" if a.get('images') else ""
        safe_print(f"  [{i}] {title}{price}{link_status}{img_count}")
        if a.get('weidian_link'):
            safe_print(f"      -> {a['weidian_link'][:100]}")
    
    # Download mode: save Yupoo images to input_sourcing/
    if download_mode and albums:
        staging_dir = Path(__file__).parent / "input_sourcing"
        staging_dir.mkdir(exist_ok=True)
        
        if pick_idx is not None:
            # Download specific album
            if 1 <= pick_idx <= len(albums):
                album = albums[pick_idx - 1]
                safe_print(f"\n📥 Downloading album [{pick_idx}]: {album['title']}")
                result = scraper.download_album_to_staging(subdomain, album, staging_dir)
                if result['images_downloaded']:
                    safe_print(f"✅ Done: {result['images_downloaded']} images → {result['folder_path']}")
                else:
                    safe_print(f"❌ Failed to download images for album [{pick_idx}]")
            else:
                safe_print(f"❌ Invalid album number {pick_idx}. Range: 1-{len(albums)}")
        else:
            # Download first N albums that have images
            downloaded = 0
            for album in albums:
                if downloaded >= max_download:
                    break
                if not album.get('images'):
                    continue
                # Skip informational/banner/agent guide albums
                title_lower = album.get('title', '').lower()
                is_banner = any(w in title_lower for w in [
                    'how to', 'whatsapp', 'discord', 'telegram', 'tiktok', 'wechat',
                    'customer review', 'reviews', 'contact', 'new yupoo', 'hot selling',
                    'brand 品牌', 'trusted agent', 'purchase', 'buy on', 'sugargoo',
                    'gtbuy', 'kakobuy', 'hippobuy', 'rizzitgo', 'micro-business',
                    '微商相册', '微店', 'stores and chat', 'goated buy', 'guide', 'agents'
                ])
                if is_banner or (not album.get('weidian_link') and len(album.get('images', [])) < 6):
                    continue



                safe_print(f"\n📥 Downloading: {album['title']}")
                result = scraper.download_album_to_staging(subdomain, album, staging_dir)
                if result['images_downloaded']:
                    downloaded += 1
                    safe_print(f"✅ Done: {result['images_downloaded']} images")
                time.sleep(1)  # Rate limit between albums
            
            safe_print(f"\n{'='*60}")
            safe_print(f"DOWNLOAD COMPLETE: {downloaded} products saved to input_sourcing/")
            safe_print(f"{'='*60}")

