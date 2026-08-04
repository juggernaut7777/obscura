"""
Spreadsheet Ingestor — Reads Google Sheets or CSV files and extracts Weidian/Taobao/1688 URLs.

Usage:
    from spreadsheet_ingestor import SpreadsheetIngestor
    ingestor = SpreadsheetIngestor()
    results = ingestor.ingest("https://docs.google.com/spreadsheets/d/abc123/edit")
    # results = [{"product_name": "...", "url": "...", "platform": "weidian", "row": 5}, ...]
"""

import re
import csv
import io
import sys
import logging
import requests
from typing import List, Dict, Optional

# ── Safe print for Windows cp1252 ──────────────────────────────────────────
def safe_print(*args, **kwargs):
    """Print that handles Unicode on Windows cp1252 terminals."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        print(text.encode("ascii", "backslashreplace").decode("ascii"), **kwargs)

# ── Logging ────────────────────────────────────────────────────────────────
log = logging.getLogger("spreadsheet_ingestor")

# ── Constants ──────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

# Regex to match Chinese marketplace URLs
MARKETPLACE_URL_PATTERN = re.compile(
    r'(https?://(?:'
    r'weidian\.com/item\.html\?[^\s"\'<>]+'
    r'|item\.taobao\.com/item\.htm\?[^\s"\'<>]+'
    r'|detail\.1688\.com/offer/[^\s"\'<>]+'
    r'|m\.1688\.com/offer/[^\s"\'<>]+'
    r'|shop\d+\.1688\.com[^\s"\'<>]*'
    r'|weidian\.com/fastorder/item\.html\?[^\s"\'<>]+'
    r'))',
    re.IGNORECASE
)

# Regex to match agent-wrapped URLs (Pandabuy, Kakobuy, CNFans, etc.)
AGENT_URL_PATTERN = re.compile(
    r'(https?://(?:'
    r'www\.pandabuy\.com/product\?[^\s"\'<>]+'
    r'|www\.kakobuy\.com/item/detail\?[^\s"\'<>]+'
    r'|www\.cnfans\.com/product/\?[^\s"\'<>]+'
    r'|www\.allchinabuy\.com/product/[^\s"\'<>]+'
    r'|www\.superbuy\.com/en/page/buy\?[^\s"\'<>]+'
    r'|www\.cssbuy\.com/item-[^\s"\'<>]+'
    r'))',
    re.IGNORECASE
)


class SpreadsheetIngestor:
    """Reads spreadsheets and extracts Chinese marketplace URLs."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _convert_google_sheets_url(self, url: str) -> List[str]:
        """Convert a Google Sheets share/edit URL to CSV export URLs (one per tab).
        
        Supports formats:
        - https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=0
        - https://docs.google.com/spreadsheets/d/SHEET_ID/edit?usp=sharing
        - https://docs.google.com/spreadsheets/d/SHEET_ID/
        """
        # Extract the sheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', url)
        if not match:
            log.warning(f"Could not extract Google Sheets ID from: {url}")
            return []
        
        sheet_id = match.group(1)
        
        # Try to get all sheet (tab) GIDs by fetching the HTML page
        csv_urls = []
        try:
            html_resp = self.session.get(url, timeout=15)
            # Extract all gid values from the page
            gids = re.findall(r'gid[=:](\d+)', html_resp.text)
            gids = list(set(gids))  # Deduplicate
            
            if gids:
                for gid in gids:
                    csv_urls.append(
                        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
                    )
            else:
                # Fallback: just export the default sheet
                csv_urls.append(
                    f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                )
        except Exception as e:
            log.warning(f"Error fetching sheet tabs: {e}")
            csv_urls.append(
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            )
        
        return csv_urls

    def _extract_marketplace_url_from_agent(self, agent_url: str) -> Optional[str]:
        """Extract the original marketplace URL from an agent-wrapped URL.
        
        Agent URLs typically contain the original URL as a query parameter:
        - Pandabuy: ?url=https://weidian.com/...
        - Kakobuy: ?url=https://weidian.com/...
        - CNFans: ?shop_type=weidian&id=12345
        """
        # Try extracting 'url' parameter
        url_match = re.search(r'[?&]url=([^&]+)', agent_url)
        if url_match:
            from urllib.parse import unquote
            return unquote(url_match.group(1))
        
        # CNFans format: shop_type=weidian&id=12345
        cnfans_match = re.search(r'shop_type=(weidian|taobao|1688)&id=(\d+)', agent_url)
        if cnfans_match:
            platform = cnfans_match.group(1)
            item_id = cnfans_match.group(2)
            if platform == 'weidian':
                return f"https://weidian.com/item.html?itemID={item_id}"
            elif platform == 'taobao':
                return f"https://item.taobao.com/item.htm?id={item_id}"
            elif platform == '1688':
                return f"https://detail.1688.com/offer/{item_id}.html"
        
        return None

    def _detect_platform(self, url: str) -> str:
        """Detect whether a URL is from Weidian, Taobao, or 1688."""
        if 'weidian.com' in url:
            return 'weidian'
        elif 'taobao.com' in url:
            return 'taobao'
        elif '1688.com' in url:
            return '1688'
        return 'unknown'

    def _extract_urls_from_text(self, text: str) -> List[Dict]:
        """Extract all marketplace URLs from a text string."""
        results = []
        seen_urls = set()
        
        # Direct marketplace URLs
        for match in MARKETPLACE_URL_PATTERN.finditer(text):
            url = match.group(1).rstrip('.,;)]}')
            if url not in seen_urls:
                seen_urls.add(url)
                results.append({
                    'url': url,
                    'platform': self._detect_platform(url),
                    'source': 'direct'
                })
        
        # Agent-wrapped URLs (unwrap to get original)
        for match in AGENT_URL_PATTERN.finditer(text):
            agent_url = match.group(1).rstrip('.,;)]}')
            original = self._extract_marketplace_url_from_agent(agent_url)
            if original and original not in seen_urls:
                seen_urls.add(original)
                results.append({
                    'url': original,
                    'platform': self._detect_platform(original),
                    'source': 'agent_unwrapped'
                })
        
        return results

    def _parse_csv_content(self, csv_text: str) -> List[Dict]:
        """Parse CSV content and extract marketplace URLs with row context."""
        results = []
        seen_urls = set()
        
        reader = csv.reader(io.StringIO(csv_text))
        header_row = None
        
        for row_num, row in enumerate(reader, start=1):
            if not row:
                continue
            
            # Try to detect header row
            if row_num == 1:
                header_row = row
                # Check if this row is actually a header (no URLs in it)
                row_text = ' '.join(row)
                if not MARKETPLACE_URL_PATTERN.search(row_text) and not AGENT_URL_PATTERN.search(row_text):
                    continue
            
            # Join all cells and search for URLs
            row_text = ' '.join(str(cell) for cell in row)
            urls_found = self._extract_urls_from_text(row_text)
            
            for url_info in urls_found:
                if url_info['url'] in seen_urls:
                    continue
                seen_urls.add(url_info['url'])
                
                # Try to find product name from the row context
                product_name = ''
                for cell in row:
                    cell_str = str(cell).strip()
                    # Skip cells that are URLs or very short
                    if cell_str and len(cell_str) > 3 and not cell_str.startswith('http'):
                        product_name = cell_str[:150]
                        break
                
                # Try to find category from header context
                category = ''
                if header_row:
                    for i, header_cell in enumerate(header_row):
                        if i < len(row) and row[i] and 'http' in str(row[i]):
                            category = str(header_cell).strip()
                            break
                
                results.append({
                    'product_name': product_name,
                    'url': url_info['url'],
                    'platform': url_info['platform'],
                    'source': url_info['source'],
                    'row': row_num,
                    'category': category,
                })
        
        return results

    def ingest(self, url: str) -> List[Dict]:
        """Ingest a spreadsheet URL and return extracted marketplace links.
        
        Args:
            url: Google Sheets URL or direct CSV URL.
            
        Returns:
            List of dicts with keys: product_name, url, platform, source, row, category
        """
        all_results = []
        
        if 'docs.google.com/spreadsheets' in url:
            safe_print(f"[Spreadsheet] Detected Google Sheets URL, converting to CSV export...")
            csv_urls = self._convert_google_sheets_url(url)
            safe_print(f"[Spreadsheet] Found {len(csv_urls)} sheet tab(s) to process")
        elif url.endswith('.csv'):
            csv_urls = [url]
        else:
            # Try it as a direct URL
            csv_urls = [url]
        
        for i, csv_url in enumerate(csv_urls):
            safe_print(f"[Spreadsheet] Downloading tab {i+1}/{len(csv_urls)}...")
            try:
                resp = self.session.get(csv_url, timeout=30)
                if resp.status_code != 200:
                    safe_print(f"[Spreadsheet] HTTP {resp.status_code} for tab {i+1}, skipping")
                    continue
                
                results = self._parse_csv_content(resp.text)
                safe_print(f"[Spreadsheet] Tab {i+1}: found {len(results)} marketplace link(s)")
                all_results.extend(results)
                
            except Exception as e:
                safe_print(f"[Spreadsheet] Error processing tab {i+1}: {e}")
        
        # Deduplicate across tabs
        seen = set()
        deduped = []
        for r in all_results:
            if r['url'] not in seen:
                seen.add(r['url'])
                deduped.append(r)
        
        safe_print(f"[Spreadsheet] Total unique marketplace links: {len(deduped)}")
        return deduped


# ── CLI Test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        safe_print("Usage: python spreadsheet_ingestor.py <google_sheets_url_or_csv_url>")
        sys.exit(1)
    
    ingestor = SpreadsheetIngestor()
    results = ingestor.ingest(sys.argv[1])
    
    safe_print(f"\n{'='*60}")
    safe_print(f"RESULTS: {len(results)} marketplace links found")
    safe_print(f"{'='*60}")
    
    for i, r in enumerate(results, 1):
        name = r['product_name'][:50] if r['product_name'] else '(unnamed)'
        safe_print(f"  [{i}] {name}")
        safe_print(f"      {r['platform']}: {r['url'][:100]}")
        if r['category']:
            safe_print(f"      Category: {r['category']}")
