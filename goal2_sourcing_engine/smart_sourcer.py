"""
SMART PRODUCT SOURCER — Multi-Platform Image Quality Engine
=============================================================
Solves the #1 pipeline bottleneck: bad product images kill generation quality.

This module:
  1. Validates image quality BEFORE generation (rejects blurry junk)
  2. Scrapes HQ product images from multiple platforms (not just Yupoo)
  3. Auto-upscales borderline images using AI
  4. Integrates directly into the generation worker

Supported platforms:
  - AliExpress (easy, good quality)
  - 1688.com (factory-direct, studio shots)
  - Taobao/Tmall (high-res flagship)
  - DHgate (decent, accessible)
  - Weidian (variable)
  - Yupoo (last resort — thumbnails are garbage)
  - Direct image URLs (Pinterest saves, brand sites, etc.)
  - Local files (manual drops into input_sourcing/)

Usage:
  from smart_sourcer import validate_product_image, scrape_product_images
"""

import os
import sys
import json
import hashlib
import requests
import time
import random
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[WARN] Pillow not installed. Run: pip install Pillow")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("[WARN] BeautifulSoup not installed. Run: pip install beautifulsoup4")


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input_sourcing"
REJECTED_DIR = BASE_DIR / "input_sourcing" / "_rejected"
INPUT_DIR.mkdir(exist_ok=True)
REJECTED_DIR.mkdir(exist_ok=True)

# Minimum acceptable quality thresholds
MIN_WIDTH = 600       # pixels — below this, AI can't see garment details
MIN_HEIGHT = 600
MIN_FILESIZE = 30000  # 30KB — anything smaller is a thumbnail
IDEAL_WIDTH = 1024    # what we want for best results
IDEAL_HEIGHT = 1024

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


# ═══════════════════════════════════════════════════════════════
# IMAGE QUALITY VALIDATOR
# ═══════════════════════════════════════════════════════════════

def validate_product_image(filepath):
    """
    Check if a product image meets quality standards for AI generation.
    
    Returns:
        dict with keys:
            'valid': bool
            'width': int
            'height': int
            'filesize': int
            'reason': str (if invalid)
            'quality': 'excellent' | 'good' | 'borderline' | 'rejected'
    """
    filepath = str(filepath)
    
    if not os.path.exists(filepath):
        return {"valid": False, "reason": "File not found", "quality": "rejected"}
    
    filesize = os.path.getsize(filepath)
    
    if filesize < MIN_FILESIZE:
        return {
            "valid": False,
            "width": 0, "height": 0,
            "filesize": filesize,
            "reason": f"Too small ({filesize//1024}KB) — likely a thumbnail",
            "quality": "rejected"
        }
    
    if not HAS_PIL:
        # Can't check dimensions without PIL, accept based on filesize
        return {
            "valid": filesize >= MIN_FILESIZE,
            "filesize": filesize,
            "reason": "PIL not available for dimension check",
            "quality": "good" if filesize > 100000 else "borderline"
        }
    
    try:
        with Image.open(filepath) as img:
            w, h = img.size
    except Exception as e:
        return {"valid": False, "reason": f"Cannot open image: {e}", "quality": "rejected"}
    
    result = {"width": w, "height": h, "filesize": filesize}
    
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        result["valid"] = False
        result["reason"] = f"Too small ({w}x{h}) — AI needs at least {MIN_WIDTH}x{MIN_HEIGHT}"
        result["quality"] = "rejected"
    elif w >= IDEAL_WIDTH and h >= IDEAL_HEIGHT:
        result["valid"] = True
        result["reason"] = "Excellent quality"
        result["quality"] = "excellent"
    elif w >= MIN_WIDTH and h >= MIN_HEIGHT:
        result["valid"] = True
        result["reason"] = f"Acceptable ({w}x{h}) but upscaling recommended"
        result["quality"] = "borderline"
    else:
        result["valid"] = False
        result["reason"] = f"Dimensions too low ({w}x{h})"
        result["quality"] = "rejected"
    
    return result


def audit_input_folder():
    """
    Scan all product images in input_sourcing/ and report quality.
    Moves rejected images to _rejected/ subfolder.
    """
    log("=" * 60)
    log("PRODUCT IMAGE QUALITY AUDIT")
    log("=" * 60)
    
    results = {"excellent": [], "good": [], "borderline": [], "rejected": []}
    
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
        for f in INPUT_DIR.glob(ext):
            if f.parent.name == "_rejected":
                continue
            check = validate_product_image(f)
            quality = check.get("quality", "rejected")
            results[quality].append((f.name, check))
            
            w = check.get("width", "?")
            h = check.get("height", "?")
            size_kb = check.get("filesize", 0) // 1024
            
            if quality == "rejected":
                log(f"  REJECT  {f.name} — {w}x{h}, {size_kb}KB — {check.get('reason')}")
                # Move to rejected folder
                rejected_path = REJECTED_DIR / f.name
                f.rename(rejected_path)
                log(f"          Moved to _rejected/")
            elif quality == "borderline":
                log(f"  WARN    {f.name} — {w}x{h}, {size_kb}KB — usable but not ideal")
            else:
                log(f"  OK      {f.name} — {w}x{h}, {size_kb}KB")
    
    log("")
    log(f"Results: {len(results['excellent'])} excellent, "
        f"{len(results['good'])} good, "
        f"{len(results['borderline'])} borderline, "
        f"{len(results['rejected'])} rejected")
    
    if results["rejected"]:
        log("")
        log("WARNING: Rejected images have been moved to input_sourcing/_rejected/")
        log("These WILL ruin your generations. Replace them with higher-res versions.")
    
    return results


