"""
Reverse Image Search Engine — Multi-provider approach
=====================================================
Uses direct HTTP APIs instead of Playwright to avoid bot detection.

Providers (in priority order):
1. Bing Visual Search (direct POST with image)
2. Google Lens (via URL-based image search)

Returns supplier links from: AliExpress, 1688, Alibaba, DHgate, Taobao, Weidian
"""
import asyncio
import os
import sys
import base64
import json
import re
from typing import List, Dict

import httpx


def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode('ascii'))


SUPPLIER_DOMAINS = [
    "aliexpress.com", "1688.com", "alibaba.com", "dhgate.com",
    "taobao.com", "weidian.com", "ebay.com", "amazon.com",
    "temu.com", "shein.com",
]


async def reverse_search_bing(image_path: str) -> List[Dict]:
    """
    Upload image to Bing Visual Search API and extract shopping/supplier links.
    Uses Bing's public visual search endpoint (no API key needed).
    """
    safe_print(f"[BING] Reverse searching: {os.path.basename(image_path)}")
    results = []
    
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        filename = os.path.basename(image_path)
        
        # Bing Visual Search uses multipart form upload
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Step 1: Upload to Bing Visual Search
            files = {
                "imgurl": (None, ""),
                "cbir": (None, "sbi"),
                "imageBin": (filename, image_data, "image/jpeg"),
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            resp = await client.post(
                "https://www.bing.com/images/search?view=detailv2&iss=sbiupload&FORM=SBIHMP",
                files=files,
                headers=headers,
            )
            
            safe_print(f"[BING] Response status: {resp.status_code}")
            safe_print(f"[BING] Response URL: {str(resp.url)[:100]}")
            
            html = resp.text
            
            # Extract links from the HTML
            link_pattern = re.compile(r'href=["\']?(https?://[^"\'\s>]+)', re.IGNORECASE)
            all_links = link_pattern.findall(html)
            
            safe_print(f"[BING] Found {len(all_links)} total links in response HTML")
            
            # Filter for supplier domains
            for link in all_links:
                if any(domain in link.lower() for domain in SUPPLIER_DOMAINS):
                    results.append({
                        "url": link,
                        "source": "bing_visual",
                        "domain": next((d for d in SUPPLIER_DOMAINS if d in link.lower()), "unknown"),
                    })
                    safe_print(f"   [+] Supplier: {link[:80]}")
            
            # Also try to extract product name from page title
            title_match = re.search(r'<title>([^<]+)</title>', html)
            if title_match:
                safe_print(f"[BING] Page title: {title_match.group(1)[:60]}")
            
            # Also extract "similar products" / "shop" section links
            shop_pattern = re.compile(r'"purl":"(https?://[^"]+)"', re.IGNORECASE)
            shop_links = shop_pattern.findall(html)
            for link in shop_links:
                if any(domain in link.lower() for domain in SUPPLIER_DOMAINS):
                    if not any(r["url"] == link for r in results):
                        results.append({
                            "url": link,
                            "source": "bing_visual_shop",
                            "domain": next((d for d in SUPPLIER_DOMAINS if d in link.lower()), "unknown"),
                        })
                        safe_print(f"   [+] Shop link: {link[:80]}")
    
    except Exception as e:
        safe_print(f"[BING] Error: {e}")
    
    safe_print(f"[BING] Total supplier links found: {len(results)}")
    return results


async def reverse_search_google_lens_url(image_url: str) -> List[Dict]:
    """
    Use Google Lens via URL-based search (for images already hosted online).
    This avoids the file upload flow entirely.
    """
    safe_print(f"[LENS] Reverse searching URL: {image_url[:60]}")
    results = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }
            
            lens_url = f"https://lens.google.com/uploadbyurl?url={image_url}"
            resp = await client.get(lens_url, headers=headers)
            
            safe_print(f"[LENS] Status: {resp.status_code}")
            
            html = resp.text
            link_pattern = re.compile(r'href=["\']?(https?://[^"\'\s>]+)', re.IGNORECASE)
            all_links = link_pattern.findall(html)
            
            for link in all_links:
                if any(domain in link.lower() for domain in SUPPLIER_DOMAINS):
                    results.append({
                        "url": link,
                        "source": "google_lens",
                        "domain": next((d for d in SUPPLIER_DOMAINS if d in link.lower()), "unknown"),
                    })
                    safe_print(f"   [+] Supplier: {link[:80]}")
    
    except Exception as e:
        safe_print(f"[LENS] Error: {e}")
    
    return results


