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

import re
import json
import time
import logging
import requests
from typing import List, Dict, Optional, Tuple
from pathlib import Path
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
    "Accept-Encoding": "gzip, deflate, br",
}

# Regex patterns for marketplace URL extraction
MARKETPLACE_PATTERN = re.compile(
    r'(https?://(?:'
    r'weidian\.com/(?:item\.html|fastorder/item\.html)\?[^\s"\'<>]+'
    r'|item\.taobao\.com/item\.htm\?[^\s"\'<>]+'
    r'|detail\.1688\.com/offer/[^\s"\'<>]+'
    r'|m\.1688\.com/offer/[^\s"\'<>]+'
    r'))',
    re.IGNORECASE
)

# Price extraction from titles (e.g., "89¥ Navy Cargo Shorts" or "¥289 | Nike Tech" or "￥95 Gallery Dept")
PRICE_PATTERN = re.compile(
    r'(?:(\d+(?:\.\d+)?)\s*(?:¥|\uffe5|yuan|rmb|cny))|(?:(?:¥|\uffe5|yuan|rmb|cny)\s*(\d+(?:\.\d+)?))',
    re.IGNORECASE
)


class YupooScraper:
    """Scrapes Yupoo seller catalogs to extract album info and Weidian links."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get_page(self, url: str, timeout: int = 15) -> Optional[str]:
        """Fetch a URL and return HTML content, or None on failure."""
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

    def _extract_price(self, title: str) -> Optional[float]:
        """Extract price in CNY from an album title string."""
        match = PRICE_PATTERN.search(title)
        if match:
            price_str = match.group(1) or match.group(2)
            try:
                return float(price_str)
            except ValueError:
                pass
        return None

    def _detect_platform(self, url: str) -> str:
        """Detect marketplace platform from URL."""
        if 'weidian.com' in url:
            return 'weidian'
        elif 'taobao.com' in url:
            return 'taobao'
        elif '1688.com' in url:
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
        # Pattern 1: Category links with text content
        cat_matches = re.findall(
            r'href="/categories/(\d+)"[^>]*>\s*([^<]+)',
            html
        )
        for cat_id, cat_name in cat_matches:
            name = cat_name.strip()
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
                    'name': cat_name.strip(),
                    'url': f"{base_url}/categories/{cat_id}",
                })
                seen_ids.add(cat_id)

        return categories

    def _parse_modern_albums(self, html: str, base_url: str, seen_urls: set) -> List[Dict]:
        """Extract albums using the modern template."""
        modern_matches = re.findall(
            r'<a[^>]*href="(/albums/\d+\?[^"]+)"[^>]*title="([^"]*)"', html
        )
        modern_matches_rev = re.findall(
            r'<a[^>]*title="([^"]*)"[^>]*href="(/albums/\d+\?[^"]+)"', html
        )
        all_modern = [(url, title) for url, title in modern_matches] + \
                     [(url, title) for title, url in modern_matches_rev]
        
        albums = []
        if all_modern:
            for album_path, title in all_modern:
                if album_path in seen_urls:
                    continue
                seen_urls.add(album_path)
                
                title_clean = title.strip()
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
        return albums

    def _parse_classic_albums(self, html: str, base_url: str, seen_urls: set) -> List[Dict]:
        """Extract albums using the classic template or fallback."""
        classic_albums = re.findall(r'href="(/albums/\d+\?[^"]+)"', html)
        classic_titles = re.findall(r'class="[^"]*album__title[^"]*"[^>]*>([^<]+)', html)
        
        title_class_elements = re.findall(
            r'<(?:span|p|div)[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)', html
        )
        title_class_elements = [
            t.strip() for t in title_class_elements
            if t.strip() and 'Supplier' not in t and 'yupoo' not in t.lower()
            and len(t.strip()) > 2
        ]

        albums = []
        use_title_class = bool(title_class_elements and not classic_titles)
        use_classic_titles = bool(classic_titles)

        for i, album_path in enumerate(classic_albums):
            if album_path in seen_urls:
                continue
            seen_urls.add(album_path)

            if use_title_class:
                title = title_class_elements[i].strip() if i < len(title_class_elements) else f"Album {i+1}"
                price = self._extract_price(title)
            elif use_classic_titles:
                title = classic_titles[i].strip() if i < len(classic_titles) else f"Album {i+1}"
                price = self._extract_price(title)
            else:
                title = f"Album {i+1}"
                price = None
                
            albums.append({
                'title': title,
                'album_url': f"{base_url}{album_path}",
                'album_path': album_path,
                'price_cny': price,
                'thumbnail': None,
                'weidian_link': None,
                'platform': None,
            })
        return albums

    def _extract_thumbnails(self, html: str, albums: List[Dict]) -> None:
        """Extract thumbnails and assign them to the albums list in-place."""
        all_imgs = re.findall(
            r'(?:src|data-src)="(https://photo\.yupoo\.com/[^"]+(?:medium|small|square)\.[^"]+)"', html
        )

        unique_imgs = []
        seen_hashes = set()
        for img in all_imgs:
            hash_match = re.search(r'/([a-f0-9]+)/(?:medium|small|square)', img)
            if hash_match:
                h = hash_match.group(1)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    medium_url = re.sub(r'/(small|square)\.', '/medium.', img)
                    unique_imgs.append(medium_url)
        
        for i, album in enumerate(albums):
            if i < len(unique_imgs):
                album['thumbnail'] = unique_imgs[i]

    def _detect_pagination(self, html: str, page: int) -> bool:
        """Detect if there are more pages."""
        has_more = bool(re.search(r'page=' + str(page + 1), html))
        if not has_more:
            has_more = bool(re.search(r'class="[^"]*paginat[^"]*"', html, re.IGNORECASE))
        return has_more

    def scrape_album_list(self, subdomain: str, page: int = 1, category_id: Optional[str] = None) -> Tuple[List[Dict], bool]:
        """Scrape the album listing page for a seller.

        Args:
            subdomain: Yupoo seller subdomain (e.g., "goat-official")
            page: Page number (1-indexed). Each page shows ~48 albums.
            category_id: Optional category ID to filter by.

        Returns:
            Tuple of (list of album dicts, has_more_pages bool)
        """
        base_url = f"https://{subdomain}.x.yupoo.com"

        if category_id:
            url = f"{base_url}/categories/{category_id}?page={page}"
        else:
            url = f"{base_url}/albums?page={page}"

        html = self._get_page(url)
        if not html:
            return [], False

        seen_urls = set()

        albums = self._parse_modern_albums(html, base_url, seen_urls)
        if not albums:
            albums = self._parse_classic_albums(html, base_url, seen_urls)

        self._extract_thumbnails(html, albums)
        has_more = self._detect_pagination(html, page)

        safe_print(f"[Yupoo] {subdomain} page {page}: {len(albums)} albums, has_more={has_more}")
        return albums, has_more

    def scrape_album_detail(self, album_url: str) -> Dict:
        """Scrape an individual album detail page to extract Weidian links and full images.
        
        Args:
            album_url: Full URL to the album detail page.
            
        Returns:
            Dict with keys: weidian_link, platform, images, description
        """
        html = self._get_page(album_url)
        if not html:
            return {'weidian_link': None, 'platform': None, 'images': [], 'description': ''}

        result = {
            'weidian_link': None,
            'platform': None,
            'images': [],
            'description': '',
        }

        # ── Extract marketplace links ─────────────────────────────────────
        marketplace_links = MARKETPLACE_PATTERN.findall(html)
        if marketplace_links:
            # Take the first Weidian link if available, otherwise first match
            weidian_links = [l for l in marketplace_links if 'weidian.com' in l]
            best_link = weidian_links[0] if weidian_links else marketplace_links[0]
            result['weidian_link'] = best_link.rstrip('.,;)]}')
            result['platform'] = self._detect_platform(result['weidian_link'])

        # ── Extract description ───────────────────────────────────────────
        # Classic: <div class="showalbum__des">...</div>
        desc_matches = re.findall(r'showalbum__des[^>]*>(.*?)</div>', html, re.DOTALL)
        if desc_matches:
            # Clean HTML tags from description
            desc_text = re.sub(r'<[^>]+>', ' ', desc_matches[0]).strip()
            desc_text = re.sub(r'\s+', ' ', desc_text)
            result['description'] = desc_text[:500]
            
            # Also check description for marketplace links
            if not result['weidian_link']:
                desc_links = MARKETPLACE_PATTERN.findall(desc_matches[0])
                if desc_links:
                    result['weidian_link'] = desc_links[0].rstrip('.,;)]}')
                    result['platform'] = self._detect_platform(result['weidian_link'])

        # ── Extract full-size images ──────────────────────────────────────
        # Look for big/origin quality images on detail page
        big_imgs = re.findall(
            r'(?:src|data-src|data-origin-src)="(https://photo\.yupoo\.com/[^"]+(?:big|origin)\.[^"]+)"',
            html
        )
        if big_imgs:
            result['images'] = list(dict.fromkeys(big_imgs))  # Deduplicate preserving order
        else:
            # Fallback to medium images
            medium_imgs = re.findall(
                r'(?:src|data-src)="(https://photo\.yupoo\.com/[^"]+medium\.[^"]+)"',
                html
            )
            result['images'] = list(dict.fromkeys(medium_imgs))

        # Also check for links in general text (some sellers put links as plain text)
        if not result['weidian_link']:
            # Look for any URL-like text in the page body
            body_text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            body_links = MARKETPLACE_PATTERN.findall(body_text)
            if body_links:
                result['weidian_link'] = body_links[0].rstrip('.,;)]}')
                result['platform'] = self._detect_platform(result['weidian_link'])

        return result

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


# ── CLI Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    subdomain = sys.argv[1] if len(sys.argv) > 1 else "goat-official"
    fetch_details = "--details" in sys.argv
    
    scraper = YupooScraper()
    
    # Show categories first
    categories = scraper.get_categories(subdomain)
    safe_print(f"\nCategories ({len(categories)}):")
    for c in categories[:10]:
        safe_print(f"  [{c['id']}] {c['name']}")
    
    # Scrape first page
    albums = scraper.scrape_seller(subdomain, max_pages=1, fetch_details=fetch_details)
    
    safe_print(f"\n{'='*60}")
    safe_print(f"RESULTS: {len(albums)} albums from {subdomain}")
    safe_print(f"{'='*60}")
    
    for i, a in enumerate(albums[:20], 1):
        title = a['title'][:60]
        price = f" | CNY {a['price_cny']}" if a['price_cny'] else ""
        link_status = " [HAS LINK]" if a['weidian_link'] else ""
        safe_print(f"  [{i}] {title}{price}{link_status}")
        if a.get('weidian_link'):
            safe_print(f"      -> {a['weidian_link'][:100]}")