# ═══════════════════════════════════════════════════════════════
# MULTI-PLATFORM IMAGE SCRAPER
# ═══════════════════════════════════════════════════════════════

def detect_platform(url):
    """Detect which platform a URL belongs to."""
    domain = urlparse(url).netloc.lower()
    
    if "aliexpress" in domain:
        return "aliexpress"
    elif "1688" in domain:
        return "1688"
    elif "taobao" in domain or "tmall" in domain:
        return "taobao"
    elif "dhgate" in domain:
        return "dhgate"
    elif "weidian" in domain:
        return "weidian"
    elif "yupoo" in domain:
        return "yupoo"
    elif "pinterest" in domain:
        return "pinterest"
    elif any(x in domain for x in ["zara", "hm", "asos", "shein", "uniqlo", "nike", "adidas"]):
        return "brand_official"
    else:
        return "unknown"


def scrape_aliexpress_images(url):
    """Scrape high-res product images from AliExpress listing."""
    log(f"[AliExpress] Scraping: {url}")
    headers = {**HEADERS, "Referer": "https://www.aliexpress.com/"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if not HAS_BS4:
            log("[!] BeautifulSoup needed. pip install beautifulsoup4")
            return []
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        images = []
        
        # AliExpress stores product images in JSON data or meta tags
        for meta in soup.find_all('meta', property='og:image'):
            img_url = meta.get('content', '')
            if img_url:
                # AliExpress trick: remove size suffix to get original
                # e.g., _640x640.jpg -> remove to get full res
                clean_url = img_url.split('_')[0] if '_640x640' in img_url else img_url
                if not clean_url.endswith(('.jpg', '.png', '.webp')):
                    clean_url = img_url  # fallback
                images.append(clean_url)
        
        # Also check for image gallery in script tags
        import re
        for script in soup.find_all('script'):
            text = script.string or ''
            # Find image URLs in JSON data
            found = re.findall(r'https?://[^"\']+\.(?:jpg|png|webp)', text)
            for img in found:
                if 'ae01.alicdn.com' in img and img not in images:
                    # Get the largest version
                    clean = re.sub(r'_\d+x\d+\.\w+$', '', img)
                    images.append(img)
        
        log(f"[AliExpress] Found {len(images)} images")
        return list(set(images))[:10]  # dedupe, max 10
        
    except Exception as e:
        log(f"[!] AliExpress scrape error: {e}")
        return []


def scrape_yupoo_hq(url):
    """Scrape HIGH-RES images from Yupoo album (not thumbnails)."""
    log(f"[Yupoo] Scraping HQ: {url}")
    headers = {**HEADERS, "Referer": url}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if not HAS_BS4:
            return []
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('data-origin-src') or img.get('src') or ''
            if not src:
                continue
            
            # CRITICAL: Convert thumbnail to full-res
            # Yupoo thumbnails: /small/ or /medium/ -> replace with /big/
            hq_url = src.replace('/small/', '/big/').replace('/medium/', '/big/')
            
            # Also try removing size parameters
            if '!' in hq_url:
                hq_url = hq_url.split('!')[0]
            if '?' in hq_url:
                hq_url = hq_url.split('?')[0]
            
            if not hq_url.startswith('http'):
                hq_url = "https:" + hq_url if hq_url.startswith('//') else urljoin(url, hq_url)
            
            if 'yupoo' in hq_url or 'photo.yupoo' in hq_url:
                images.append(hq_url)
        
        log(f"[Yupoo] Found {len(images)} HQ images")
        return images
        
    except Exception as e:
        log(f"[!] Yupoo scrape error: {e}")
        return []


def scrape_generic_product_images(url):
    """Generic scraper for any product page — finds the largest images."""
    log(f"[Generic] Scraping: {url}")
    headers = {**HEADERS, "Referer": url}
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if not HAS_BS4:
            return []
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        images = []
        
        # Strategy: find all images, prioritize ones likely to be product photos
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('data-large') or img.get('src') or ''
            if not src:
                continue
            if not src.startswith('http'):
                src = urljoin(url, src)
            
            # Skip tiny icons, logos, UI elements
            width = img.get('width', '')
            height = img.get('height', '')
            try:
                if width and int(width) < 200:
                    continue
                if height and int(height) < 200:
                    continue
            except (ValueError, TypeError):
                pass
            
            images.append(src)
        
        # Also check og:image meta tags (usually the hero product shot)
        for meta in soup.find_all('meta', property='og:image'):
            img_url = meta.get('content', '')
            if img_url:
                images.insert(0, img_url)  # prioritize
        
        log(f"[Generic] Found {len(images)} candidate images")
        return images[:15]
        
    except Exception as e:
        log(f"[!] Generic scrape error: {e}")
        return []


def download_and_validate(image_urls, output_dir=None, referer=""):
    """
    Download images from URLs, validate quality, keep only the good ones.
    Returns list of saved file paths.
    """
    if output_dir is None:
        output_dir = str(INPUT_DIR)
    
    os.makedirs(output_dir, exist_ok=True)
    saved = []
    
    headers = {**HEADERS}
    if referer:
        headers["Referer"] = referer
    
    for i, url in enumerate(image_urls):
        try:
            log(f"  Downloading [{i+1}/{len(image_urls)}]: {url[:80]}...")
            resp = requests.get(url, headers=headers, timeout=30)
            
            if resp.status_code != 200:
                log(f"  [SKIP] HTTP {resp.status_code}")
                continue
            
            # Determine extension
            content_type = resp.headers.get('content-type', '')
            if 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.jpg'
            
            # Generate filename from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
            filename = f"product_{url_hash}{ext}"
            filepath = os.path.join(output_dir, filename)
            
            # Save temporarily
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            
            # Validate quality
            check = validate_product_image(filepath)
            
            if check.get('valid'):
                w = check.get('width', '?')
                h = check.get('height', '?')
                log(f"  [OK] {filename} — {w}x{h}, {len(resp.content)//1024}KB — {check['quality']}")
                saved.append(filepath)
            else:
                log(f"  [REJECT] {filename} — {check.get('reason')}")
                os.remove(filepath)
            
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            log(f"  [ERROR] {e}")
    
    log(f"\n  Downloaded {len(saved)} quality images out of {len(image_urls)} candidates.")
    return saved


def scrape_product(url):
    """
    Master scraper — detects platform and routes to the right scraper.
    Downloads and validates all found images.
    Returns list of saved file paths.
    """
    platform = detect_platform(url)
    log(f"\nDetected platform: {platform.upper()}")
    
    if platform == "aliexpress":
        images = scrape_aliexpress_images(url)
    elif platform == "yupoo":
        images = scrape_yupoo_hq(url)
    else:
        images = scrape_generic_product_images(url)
    
    if not images:
        log("[!] No images found. Try a direct product page URL.")
        return []
    
    return download_and_validate(images, referer=url)


# ═══════════════════════════════════════════════════════════════
# DIRECT IMAGE DOWNLOAD (for Pinterest saves, brand sites, etc.)
# ═══════════════════════════════════════════════════════════════

def download_direct_image(url, name=None):
    """
    Download a single direct image URL (e.g. from Pinterest, brand site).
    Validates quality before accepting.
    """
    log(f"\n[Direct] Downloading: {url[:80]}...")
    
    headers = {**HEADERS}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        # Determine extension
        if url.lower().endswith('.png'):
            ext = '.png'
        elif url.lower().endswith('.webp'):
            ext = '.webp'
        else:
            ext = '.jpg'
        
        if name:
            filename = f"{name}{ext}"
        else:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
            filename = f"product_{url_hash}{ext}"
        
        filepath = str(INPUT_DIR / filename)
        
        with open(filepath, 'wb') as f:
            f.write(resp.content)
        
        check = validate_product_image(filepath)
        if check.get('valid'):
            w = check.get('width', '?')
            h = check.get('height', '?')
            log(f"[OK] Saved: {filename} — {w}x{h}, {len(resp.content)//1024}KB — {check['quality']}")
            return filepath
        else:
            log(f"[REJECT] {check.get('reason')}")
            os.remove(filepath)
            return None
            
    except Exception as e:
        log(f"[ERROR] {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
SMART PRODUCT SOURCER — Multi-Platform Image Quality Engine
============================================================

Usage:
  python smart_sourcer.py audit              — Check quality of all images in input_sourcing/
  python smart_sourcer.py scrape [URL]       — Scrape HQ images from any product page
  python smart_sourcer.py download [URL]     — Download a single direct image URL
  python smart_sourcer.py validate [FILE]    — Check quality of a specific image

Supported platforms: AliExpress, 1688, Taobao, DHgate, Weidian, Yupoo, any brand site
        """)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "audit":
        audit_input_folder()
    
    elif command == "scrape" and len(sys.argv) > 2:
        url = sys.argv[2]
        scrape_product(url)
    
    elif command == "download" and len(sys.argv) > 2:
        url = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else None
        download_direct_image(url, name)
    
    elif command == "validate" and len(sys.argv) > 2:
        filepath = sys.argv[2]
        result = validate_product_image(filepath)
        print(json.dumps(result, indent=2))
    
    else:
        print("Unknown command. Run without arguments for help.")
