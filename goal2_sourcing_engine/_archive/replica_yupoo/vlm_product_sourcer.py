"""
VLM AUTONOMOUS SOURCING ENGINE v3 — CONTACT SHEET CURATION
============================================================
TWO-PHASE WORKFLOW:
  Phase 1 (This file — runs automatically):
    1. Browse Yupoo seller albums
    2. Download THUMBNAILS only (fast, ~20-50KB each)
    3. Compile thumbnails into numbered CONTACT SHEETS (Pillow grid)
    4. Send contact sheets to Discord for human review
    5. Save image URL mapping to review_pending/{message_id}.json

  Phase 2 (discord_listener.py — triggered by user reply):
    1. User replies to contact sheet on Discord: "2, 5, 12"
    2. Bot downloads ONLY those HQ images from Yupoo CDN
    3. VLM evaluates selected images (product / size_chart / other)
    4. Saves to MANUAL_CURATION for AI generation pipeline
"""

import os
import json
import uuid
import asyncio
import base64
import re
import math
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import httpx
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

# Safe print for Windows (avoids UnicodeEncodeError on cp1252)
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_SOURCING_DIR = os.path.join(BASE_DIR, "input_sourcing")
REVIEW_PENDING_DIR = os.path.join(BASE_DIR, "review_pending")
MANUAL_CURATION_DIR = os.path.join(BASE_DIR, "MANUAL_CURATION")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(INPUT_SOURCING_DIR, exist_ok=True)
os.makedirs(REVIEW_PENDING_DIR, exist_ok=True)
os.makedirs(MANUAL_CURATION_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ── PERSISTENT DEDUP HISTORY (never gets deleted, unlike review_pending) ──
SCRAPED_HISTORY_FILE = os.path.join(DATA_DIR, "scraped_albums_history.json")


def _normalize_url(url: str) -> str:
    """Normalize a Yupoo album URL for consistent dedup comparison.
    If it is an album page, extracts the unique integer album ID to ensure
    subdomain-independent deduplication. Otherwise, normalizes domain/path."""
    if not url:
        return ""
    
    # Extract Yupoo album ID (/albums/12345678)
    album_match = re.search(r'/albums/(\d+)', url)
    if album_match:
        return f"yupoo_album_{album_match.group(1)}"
        
    url = url.split("?")[0].strip().rstrip("/")
    # Force https
    url = url.replace("http://", "https://")
    # Lowercase just the domain portion (before first single /)
    if "://" in url:
        proto, rest = url.split("://", 1)
        if "/" in rest:
            domain, path = rest.split("/", 1)
            url = f"{proto}://{domain.lower()}/{path}"
        else:
            url = f"{proto}://{rest.lower()}"
    return url

# Define known Yupoo sellers to monitor (Active Sellers & Categories only)
SELLERS = [
    {
        "id": "topacney",
        "name": "TopAcney (Premium Acne Studios Clothing)",
        "base_url": "https://topacney.x.yupoo.com",
        "categories": {
            "latest": "https://topacney.x.yupoo.com/albums"
        }
    },
    # ── CLOTHING HEAVY ──
    {
        "id": "taurus",
        "name": "Taurus-Reps (Margiela, Balenciaga, Acne, Loewe, Corteiz, Bape, Stussy)",
        "base_url": "https://deateath.x.yupoo.com",
        "categories": {
            "balenciaga_clothing": "https://deateath.x.yupoo.com/categories/4568347",
            "acne_studios": "https://deateath.x.yupoo.com/categories/4645865",
            "bape": "https://deateath.x.yupoo.com/categories/4578590",
            "loewe_clothing": "https://deateath.x.yupoo.com/categories/4625872",
            "corteiz": "https://deateath.x.yupoo.com/categories/4572053",
            "maison_margiela": "https://deateath.x.yupoo.com/categories/4634017",
            "stussy": "https://deateath.x.yupoo.com/categories/4563382",
            "gallery_dept": "https://deateath.x.yupoo.com/categories/4578564",
            "latest": "https://deateath.x.yupoo.com/albums"
        }
    },
    {
        "id": "3madman",
        "name": "3madman (Archive, Chrome Hearts, Deconstructed)",
        "base_url": "https://3madman.x.yupoo.com",
        "categories": {
            "chrome_hearts": "https://3madman.x.yupoo.com/categories/4462115",
            "latest": "https://3madman.x.yupoo.com/albums"
        }
    },
    {
        "id": "goat",
        "name": "Goat (Corteiz, Tech Tracksuits, Sets)",
        "base_url": "https://goat-official.x.yupoo.com",
        "categories": {
            "corteiz": "https://goat-official.x.yupoo.com/categories/3848149",
            "tracksuits": "https://goat-official.x.yupoo.com/categories/5144216",
            "latest": "https://goat-official.x.yupoo.com/albums"
        }
    },
    {
        "id": "kobe_factory",
        "name": "Kobe Factory (Essentials, Fear of God, Rick Owens)",
        "base_url": "https://kobefactory.x.yupoo.com",
        "categories": {
            "essentials": "https://kobefactory.x.yupoo.com/albums",
        }
    },
    {
        "id": "fog_store",
        "name": "FOG Store (Fear of God, Essentials, Gallery Dept)",
        "base_url": "https://fogstore.x.yupoo.com",
        "categories": {
            "all": "https://fogstore.x.yupoo.com/albums"
        }
    },
    {
        "id": "allsole",
        "name": "Allsole Store (Mixed Luxury Streetwear + Hoodies)",
        "base_url": "https://allsole-store.x.yupoo.com",
        "categories": {
            "all": "https://allsole-store.x.yupoo.com/albums"
        }
    },
    {
        "id": "shark_breeder",
        "name": "Shark Breeder (Hoodies, Cargos, Sets)",
        "base_url": "https://shark-breeder.x.yupoo.com",
        "categories": {
            "hoodies": "https://shark-breeder.x.yupoo.com/albums"
        }
    },
    {
        "id": "cnfashion",
        "name": "CN Fashion Rep (Stone Island, CP Company, Moncler)",
        "base_url": "https://cnfashionrep.x.yupoo.com",
        "categories": {
            "stone_island": "https://cnfashionrep.x.yupoo.com/albums"
        }
    },
    {
        "id": "luxurygoods",
        "name": "Luxury Goods Rep (LV, Gucci, Prada Accessories + Bags)",
        "base_url": "https://luxurygoodsrep.x.yupoo.com",
        "categories": {
            "bags": "https://luxurygoodsrep.x.yupoo.com/albums"
        }
    },
    {
        "id": "ddshop",
        "name": "DD Shop (Off-White, Carhartt, Stussy Hoodies + Jackets)",
        "base_url": "https://ddshop168.x.yupoo.com",
        "categories": {
            "latest": "https://ddshop168.x.yupoo.com/albums"
        }
    },
    {
        "id": "tophat",
        "name": "TopHat (Supreme, Palace, Bape Hoodies + Tees)",
        "base_url": "https://tophatfashion.x.yupoo.com",
        "categories": {
            "supreme": "https://tophatfashion.x.yupoo.com/albums"
        }
    },
    # ── SHOES (intentionally limited to balance) ──
    {
        "id": "wwtop",
        "name": "WWTOP (Jordans, Dior B23, Loewe Shoes)",
        "base_url": "https://wwfake100.x.yupoo.com",
        "categories": {
            "jordan": "https://wwfake100.x.yupoo.com/categories/4333842",
            "dior_shoes": "https://wwfake100.x.yupoo.com/categories/4333857",
        }
    },
    # ── ACCESSORIES & BAGS ──
    {
        "id": "bagking",
        "name": "Bag King (Designer Bags - LV, Gucci, Dior, Prada)",
        "base_url": "https://bagkingrep.x.yupoo.com",
        "categories": {
            "all": "https://bagkingrep.x.yupoo.com/albums"
        }
    },
    {
        "id": "watchrep",
        "name": "Watch Rep (Rolex, AP, Cartier, Omega)",
        "base_url": "https://watchrep168.x.yupoo.com",
        "categories": {
            "all": "https://watchrep168.x.yupoo.com/albums"
        }
    },
]

# ── CATEGORY PRIORITY WEIGHTS (used by scout to pick what to scrape first) ──
# Higher weight = scraped more often
CATEGORY_WEIGHTS = {
    "hoodies": 0.25,
    "tracksuits": 0.20,
    "cargos": 0.15,
    "bags": 0.15,
    "accessories": 0.10,
    "shoes": 0.10,   # Intentionally deprioritised — already oversupplied
    "tees": 0.05,
}


# Discord channel ID for review (set in .env or hardcode)
DISCORD_REVIEW_CHANNEL = os.getenv("DISCORD_REVIEW_CHANNEL", "")

def _load_persistent_history() -> set:
    """Load the permanent scraped album history file. This NEVER gets deleted."""
    if os.path.exists(SCRAPED_HISTORY_FILE):
        try:
            with open(SCRAPED_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                raw_urls = data.get("scraped_urls", [])
                normalized_urls = set()
                for url in raw_urls:
                    norm = _normalize_url(url)
                    if norm:
                        normalized_urls.add(norm)
                return normalized_urls
        except:
            pass
    return set()


def _save_to_persistent_history(album_url: str):
    """Permanently record an album URL so we never scrape it again, even after cleanup."""
    history = _load_persistent_history()
    normalized = _normalize_url(album_url)
    if not normalized or normalized in history:
        return  # Already recorded or empty
    history.add(normalized)
    try:
        with open(SCRAPED_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "scraped_urls": sorted(list(history)),
                "total_count": len(history),
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)
    except Exception as e:
        safe_print(f"   [!] Failed to save persistent history: {e}")


def _save_batch_to_persistent_history(album_urls: list):
    """Save multiple album URLs to persistent history in a single write."""
    history = _load_persistent_history()
    added = 0
    for url in album_urls:
        normalized = _normalize_url(url)
        if normalized and normalized not in history:
            history.add(normalized)
            added += 1
    if added > 0:
        try:
            with open(SCRAPED_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "scraped_urls": sorted(list(history)),
                    "total_count": len(history),
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
            safe_print(f"   [HISTORY] Saved {added} new URLs to persistent history (total: {len(history)})")
        except Exception as e:
            safe_print(f"   [!] Failed to save persistent history batch: {e}")


def _backfill_persistent_history():
    """Scan review_pending/ and MANUAL_CURATION/ to rebuild persistent history.
    This ensures we never lose dedup data even if the history file was deleted."""
    safe_print("[*] Backfilling persistent history from existing data...")
    found_urls = []

    # 1. Scan review_pending/ JSON files
    if os.path.exists(REVIEW_PENDING_DIR):
        for fname in os.listdir(REVIEW_PENDING_DIR):
            if fname.endswith(".json"):
                fpath = os.path.join(REVIEW_PENDING_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        album_url = data.get("album_url")
                        if album_url:
                            found_urls.append(album_url)
                except:
                    pass

    # 2. Scan MANUAL_CURATION/ subdirectories
    if os.path.exists(MANUAL_CURATION_DIR):
        for dirname in os.listdir(MANUAL_CURATION_DIR):
            dirpath = os.path.join(MANUAL_CURATION_DIR, dirname)
            if os.path.isdir(dirpath):
                meta_path = os.path.join(dirpath, "metadata.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            album_url = data.get("album_url")
                            if album_url:
                                found_urls.append(album_url)
                    except:
                        pass

    if found_urls:
        _save_batch_to_persistent_history(found_urls)
        safe_print(f"   [BACKFILL] Recovered {len(found_urls)} album URLs from existing data")
    else:
        # Create the file even if empty so it exists for future writes
        if not os.path.exists(SCRAPED_HISTORY_FILE):
            try:
                with open(SCRAPED_HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump({"scraped_urls": [], "total_count": 0, "last_updated": datetime.now().isoformat()}, f, indent=2)
                safe_print("   [BACKFILL] Created empty persistent history file")
            except Exception as e:
                safe_print(f"   [!] Failed to create history file: {e}")


def get_scraped_album_urls() -> set:
    """Build dedup set from ALL sources: persistent history + pending reviews + curated folders."""
    urls = set()
    
    # 0. PERMANENT HISTORY (the primary dedup source — never deleted)
    urls.update(_load_persistent_history())
    
    # 1. Read review_pending JSON files (secondary, gets cleaned up)
    if os.path.exists(REVIEW_PENDING_DIR):
        for fname in os.listdir(REVIEW_PENDING_DIR):
            if fname.endswith(".json"):
                fpath = os.path.join(REVIEW_PENDING_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        album_url = data.get("album_url")
                        if album_url:
                            urls.add(_normalize_url(album_url))
                except:
                    pass
                    
    # 2. Read MANUAL_CURATION subdirectories
    if os.path.exists(MANUAL_CURATION_DIR):
        for dirname in os.listdir(MANUAL_CURATION_DIR):
            dirpath = os.path.join(MANUAL_CURATION_DIR, dirname)
            if os.path.isdir(dirpath):
                meta_path = os.path.join(dirpath, "metadata.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            album_url = data.get("album_url")
                            if album_url:
                                urls.add(_normalize_url(album_url))
                    except:
                        pass
    
    safe_print(f"   [DEDUP] {len(urls)} album URLs in dedup set (persistent + pending + curated)")
    return urls


# ─── Contact Sheet Configuration ───
GRID_COLS = 4          # 4 thumbnails per row
THUMB_SIZE = 200       # Each thumbnail is 200x200px (reduced for faster loading)
BADGE_RADIUS = 18      # Size of the numbered circle badge
BADGE_COLOR = (220, 20, 60)   # Crimson red
BADGE_TEXT = (255, 255, 255)   # White text
SHEET_BG = (18, 18, 18)       # Dark background
PADDING = 8                    # Padding between thumbnails


def parse_album_text(raw_text: str) -> dict:
    """
    Parse the raw album page text into structured metadata.
    Extracts: product title, price, WhatsApp, WeChat, Discord, Weidian/Taobao links.
    """
    info = {
        "whatsapp": "",
        "wechat": "",
        "discord_invite": "",
        "price_cny": 0,
        "purchase_links": [],
    }

    # WhatsApp - strip ALL unicode invisible chars first
    cleaned = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\u202a\u202b\u202c\u202d\u202e\ufeff]', '', raw_text)
    wa_match = re.search(r'[Ww]hats?\s*[Aa]pp[^+\d]*([+]?[\d\s\-()]{8,20})', cleaned)
    if wa_match:
        info["whatsapp"] = re.sub(r'[\s]', '', wa_match.group(1))

    # WeChat - also strip unicode invisible chars
    wc_match = re.search(r'[Ww]e\s*[Cc]hat[^\w]*([\w]+)', cleaned)
    if wc_match:
        info["wechat"] = wc_match.group(1).strip()

    # Discord
    dc_match = re.search(r'(https?://discord\.gg/\S+)', raw_text)
    if dc_match:
        info["discord_invite"] = dc_match.group(1)

    # Price (¥ or "Price:" pattern)
    price_match = re.search(r'[Pp]rice[:\s]*[¥￥]?\s*(\d+)', raw_text)
    if price_match:
        info["price_cny"] = int(price_match.group(1))
    else:
        yen_match = re.search(r'[¥￥]\s*(\d+)', raw_text)
        if yen_match:
            info["price_cny"] = int(yen_match.group(1))

    # Purchase links (Weidian, Taobao, 1688)
    link_matches = re.findall(
        r'https?://(?:[a-zA-Z0-9-]+\.)*(?:weidian\.com|taobao\.com|1688\.com|detail\.tmall\.com|item\.taobao\.com)[^\s<>"\']+',
        raw_text
    )
    info["purchase_links"] = list(set(link_matches))

    return info


def create_contact_sheets(thumb_paths: List[str], start_index: int = 1) -> List[str]:
    """
    Build numbered contact sheet grids from a list of thumbnail image paths.
    Returns a list of contact sheet image paths.
    
    Each thumbnail gets a red circle badge with its index number in the top-left corner.
    Images are arranged in a grid of GRID_COLS columns.
    Max 24 images per sheet (4x6). If more, creates multiple sheets.
    """
    MAX_PER_SHEET = 24  # 4 cols x 6 rows
    sheets = []
    
    for chunk_start in range(0, len(thumb_paths), MAX_PER_SHEET):
        chunk = thumb_paths[chunk_start:chunk_start + MAX_PER_SHEET]
        num_rows = math.ceil(len(chunk) / GRID_COLS)
        
        sheet_w = GRID_COLS * (THUMB_SIZE + PADDING) + PADDING
        sheet_h = num_rows * (THUMB_SIZE + PADDING) + PADDING
        
        sheet = Image.new("RGB", (sheet_w, sheet_h), SHEET_BG)
        draw = ImageDraw.Draw(sheet)
        
        # Try to load a decent font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except (IOError, OSError):
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except (IOError, OSError):
                font = ImageFont.load_default()
        
        for i, thumb_path in enumerate(chunk):
            row = i // GRID_COLS
            col = i % GRID_COLS
            
            x = PADDING + col * (THUMB_SIZE + PADDING)
            y = PADDING + row * (THUMB_SIZE + PADDING)
            
            try:
                img = Image.open(thumb_path)
                # Resize to square, maintaining aspect ratio with padding
                img.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
                # Center the image in the THUMB_SIZE x THUMB_SIZE cell
                offset_x = x + (THUMB_SIZE - img.width) // 2
                offset_y = y + (THUMB_SIZE - img.height) // 2
                sheet.paste(img, (offset_x, offset_y))
            except Exception as e:
                safe_print(f"      [!] Failed to paste thumbnail {i}: {e}")
                # Draw a grey placeholder
                draw.rectangle([x, y, x + THUMB_SIZE, y + THUMB_SIZE], fill=(60, 60, 60))
            
            # Draw numbered badge in top-left corner
            badge_x = x + 8
            badge_y = y + 8
            idx = start_index + chunk_start + i
            
            # Red circle
            draw.ellipse(
                [badge_x - BADGE_RADIUS, badge_y - BADGE_RADIUS,
                 badge_x + BADGE_RADIUS, badge_y + BADGE_RADIUS],
                fill=BADGE_COLOR
            )
            # White number
            text = str(idx)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text(
                (badge_x - tw // 2, badge_y - th // 2 - 1),
                text, fill=BADGE_TEXT, font=font
            )
        
        # Save sheet
        sheet_path = os.path.join(
            INPUT_SOURCING_DIR,
            f"contact_sheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{chunk_start}.jpg"
        )
        sheet.save(sheet_path, "JPEG", quality=75)
        sheets.append(sheet_path)
        safe_print(f"   [SHEET] Created contact sheet: {os.path.basename(sheet_path)} ({len(chunk)} images)")
    
    return sheets


class VLMSourcer:
    """
    Autonomous Vision-AI Scraper v3 — Contact Sheet Mode
    - Playwright-Stealth bypasses Cloudflare
    - Downloads THUMBNAILS only (fast, lightweight)
    - Creates numbered contact sheet grids for Discord review
    - Saves URL mapping so user can pick images by number
    - HQ download + VLM evaluation happens ONLY on user-selected images
    """
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.context = None
        self.session = None

    async def start(self):
        try:
            from playwright.async_api import async_playwright
            from playwright_stealth import Stealth

            self.pw = await async_playwright().start()
            self.context = await self.pw.chromium.launch_persistent_context(
                user_data_dir=os.path.abspath("playwright_profile_sourcing"),
                headless=self.headless,
                viewport={"width": 1920, "height": 1080},
                args=["--disable-blink-features=AutomationControlled"]
            )

            await Stealth().apply_stealth_async(self.context)
            print("[+] VLM Sourcer v3 Initialized (Contact Sheet Mode)")
        except ImportError:
            print("[!] FATAL: playwright-stealth not installed. Run: pip install playwright-stealth")
            raise

        self.session = httpx.AsyncClient(timeout=30.0)
        self.scraped_urls = get_scraped_album_urls()

    def slugify(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        return re.sub(r'[\s_]+', '-', text)

    async def discover_categories(self, base_url: str) -> Dict[str, str]:
        """
        Dynamically discover categories for a seller by visiting base_url + "/categories".
        Returns a dictionary mapping category names/slugs to their full category page URLs.
        """
        if not base_url.startswith("http"):
            base_url = "https://" + base_url
        categories_url = base_url.rstrip("/") + "/categories"
        safe_print(f"[*] Discovering categories dynamically from: {categories_url}")
        
        page = await self.context.new_page()
        categories = {}
        try:
            try:
                await page.goto(categories_url, wait_until="commit", timeout=20000)
                await page.wait_for_selector("a[href*='/categories/'], a[href*='/category/'], .category__link", timeout=12000)
            except Exception as e:
                safe_print(f"      [!] Timeout or selector mismatch on categories page: {e}. Attempting raw links extraction...")

            # Scroll down to ensure links are loaded
            await page.evaluate("window.scrollTo(0, 500)")
            await asyncio.sleep(0.5)

            # Query all anchor tags
            links = await page.query_selector_all("a")
            for link in links:
                href = await link.get_attribute("href")
                text = (await link.inner_text() or "").strip()
                
                if href and ("/categories/" in href or "/category/" in href):
                    if href.startswith("/"):
                        full_url = base_url.rstrip("/") + href
                    else:
                        full_url = href
                    
                    clean_name = self.slugify(text) if text else href.split("/")[-1]
                    if not clean_name:
                        clean_name = "category_" + href.split("/")[-1]
                        
                    if full_url not in categories.values() and clean_name:
                        orig_name = clean_name
                        counter = 1
                        while clean_name in categories:
                            clean_name = f"{orig_name}_{counter}"
                            counter += 1
                        categories[clean_name] = full_url

            if categories:
                safe_print(f"      [DISCOVERED] Found {len(categories)} categories: {list(categories.keys())}")
            else:
                safe_print("      [!] No categories discovered via /categories. Falling back to default albums endpoint.")
                categories["latest"] = base_url.rstrip("/") + "/albums"
                
        except Exception as e:
            safe_print(f"      [!] Error during category discovery: {e}")
            categories["latest"] = base_url.rstrip("/") + "/albums"
        finally:
            await page.close()
            
        return categories


    async def download_thumbnail(self, img_url: str, save_path: str, referer: str) -> bool:
        """
        Download a THUMBNAIL image (small/medium) — fast and lightweight.
        Yupoo thumbnails are typically 20-80KB each.
        We intentionally keep the /small/ or /medium/ URL to stay fast.
        """
        # Ensure URL has protocol
        url = img_url
        if not url.startswith('http'):
            url = "https:" + url if url.startswith('//') else url

        try:
            resp = await self.session.get(
                url,
                headers={
                    "Referer": referer,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                return True
        except Exception as e:
            safe_print(f"      [!] Thumbnail download error: {e}")

        return False

    async def scrape_single_album(self, album_url: str, category_id: str, title: str = "Unknown Product") -> bool:
        """
        Scrape a single Yupoo album page:
        1. Download thumbnails (concurrent, fast)
        2. Create numbered contact sheet
        3. Send to Discord for review
        4. Save mapping JSON so user can pick by number
        5. Record album URL in persistent history
        """
        normalized_url = _normalize_url(album_url)
        if normalized_url in self.scraped_urls:
            return False

        # Ensure uid=1 is present to prevent 404/not found routing on some subdomains
        if "uid=" not in album_url:
            separator = "&" if "?" in album_url else "?"
            album_url = f"{album_url}{separator}uid=1"

        album_page = await self.context.new_page()
        try:
            try:
                await album_page.goto(album_url, wait_until="commit", timeout=20000)
            except Exception as e:
                safe_print(f"      [!] Failed to navigate to album page: {e}")
                return False

            try:
                await album_page.wait_for_selector(".showalbum__children img, img", timeout=15000)
            except Exception as e:
                safe_print(f"      [!] Timeout waiting for album images to load: {e}")

            # Check if yupoo frozen screen is displayed inside album
            try:
                album_title = await album_page.title()
                album_body = await album_page.evaluate("document.body.innerText")
                if "暂停访问" in album_title or "temporarily unavailable" in album_body:
                    print(f"      [!] Album page is frozen/suspended. Skipping album.")
                    return False
            except Exception as e:
                safe_print(f"      [!] Error checking page frozen status: {e}")
                return False

            # Scroll to trigger lazy loading of images
            for _ in range(5):
                await album_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.8)

            # ─── TRY TO EXTRACT PROPER TITLE FROM ALBUM PAGE ───
            if title == "Unknown Product":
                try:
                    page_title = await album_page.evaluate("""
                        () => {
                            const h = document.querySelector('.showalbum__title, .album-title, h1, .text_overflow');
                            if (h && h.innerText.trim().length > 2) return h.innerText.trim();
                            const t = document.title;
                            if (t && !t.includes('yupoo') && t.length > 3) return t.split(' - ')[0].trim();
                            return '';
                        }
                    """)
                    if page_title and len(page_title) > 2:
                        title = page_title[:80]
                        safe_print(f"      [TITLE] Extracted: {title}")
                except:
                    pass

            # ─── EXTRACT STRUCTURED METADATA ───
            try:
                album_text = await album_page.evaluate("document.body.innerText")
            except:
                album_text = ""

            parsed_info = parse_album_text(album_text)

            # ─── EXTRACT ALL IMAGE URLs ───
            img_urls = await album_page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('.showalbum__children img, .showalbum__wrap img, .image__imagewrap img, img[data-src*="photo.yupoo.com"], img[src*="photo.yupoo.com"]');
                    return Array.from(imgs).map(img => {
                        return {
                            thumb: img.getAttribute('data-src')
                                || img.getAttribute('src')
                                || '',
                            hq: img.getAttribute('data-origin-src')
                                || img.getAttribute('data-src')
                                || img.getAttribute('src')
                                || ''
                        };
                    }).filter(item => item.thumb && item.thumb.length > 10);
                }
            """)

            total_images = len(img_urls)
            safe_print(f"      Found {total_images} images in album. Downloading thumbnails...")

            if total_images == 0:
                return False

            # ─── PHASE 1: DOWNLOAD THUMBNAILS CONCURRENTLY ───
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            uid = uuid.uuid4().hex[:4]
            temp_dir = os.path.join(INPUT_SOURCING_DIR, f"_thumbs_{ts}_{uid}")
            os.makedirs(temp_dir, exist_ok=True)

            # Build download tasks
            thumb_tasks = []
            for i, img_data in enumerate(img_urls):
                thumb_url = img_data["thumb"]
                ext = thumb_url.split('.')[-1].split('?')[0].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                    ext = 'jpg'
                save_path = os.path.join(temp_dir, f"thumb_{i+1:03d}.{ext}")
                thumb_tasks.append(self.download_thumbnail(thumb_url, save_path, album_url))

            # Download all thumbnails concurrently (very fast)
            results = await asyncio.gather(*thumb_tasks, return_exceptions=True)
            
            # Collect successful downloads
            thumb_paths = []
            for i, result in enumerate(results):
                ext = img_urls[i]["thumb"].split('.')[-1].split('?')[0].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                    ext = 'jpg'
                path = os.path.join(temp_dir, f"thumb_{i+1:03d}.{ext}")
                if result is True and os.path.exists(path):
                    thumb_paths.append(path)

            downloaded = len(thumb_paths)
            safe_print(f"      Downloaded {downloaded}/{total_images} thumbnails")

            if downloaded == 0:
                safe_print(f"   [!] No thumbnails downloaded. Skipping album.")
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
                return False

            # ─── CREATE CONTACT SHEETS ───
            contact_sheets = create_contact_sheets(thumb_paths)
            safe_print(f"      Created {len(contact_sheets)} contact sheet(s)")

            # ─── BUILD URL MAPPING (index -> HQ URL) ───
            url_mapping = {}
            for i, img_data in enumerate(img_urls):
                hq_url = img_data["hq"]
                # Convert to full-res URL
                hq_url = hq_url.replace('/small/', '/big/').replace('/medium/', '/big/')
                if not hq_url.startswith('http'):
                    hq_url = "https:" + hq_url if hq_url.startswith('//') else hq_url
                url_mapping[str(i + 1)] = hq_url

            # Build the purchase link
            purchase_link = ""
            if parsed_info["purchase_links"]:
                purchase_link = parsed_info["purchase_links"][0]

            # ─── SEND TO DISCORD + SAVE PENDING ───
            pending_data = {
                "product_name": title,
                "album_url": album_url,
                "referer": album_url,
                "category_id": category_id,
                "timestamp": ts,
                "total_images": total_images,
                "url_mapping": url_mapping,
                "metadata": {
                    "price_cny": parsed_info["price_cny"],
                    "link": purchase_link or album_url,
                    "whatsapp": parsed_info["whatsapp"],
                    "wechat": parsed_info["wechat"],
                    "discord_invite": parsed_info["discord_invite"],
                    "purchase_links": parsed_info["purchase_links"],
                    "description": album_text[:500] if album_text else ""
                }
            }

            discord_msg_id = await self.send_contact_sheet_to_discord(
                contact_sheets, pending_data
            )

            if discord_msg_id:
                # Save mapping to review_pending/{message_id}.json
                pending_path = os.path.join(REVIEW_PENDING_DIR, f"{discord_msg_id}.json")
                with open(pending_path, "w", encoding="utf-8") as f:
                    json.dump(pending_data, f, indent=2, ensure_ascii=False)
                safe_print(f"   [PENDING] Saved mapping: review_pending/{discord_msg_id}.json")
            else:
                # No Discord — save with a UUID fallback so it's not lost
                fallback_id = f"local_{uid}"
                pending_path = os.path.join(REVIEW_PENDING_DIR, f"{fallback_id}.json")
                with open(pending_path, "w", encoding="utf-8") as f:
                    json.dump(pending_data, f, indent=2, ensure_ascii=False)
                safe_print(f"   [LOCAL] No Discord. Saved mapping: review_pending/{fallback_id}.json")

            # ─── PERMANENTLY RECORD THIS ALBUM ───
            _save_to_persistent_history(album_url)
            self.scraped_urls.add(normalized_url)  # Update in-memory set too

            # Print summary
            safe_print(f"   [OK] {title} — {total_images} images → contact sheet sent to Discord")
            safe_print(f"        Price: ¥{parsed_info['price_cny']} | WhatsApp: {parsed_info['whatsapp'] or 'N/A'} | WeChat: {parsed_info['wechat'] or 'N/A'}")
            if parsed_info["purchase_links"]:
                safe_print(f"        Link: {parsed_info['purchase_links'][0]}")

            # ─── CLEANUP TEMP THUMBNAILS ───
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
            # Contact sheets are kept until Discord confirms receipt
            for cs in contact_sheets:
                try:
                    os.remove(cs)
                except:
                    pass

            return True

        finally:
            await album_page.close()

    async def scrape_category(self, url: str, category_id: str, max_items: int = 4):
        """
        Browse a Yupoo category WITH PAGINATION. For each album:
        Delegates single album processing to scrape_single_album.
        """
        print(f"\n[*] Contact Sheet Scraping: {url}")

        page = await self.context.new_page()
        try:
            # ─── PAGINATION LOOP ───
            MAX_PAGES = 10  # Safety limit to avoid infinite loops
            current_page_num = 1
            processed_count = 0

            while current_page_num <= MAX_PAGES and processed_count < max_items:
                # Build paginated URL
                if current_page_num == 1:
                    page_url = url
                else:
                    separator = "&" if "?" in url else "?"
                    page_url = f"{url}{separator}page={current_page_num}"
                    safe_print(f"   [PAGE {current_page_num}] Navigating to: {page_url}")

                try:
                    await page.goto(page_url, wait_until="commit", timeout=20000)
                    await page.wait_for_selector(".album__main, .album3__main, .album__name, a[href*='/albums/']", timeout=3000)
                except Exception as e:
                    safe_print(f"   [PAGE {current_page_num}] Warning/Timeout waiting for page content: {e}")

                # Check if yupoo frozen screen is displayed
                title = await page.title()
                body_text = await page.evaluate("document.body.innerText")
                if "暂停访问" in title or "temporarily unavailable" in body_text:
                    print(f"   [!] Seller subdomain is suspended/frozen. Skipping: {url}")
                    return

                # Extract album links (support both Layout 1/2, Layout 3, and generic item variations)
                album_els = await page.query_selector_all(".album__main, .album3__main, .album-item, a[href*='/albums/']")

                if not album_els:
                    safe_print(f"   [PAGE {current_page_num}] No albums found — end of seller's catalog.")
                    break

                safe_print(f"   [PAGE {current_page_num}] Found {len(album_els)} albums on this page")

                skipped_on_this_page = 0
                found_new_on_this_page = False

                for album_el in album_els:
                    if processed_count >= max_items:
                        break

                    # Try multiple selectors for album title
                    title = "Unknown Product"
                    # First check if the album element itself has a title attribute (common in Layout 3)
                    t_self = await album_el.get_attribute("title")
                    if t_self and t_self.strip() and len(t_self.strip()) > 2:
                        title = t_self.strip()
                    else:
                        for sel in [".album__name", ".album__title", "a[title]"]:
                            title_el = await album_el.query_selector(sel)
                            if title_el:
                                t = await title_el.get_attribute("title") if sel == "a[title]" else await title_el.inner_text()
                                if t and t.strip() and len(t.strip()) > 2:
                                    title = t.strip()
                                    break
                    href = await album_el.get_attribute("href")
                    if not href:
                        # Fallback: search for anchor tag inside
                        inner_a = await album_el.query_selector("a")
                        if inner_a:
                            href = await inner_a.get_attribute("href")


                    # Reconstruct absolute URL if relative
                    if href and href.startswith("/"):
                        base = url.split("/categories")[0].split("/albums")[0]
                        album_url = base + href
                    else:
                        album_url = href or url

                    # Deduplication check (normalized URL comparison)
                    normalized_url = _normalize_url(album_url)
                    if normalized_url in self.scraped_urls:
                        skipped_on_this_page += 1
                        continue

                    found_new_on_this_page = True
                    safe_print(f"   -> Album: {title}")

                    # Delegate single album processing
                    success = await self.scrape_single_album(album_url, category_id, title)
                    if success:
                        processed_count += 1

                # ─── PAGINATION DECISION ───
                if skipped_on_this_page > 0:
                    safe_print(f"   [PAGE {current_page_num}] Skipped {skipped_on_this_page} already-scraped albums")

                if processed_count >= max_items:
                    safe_print(f"   [DONE] Reached max_items limit ({max_items}). Moving to next category.")
                    break

                if not found_new_on_this_page:
                    # Everything on this page was a dupe — go to next page!
                    safe_print(f"   [PAGE {current_page_num}] All albums on this page already scraped → advancing to page {current_page_num + 1}")
                    current_page_num += 1
                    await asyncio.sleep(1)  # Be nice to Yupoo servers
                else:
                    # Found new items on this page — if we haven't hit max_items, try next page too
                    if processed_count < max_items:
                        current_page_num += 1
                        await asyncio.sleep(1)
                    else:
                        break

        finally:
            await page.close()

    async def send_contact_sheet_to_discord(
        self, sheet_paths: List[str], pending_data: dict
    ) -> Optional[str]:
        """
        Upload contact sheet image(s) to Discord with product info.
        Returns the Discord message_id so we can save the mapping.
        """
        try:
            import aiohttp
        except ImportError:
            print("      [DISCORD] aiohttp not installed. Skipping.")
            return None

        token = os.getenv("DISCORD_TOKEN", "")
        channel_id = DISCORD_REVIEW_CHANNEL
        if not token or not channel_id:
            print("      [DISCORD] No DISCORD_TOKEN or DISCORD_REVIEW_CHANNEL set. Skipping.")
            return None

        meta = pending_data.get("metadata", {})
        title = pending_data.get("product_name", "Unknown")
        album_url = pending_data.get("album_url", "")
        price = meta.get("price_cny", 0)
        link = meta.get("link", "")
        whatsapp = meta.get("whatsapp", "")
        wechat = meta.get("wechat", "")
        total = pending_data.get("total_images", 0)
        desc = meta.get("description", "")
        if desc:
            desc = desc.replace('\n', ' ')[:100] + "..."

        # Kakobuy Integration
        import urllib.parse
        kakobuy_url = ""
        if link and link != album_url:
            encoded = urllib.parse.quote(link, safe='')
            kakobuy_url = f"https://www.kakobuy.com/item/details?url={encoded}"
        elif album_url:
            encoded = urllib.parse.quote(album_url, safe='')
            kakobuy_url = f"https://www.kakobuy.com/item/details?url={encoded}"

        lines = [
            f"📸 **REVIEW: {title}** ({total} images)",
            f"💰 Price: ¥{price}" if price else "",
            f"📂 Yupoo: {album_url}" if album_url else "",
            f"🔗 Purchase: {link}" if link and link != album_url else "",
            f"🛒 **Kakobuy Checkout:** {kakobuy_url}" if kakobuy_url else "",
            f"📱 WhatsApp: `{whatsapp}`" if whatsapp else "",
            f"💬 WeChat: `{wechat}`" if wechat else "",
            f"📝 Details: {desc}" if desc else "",
            "",
            "**Reply with image numbers to download HQ versions:**",
            "```",
            "2, 5, 12          ← just numbers",
            "Hoodie | Black | ¥189 | 2, 5, 12   ← with metadata",
            "```",
        ]
        message_text = "\n".join(l for l in lines if l or l == "")

        try:
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            headers = {"Authorization": f"Bot {token}"}

            form = aiohttp.FormData()
            form.add_field("content", message_text)
            for i, sheet_path in enumerate(sheet_paths):
                if os.path.exists(sheet_path):
                    form.add_field(
                        f"files[{i}]",
                        open(sheet_path, "rb"),
                        filename=f"contact_sheet_{i+1}.jpg",
                        content_type="image/jpeg"
                    )

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=form) as resp:
                    if resp.status in [200, 201]:
                        data = await resp.json()
                        msg_id = data.get("id", "")
                        safe_print(f"      [DISCORD] ✅ Contact sheet sent! Message ID: {msg_id}")
                        # Add 📋 reaction to mark as pending review
                        react_url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg_id}/reactions/%F0%9F%93%8B/@me"
                        await session.put(react_url, headers=headers)
                        return msg_id
                    else:
                        text = await resp.text()
                        safe_print(f"      [DISCORD] ⚠️ Failed ({resp.status}): {text[:200]}")
        except Exception as e:
            safe_print(f"      [DISCORD] Error: {e}")

        return None

    async def close(self):
        if self.session:
            await self.session.aclose()
        if self.context:
            await self.context.close()
        if hasattr(self, 'pw') and self.pw:
            await self.pw.stop()


# ─── STANDALONE HQ DOWNLOAD UTILITY ───
# Called by discord_listener.py when user selects images

async def download_selected_hq_images(
    pending_data: dict,
    selected_indices: List[int],
    output_dir: str
) -> List[str]:
    """
    Download only the user-selected full-resolution images from Yupoo CDN.
    Returns list of downloaded file paths.
    """
    url_mapping = pending_data.get("url_mapping", {})
    referer = pending_data.get("referer", pending_data.get("album_url", ""))
    downloaded = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx in selected_indices:
            hq_url = url_mapping.get(str(idx))
            if not hq_url:
                safe_print(f"      [!] Index {idx} not found in mapping. Skipping.")
                continue

            ext = hq_url.split('.')[-1].split('?')[0].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = 'jpg'
            save_path = os.path.join(output_dir, f"img_{idx:03d}.{ext}")

            try:
                resp = await client.get(
                    hq_url,
                    headers={
                        "Referer": referer,
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                if resp.status_code == 200 and len(resp.content) > 5000:
                    with open(save_path, "wb") as f:
                        f.write(resp.content)
                    size_kb = len(resp.content) / 1024
                    safe_print(f"      [HQ] #{idx} → {size_kb:.0f}KB → {os.path.basename(save_path)}")
                    downloaded.append(save_path)
                else:
                    safe_print(f"      [!] HQ download #{idx} failed ({resp.status_code})")
            except Exception as e:
                safe_print(f"      [!] HQ download #{idx} error: {e}")

    return downloaded


async def evaluate_image_with_vlm(image_path: str, title: str) -> Tuple[str, int]:
    """
    Sends the image to NVIDIA NIM or Groq to categorize it.
    Returns: (category: 'product'|'size_chart'|'other', quality_score_out_of_10)
    """
    try:
        with Image.open(image_path) as img:
            img.thumbnail((1024, 1024))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            b64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"      [!] Image Processing Error: {e}")
        return "other", 0

    vlm_prompt = (
        f"Evaluate this image for '{title}'. Classify it into one category: "
        "'product' (flat lay, ghost mannequin, or hanger garment shot), "
        "'size_chart' (tables, measurements, sizing info), or "
        "'other' (models wearing clothes, humans, macro zoom details, logos, rubbish). "
        "Return JSON only: {\"category\": \"product\"|\"size_chart\"|\"other\", \"score\": 0-10, \"reason\": \"str\"}"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Primary: NVIDIA NIM Free Tier
        nvidia_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVAPI_KEY")
        if nvidia_key:
            try:
                payload = {
                    "model": "meta/llama-3.2-11b-vision-instruct",
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": vlm_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                    ]}],
                    "response_format": {"type": "json_object"}
                }

                resp = await client.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {nvidia_key}"},
                    json=payload
                )

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    matches = re.findall(r"\{.*?\}", content, re.DOTALL)
                    if matches:
                        result = json.loads(matches[0])
                        category = result.get("category", "other")
                        score = result.get("score", 0)
                        safe_print(f"      [VLM: NVIDIA] Category: {category} | Score: {score}/10 | {result.get('reason', '')}")
                        return category, score
                else:
                    safe_print(f"      [!] NVIDIA returned {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                safe_print(f"      [!] NVIDIA VLM Exception: {e}")

        # Secondary: Gemini Vision via LiteLLM Router (Multiplexed & Resilient)
        try:
            from litellm_router import shared_router
            messages = [{"role": "user", "content": [
                {"type": "text", "text": vlm_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
            ]}]
            resp = await shared_router.get_chat_completion(
                messages=messages,
                primary_model="gemini-lite",
                temperature=0.2,
                max_tokens=256,
                response_format={"type": "json_object"}
            )
            content = resp["choices"][0]["message"]["content"]
            matches = re.findall(r"\{.*?\}", content, re.DOTALL)
            if matches:
                result = json.loads(matches[0])
                category = result.get("category", "other")
                score = result.get("score", 0)
                safe_print(f"      [VLM: Gemini Router] Category: {category} | Score: {score}/10 | {result.get('reason', '')}")
                return category, score
        except Exception as e:
            safe_print(f"      [!] Gemini Router VLM Exception: {e}")

    # Fallback: keep as product so nothing is lost
    print("      [!] No VLM API responded. Defaulting to 'product'.")
    return "product", 10


def cleanup_old_reviews(max_age_days: int = 3):
    """Clean up review pending JSON files older than max_age_days.
    CRITICAL: Saves album URLs to persistent history BEFORE deleting files
    to prevent deduplication amnesia."""
    safe_print(f"[*] Cleaning up review pending files older than {max_age_days} days...")
    now = datetime.now()
    count = 0
    urls_to_preserve = []
    for filename in os.listdir(REVIEW_PENDING_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(REVIEW_PENDING_DIR, filename)
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                age = now - file_time
                if age.days >= max_age_days:
                    # CRITICAL FIX: Extract album URL BEFORE deleting the file
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            album_url = data.get("album_url")
                            if album_url:
                                urls_to_preserve.append(album_url)
                    except:
                        pass
                    os.remove(filepath)
                    count += 1
            except Exception as e:
                safe_print(f"  [!] Error cleaning up {filename}: {e}")
    # Save all extracted URLs to permanent history before they're lost forever
    if urls_to_preserve:
        _save_batch_to_persistent_history(urls_to_preserve)
        safe_print(f"  [PRESERVED] Saved {len(urls_to_preserve)} album URLs to permanent history before cleanup")
    if count > 0:
        safe_print(f"  [OK] Cleaned up {count} stale mapping files.")
    else:
        safe_print("  [OK] No stale mapping files found.")


async def main():
    safe_print("==================================================")
    safe_print("VLM SOURCING ENGINE v3 - CONTACT SHEET MODE")
    safe_print("==================================================")
    safe_print("Thumbnails -> Contact Sheet -> Discord -> You Pick -> HQ Download")
    safe_print("")
    
    # Check for test mode
    is_test_mode = "--test" in sys.argv or "--quick-test" in sys.argv
    if is_test_mode:
        safe_print("[TEST MODE] Running quick verification scrape...")

    # Optional command line arguments to target a specific seller/category
    selected_seller_id = None
    if "--seller" in sys.argv:
        try:
            idx = sys.argv.index("--seller")
            if idx + 1 < len(sys.argv):
                selected_seller_id = sys.argv[idx + 1]
        except ValueError:
            pass

    selected_category_id = None
    if "--category" in sys.argv:
        try:
            idx = sys.argv.index("--category")
            if idx + 1 < len(sys.argv):
                selected_category_id = sys.argv[idx + 1]
        except ValueError:
            pass

    # STEP 0: Backfill persistent history from existing data (prevents amnesia)
    _backfill_persistent_history()
    
    # Run cleanup of old reviews (now safe — saves URLs to permanent history first)
    cleanup_old_reviews(max_age_days=3)
    
    sourcer = VLMSourcer(headless=True)
    await sourcer.start()

    # ── STEP 1: Run Reddit Scout to discover new sellers & trending products ──
    reddit_sellers = []
    direct_album_urls = []
    if is_test_mode or selected_seller_id:
        safe_print("[TEST/DIRECT] Skipping Reddit Scout...")
    else:
        safe_print("\n[REDDIT SCOUT] Mining r/FashionReps, r/DesignerReps, r/RepLadies...")
        try:
            from reddit_seller_scout import run_reddit_scout, get_all_discovered_sellers, get_direct_album_urls
            reddit_results = await run_reddit_scout(max_sellers=50, min_relevance=0.3)
            safe_print(f"[REDDIT] New sellers found: {len(reddit_results['new_sellers'])}")
            safe_print(f"[REDDIT] Direct album URLs found: {len(reddit_results['direct_album_urls'])}")
            reddit_sellers = get_all_discovered_sellers()
            direct_album_urls = get_direct_album_urls()
        except Exception as e:
            safe_print(f"[REDDIT SCOUT] Warning: {e}. Continuing with hardcoded sellers.")

    # ── STEP 2: Process sellers (hardcoded + discovered) ──
    if selected_seller_id:
        matched_sellers = [s for s in SELLERS if s["id"] == selected_seller_id]
        if matched_sellers:
            target_sellers = matched_sellers
            safe_print(f"[ARG] Target seller selected: {selected_seller_id}")
        else:
            safe_print(f"[!] Warning: Seller '{selected_seller_id}' not found in list. Using custom subdomain configuration...")
            target_sellers = [{
                "id": selected_seller_id,
                "name": f"Custom Seller ({selected_seller_id})",
                "base_url": f"https://{selected_seller_id}.x.yupoo.com" if "." not in selected_seller_id else selected_seller_id,
                "categories": {
                    "latest": f"https://{selected_seller_id}.x.yupoo.com/albums" if "." not in selected_seller_id else selected_seller_id
                }
            }]
    else:
        target_sellers = SELLERS[:1] if is_test_mode else list(SELLERS)
        if not is_test_mode and reddit_sellers:
            # Process up to 15 newly discovered Reddit sellers
            target_sellers.extend(reddit_sellers[:15])
        
    safe_print(f"\n[SOURCER] Processing {len(target_sellers)} sellers...")
    for seller in target_sellers:
        print(f"\n[SELLER] {seller['name']}")
        
        # Determine categories to process
        hardcoded_cats = seller.get("categories", {})
        
        if selected_category_id:
            discovered_cats = await sourcer.discover_categories(seller["base_url"])
            # 1. Try to find in discovered categories first (slug match)
            matched_url = discovered_cats.get(selected_category_id)
            if matched_url:
                categories_to_process = [(selected_category_id, matched_url)]
            else:
                # 2. Try to find in hardcoded categories
                categories_to_process = [(k, v) for k, v in hardcoded_cats.items() if k == selected_category_id]
                
            if not categories_to_process:
                if selected_category_id.startswith("http"):
                    categories_to_process = [("custom", selected_category_id)]
                elif selected_category_id.isdigit():
                    categories_to_process = [("custom", f"{seller['base_url']}/categories/{selected_category_id}")]
                else:
                    # Look for close slug matches in discovered categories (e.g. "acne" matching "acne-studios")
                    best_match = None
                    for k, v in discovered_cats.items():
                        if selected_category_id.lower() in k.lower():
                            best_match = (k, v)
                            break
                    if best_match:
                        categories_to_process = [best_match]
                    else:
                        # Fallback
                        categories_to_process = [("custom", f"{seller['base_url']}/categories/{selected_category_id}")]
            safe_print(f"[ARG] Target category selected: {categories_to_process[0][0]} ({categories_to_process[0][1]})")
        else:
            if hardcoded_cats:
                categories_to_process = list(hardcoded_cats.items())
                safe_print(f"   [CURATED] Using {len(categories_to_process)} hardcoded categories for {seller['name']}")
            else:
                discovered_cats = await sourcer.discover_categories(seller["base_url"])
                if discovered_cats:
                    categories_to_process = list(discovered_cats.items())
                    safe_print(f"   [DYNAMIC] Discovered {len(categories_to_process)} categories dynamically for {seller['name']}")
                else:
                    categories_to_process = []
                    safe_print(f"   [!] No categories available for {seller['name']}")
                
            if is_test_mode and categories_to_process:
                categories_to_process = categories_to_process[:1]


            
        for cat_id, cat_url in categories_to_process:
            if is_test_mode:
                max_items = 1
            # Skip shoes if we have a lot of them already; prioritise clothing
            elif "shoes" in cat_id.lower() or "jordan" in cat_id.lower() or "dior_shoes" in cat_id.lower():
                max_items = 5  # 5 shoe items per run
            elif any(kw in cat_id.lower() for kw in ["hoodie", "tracksuit", "cargo", "bag"]):
                max_items = 15  # 15 items for priority categories
            else:
                max_items = 10  # Default
            try:
                await sourcer.scrape_category(cat_url, cat_id, max_items=max_items)
            except Exception as e:
                safe_print(f"      [!] Error scraping category {cat_id}: {e}")

    # ── STEP 3: Process direct trending album URLs from Reddit ──
    if not is_test_mode and not selected_seller_id and direct_album_urls:
        safe_print(f"\n[TRENDING PRODUCTS] Processing {len(direct_album_urls[:20])} direct album URLs...")
        for album_item in direct_album_urls[:20]:
            album_url = album_item if isinstance(album_item, str) else album_item.get("url")
            if not album_url:
                continue
            safe_print(f"\n[TRENDING ALBUM] Scrape target: {album_url}")
            try:
                await sourcer.scrape_single_album(album_url, "reddit_direct")
            except Exception as e:
                safe_print(f"      [!] Error scraping direct album: {e}")

    await sourcer.close()
    safe_print("\n[OK] Contact sheets sent to Discord! Reply with your picks to download HQ images.")


async def run_loop_mode(interval_hours: int):
    """
    Runs the scraper in a continuous loop, avoiding event loop recreation
    and using asyncio.sleep instead of blocking time.sleep.
    Optimization: Event loop starts once, sleep is non-blocking.
    """
    import random
    run_count = 0
    while True:
        run_count += 1
        safe_print(f"\n{'='*60}")
        safe_print(f"  SCRAPING SESSION #{run_count} — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        safe_print(f"{'='*60}")
        try:
            await main()
        except asyncio.CancelledError:
            safe_print("\n[LOOP] Cancelled.")
            break
        except Exception as e:
            safe_print(f"[LOOP] Session #{run_count} error: {e}")

        # ── STEP 4: Brand Website Sourcing Integration ──
        safe_print("\n[BRAND SOURCER] Running autonomous brand website scraping...")
        try:
            from auto_brand_sourcer import scrape_all_brands
            await scrape_all_brands(limit_per_brand=3)
        except Exception as e:
            safe_print(f"[BRAND SOURCER] Error during brand scraping: {e}")

        # Sleep with jitter to avoid predictable patterns
        sleep_secs = interval_hours * 3600 + random.randint(-300, 300)
        safe_print(f"\n[LOOP] Session #{run_count} complete. Sleeping {sleep_secs // 3600}h {(sleep_secs % 3600) // 60}m until next run...")
        try:
            await asyncio.sleep(sleep_secs)
        except asyncio.CancelledError:
            safe_print("\n[LOOP] Cancelled during sleep.")
            break

if __name__ == "__main__":
    import sys

    if "--loop" in sys.argv:
        # ── LOOP MODE: Run scraping sessions on a configurable interval ──
        # Usage: python vlm_product_sourcer.py --loop [--interval 4]
        interval_hours = 4  # Default: scrape every 4 hours
        if "--interval" in sys.argv:
            try:
                idx = sys.argv.index("--interval")
                interval_hours = int(sys.argv[idx + 1])
            except (IndexError, ValueError):
                pass
        safe_print(f"[LOOP] Starting continuous scraping mode. Interval: {interval_hours} hours.")
        safe_print(f"[LOOP] Press Ctrl+C to stop.\n")

        try:
            asyncio.run(run_loop_mode(interval_hours))
        except KeyboardInterrupt:
            safe_print("\n[LOOP] Stopped by user globally.")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            safe_print("\nStopped by user.")