async def reverse_search_bing_stealth(image_path: str) -> List[Dict]:
    """
    Use Playwright + Stealth to query Bing Visual Search and retrieve supplier links.
    """
    safe_print(f"[BING-STEALTH] Reverse searching: {os.path.basename(image_path)}")
    results = []
    
    abs_image_path = os.path.abspath(image_path)
    if not os.path.exists(abs_image_path):
        safe_print(f"[-] Image not found: {abs_image_path}")
        return results
        
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
            await Stealth().apply_stealth_async(context)
            page = await context.new_page()
            
            # Navigate directly to the upload handler on bing.com with retries
            upload_url = "https://www.bing.com/images/search?view=detailv2&iss=sbiupload&FORM=SBIHMP"
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    safe_print(f"[BING-STEALTH] Navigating to Bing Visual Search (attempt {attempt}/{max_retries})...")
                    await page.goto(upload_url, wait_until="networkidle", timeout=45000)
                    break
                except Exception as e:
                    safe_print(f"[BING-STEALTH] Navigation attempt {attempt} failed: {e}")
                    if attempt == max_retries:
                        raise e
                    await asyncio.sleep(2)
            
            await asyncio.sleep(2)
            
            file_input = page.locator('input[type="file"]')
            if await file_input.count() > 0:
                await file_input.first.set_input_files(abs_image_path)
                # Wait 12 seconds for visual search results to load dynamically
                await asyncio.sleep(12)
                
                # Grab all links on the results page
                links = await page.query_selector_all("a")
                for a in links:
                    href = await a.get_attribute("href") or ""
                    try:
                        text = (await a.inner_text() or "").strip().replace("\n", " ")[:60]
                    except:
                        text = ""
                    
                    if href:
                        match_target = f"{href.lower()} {text.lower()}"
                        if any(domain in match_target for domain in SUPPLIER_DOMAINS):
                            # Avoid duplicates in local results
                            if not any(r["url"] == href for r in results):
                                domain_found = next((d for d in SUPPLIER_DOMAINS if d in match_target), "unknown")
                                results.append({
                                    "url": href,
                                    "source": "bing_visual_stealth",
                                    "domain": domain_found,
                                })
                                safe_print(f"   [+] Matched: {domain_found.upper()} | {href[:80]} (text: {text[:30]})")
            else:
                safe_print("[-] Bing file input element not found.")
                
            await context.close()
            await browser.close()
            
    except Exception as e:
        safe_print(f"[BING-STEALTH] Error: {e}")
        
    return results


async def reverse_search_combined(image_path: str, image_url: str = None) -> List[Dict]:
    """
    Run all available reverse search providers and combine results.
    Deduplicates by URL.
    """
    all_results = []
    
    # Provider 1: Bing Visual Search via Playwright Stealth
    bing_results = await reverse_search_bing_stealth(image_path)
    all_results.extend(bing_results)
    
    # Provider 2: Google Lens URL (disabled by default due to 429/sorry block pages)
    # if image_url:
    #     lens_results = await reverse_search_google_lens_url(image_url)
    #     all_results.extend(lens_results)
    
    # Deduplicate
    seen = set()
    unique = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    
    safe_print(f"\n[COMBINED] Total unique supplier links: {len(unique)}")
    return unique


# ── CLI TEST ──
async def main():
    test_image = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "MANUAL_CURATION",
        "balenciaga-tee_grey_20260530_124135_b39d",
        "angle_1.jpeg"
    )
    
    if not os.path.exists(test_image):
        safe_print(f"[-] Test image not found: {test_image}")
        return
    
    safe_print(f"[*] Testing reverse search with: {os.path.basename(test_image)}")
    results = await reverse_search_combined(test_image)
    
    safe_print(f"\n{'='*60}")
    safe_print(f"  REVERSE SEARCH RESULTS")
    safe_print(f"{'='*60}")
    for r in results:
        safe_print(f"  [{r['source']}] {r['domain']}: {r['url'][:80]}")
    
    if not results:
        safe_print("  (No supplier links found - the product may not have matches)")


if __name__ == "__main__":
    asyncio.run(main())

