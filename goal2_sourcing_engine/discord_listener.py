"""
DISCORD PRODUCT DROP LISTENER v3
===================================
Receives product images + purchase links from your phone via Discord.
Supports:
  1. MANUAL DROPS: Send images + link from phone
  2. CONTACT SHEET REPLIES: Reply to a scraper contact sheet with picks
  3. MULTI-COLOUR VARIANTS: Same product in multiple colours
  4. SETS: Matching top+bottom sets with multiple pieces

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 HOW TO SEND A SINGLE PRODUCT DROP:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [attach images] Product Name | Color | ¥price | link

  SIMPLE:    [images] https://weidian.com/...
  WITH NAME: [images] Essentials Hoodie | https://weidian.com/...
  FULL:      [images] Essentials Hoodie | Black | ¥189 | https://weidian.com/...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 HOW TO SEND MULTIPLE COLOURS (same item):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Send EACH colour as a SEPARATE message.
  Reply to a contact sheet and specify colours:
    Hoodie | ¥189 | 2, 5   colours: black, white, grey

  Or for a contact sheet with colour variants already shown:
    Hoodie | Black | ¥189 | 1, 2, 3
    (then reply again for white version)
    Hoodie | White | ¥189 | 4, 5, 6

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👕👖 HOW TO SEND SETS (matching top + bottom):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Include the word "set" or "tracksuit" in the name:
    [images] Nike Tracksuit Set | Black | ¥350 | link
    [images] Co-ord Set | Cream | ¥280 | link

  For sets WITH multiple colours:
    Send each colour as separate message:
    [images] Cargo Set | Black | ¥320 | link
    [images] Cargo Set | Khaki | ¥320 | link

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📏 HOW TO INCLUDE SIZE CHARTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - Name the size chart image file "size.jpg" or "chart.jpg" before attaching
  - OR mention "size" in your message text
  - For contact sheet replies: add   size: 8   at the end
    e.g.  Hoodie | Black | ¥189 | 2, 5, 12   size: 12
  - The bot will auto-read the chart and extract size information

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 HOW TO REPLY TO A CONTACT SHEET:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Reply DIRECTLY to the bot's contact sheet message with:
    2, 5, 12                              ← just pick by number
    Hoodie | Black | ¥189 | 2, 5, 12     ← override name/color/price
    Hoodie | ¥189 | 2, 5   size: 8       ← with size chart
    all                                   ← select all images

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 FULL WAREHOUSE — SEND ALL IN ONE GO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Just send all your products one by one from your phone.
  Each message = one product (or one colour variant).
  The bot saves everything — the AI generates ads overnight.
"""

import os
import re
import json
import uuid
import asyncio
import httpx
import discord
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from inventory_manager import update_inventory
from size_chart_reader import extract_size_info
try:
    from style_tagger import tag_product as auto_tag
except ImportError:
    auto_tag = None

from utils import safe_print, detect_category

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

BASE_DIR = Path(__file__).parent
MANUAL_CURATION_DIR = BASE_DIR / "MANUAL_CURATION"
MANUAL_CURATION_DIR.mkdir(exist_ok=True)
REVIEW_PENDING_DIR = BASE_DIR / "review_pending"
REVIEW_PENDING_DIR.mkdir(exist_ok=True)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SCRAPE_HISTORY_FILE = DATA_DIR / "scraped_history.json"
SELLERS_FILE = DATA_DIR / "yupoo_sellers.json"


def load_scrape_history() -> dict:
    """Load the permanent scrape history from disk."""
    if SCRAPE_HISTORY_FILE.exists():
        try:
            data = json.loads(SCRAPE_HISTORY_FILE.read_text(encoding="utf-8"))
            return data.get("items", {})
        except Exception:
            pass
    return {}


def save_scrape_history(items: dict):
    """Save the permanent scrape history to disk."""
    data = {"version": 1, "items": items}
    SCRAPE_HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def record_import(item_id: str = None, album_url: str = None, product_name: str = "",
                  seller: str = "", platform: str = "", source: str = "discord"):
    """Record a product import to permanent history. Called after successful import."""
    history = load_scrape_history()
    
    # Generate dedup key
    if item_id and platform:
        key = f"{platform}_{item_id}"
    elif album_url:
        m = re.search(r'([\w-]+)\.x\.yupoo\.com(/albums/\d+)', album_url or "")
        if m:
            key = f"yupoo_{m.group(1)}_{m.group(2)}"
        else:
            key = f"url_{hash(album_url)}"
    else:
        return  # Nothing to track
    
    history[key] = {
        "item_id": item_id or "",
        "platform": platform,
        "album_url": album_url or "",
        "product_name": product_name,
        "seller": seller,
        "imported_at": datetime.now().isoformat(),
        "source": source,
    }
    save_scrape_history(history)


def is_imported(item_id: str = None, album_url: str = None, platform: str = "",
                _cache: dict = None) -> tuple:
    """Check if a product was already imported. Returns (is_dupe, entry_or_None).
    Pass _cache=history_dict to avoid re-reading the JSON file on every call."""
    history = _cache if _cache is not None else load_scrape_history()
    
    # Check by item_id
    if item_id and platform:
        key = f"{platform}_{item_id}"
        if key in history:
            return True, history[key]
    
    # Check by album URL
    if album_url:
        m = re.search(r'([\w-]+)\.x\.yupoo\.com(/albums/\d+)', album_url)
        if m:
            key = f"yupoo_{m.group(1)}_{m.group(2)}"
            if key in history:
                return True, history[key]
        # Also check all entries for matching album_url
        for entry in history.values():
            if entry.get("album_url") == album_url:
                return True, entry
    
    return False, None


def load_sellers_db() -> dict:
    """Load the Yupoo sellers database."""
    if SELLERS_FILE.exists():
        try:
            return json.loads(SELLERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_sellers_db(db: dict):
    """Save the Yupoo sellers database."""
    SELLERS_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


# Known link patterns
LINK_PATTERN = re.compile(
    r'(https?://(?:[a-zA-Z0-9-]+\.)*(?:taobao\.com|weidian\.com|1688\.com|k\.youshop10\.com|detail\.tmall\.com)[^\s<>"\']+)',
    re.IGNORECASE
)

# Common color names for auto-detection
COLOR_NAMES = [
    "black", "white", "red", "blue", "green", "grey", "gray", "navy",
    "beige", "cream", "brown", "khaki", "pink", "purple", "orange",
    "yellow", "olive", "burgundy", "maroon", "tan", "camel", "ivory",
    "charcoal", "teal", "coral", "mint", "lavender", "wine", "sand",
    "mocha", "coffee", "apricot",
]

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


# ══════════════════════════════════════════════════════════════════
# 🧠 BOT BRAIN — Gemini-powered natural language understanding
# ══════════════════════════════════════════════════════════════════

GEMINI_KEYS = [k for k in [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
    os.getenv("GEMINI_API_KEY_6"),
    os.getenv("GEMINI_API_KEY_7"),
] if k]
_gemini_key_idx = 0

BOT_BRAIN_SYSTEM = """You are a sharp, friendly Discord assistant for OBSCURA — a premium fashion sourcing and reselling business.
You help the owner source products, manage their blanks/brands catalog, and understand casual messages.

You know everything about the OBSCURA system capabilities and can explain them:
1. MARKETPLACE IMPORTS: If the user drops any 1688, Taobao, or Weidian link, you trigger a background scraper to import images, prices, and names.
2. CONTACT SHEET PICKS: User replies to contact sheets with image numbers (e.g., "2, 5, 12"). They can override details ("Hoodie | Black | ¥189 | 2, 5, 12"), pick all ("all"), or trigger multi-colour runs ("Hoodie | ¥189 | 2, 5   colours: black, white").
3. SIZE CHART READER: If they name a photo "size.jpg"/"chart.jpg", type "size" in message, or add "size: 8" (specifies image index 8 as size chart) to a reply, you auto-extract sizing info.
4. OUT-OF-THE-BOX STYLE TAGGING: staged products are auto-tagged with gender, niche (streetwear, minimalist), scene, and weight in the background.
5. AUTO-MATCHER & OUTFIT MERGES: Users can react with ✅ on top+bottom recommendations to merge pieces into a single set and copy assets.
6. VOICE NOTES (TTS): 
   - `!t [text]` / `!tts [text]` / `!g [text]` -> Google Gemini conversational voice.
   - `!v [text]` / `!voice [text]` / `!e [text]` -> Microsoft Jenny neural voice.
7. BRAND LISTING: `!sellers` / `!list` lists monitored Chinese wholesale/streetwear brands (Simple Project, Common Divisor, BJHG, etc.) and discovered Yupoo subdomains.
8. INTERACTIVE BROWSER: `!browse` / `!b` opens an interactive dropdown menu to browse Yupoo sellers by category, drill into sub-sections, and pick products. Duplicates are marked with ✅.
9. YUPOO DIRECT: `!yupoo [subdomain]` scrapes a specific seller's catalog. Already-imported items show ✅.
10. OUTFIT CURATION: `!outfit "product-1" + "product-2"` curates an outfit for on-model AI photo generation.
11. SPREADSHEET IMPORT: `!sheet [url]` imports products from a Google Sheet or CSV URL.

Always be BRIEF, smart, and use emojis. No long paragraphs. Act like a high-level streetwear co-founder, not a chatbot."""


async def call_gemini(prompt: str, system: str = BOT_BRAIN_SYSTEM) -> str:
    """Call Gemini/LLM via LiteLLM resilient router wrapper."""
    try:
        from litellm_router import shared_router
        response = await shared_router.get_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            primary_model="gemini-lite",
            system_instruction=system,
            temperature=0.4,
            max_tokens=400
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"      [LITELLM DISCORD ERROR] Chat completion failed: {e}")
        return ""


def get_warehouse_summary() -> str:
    """Summarise what's currently in MANUAL_CURATION for the bot brain context."""
    # ⚡ Bolt Optimization: Use os.scandir to avoid N+1 stat calls for mtime
    if MANUAL_CURATION_DIR.exists():
        with os.scandir(MANUAL_CURATION_DIR) as scanner:
            entries = [entry for entry in scanner if entry.is_dir()]
            folders = [Path(entry.path) for entry in sorted(entries, key=lambda e: e.stat().st_mtime, reverse=True)]
    else:
        folders = []
    total = len(folders)
    recent = []
    for folder in folders[:8]:
        meta_file = folder / "metadata.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                name = meta.get("product_name", folder.name)
                color = meta.get("color", "")
                cat = meta.get("category", "")
                entry = f"{name}"
                if color and color not in ("default", ""):
                    entry += f" ({color})"
                if cat:
                    entry += f" [{cat}]"
                recent.append(entry)
            except Exception:
                recent.append(folder.name)
    lines = [f"Total products in warehouse: {total}"]
    if recent:
        lines.append("Recent additions: " + ", ".join(recent))
    return "\n".join(lines)


def get_sellers_summary() -> str:
    """Summarise monitored and discovered brands."""
    try:
        from auto_scout_v2 import LEGIT_BRANDS
    except ImportError:
        LEGIT_BRANDS = {}
    
    lines = ["📋 **Monitored Chinese Brands:**"]
    for bid, brand in LEGIT_BRANDS.items():
        name = brand.get("name", bid)
        website = brand.get("website", brand.get("tmall_url", ""))
        vibe = brand.get("vibe", "")
        lines.append(f"• **{name}** (vibe: `{vibe}`)\n  🔗 URL: <{website}>")
        
    discovered_path = BASE_DIR / "data" / "reddit_discovered_sellers.json"
    if discovered_path.exists():
        try:
            with open(discovered_path, "r", encoding="utf-8") as f:
                disc = json.load(f)
                lines.append(f"\n🏷️ **Reddit Discovered Sellers ({len(disc)}):**")
                top_disc = list(disc.keys())[:10]
                lines.append("• " + ", ".join(top_disc))
        except Exception as e:
            print(f"[ERROR] Failed to load discovered sellers: {e}")
    return "\n".join(lines)


async def handle_brain_chat(message) -> None:
    """Route a plain text message to the Gemini brain for natural language handling."""
    text = message.content.strip()
    if not text or text.startswith("/"):
        return
    warehouse = get_warehouse_summary()
    prompt = f"""Current warehouse state:
{warehouse}

User message: "{text}"

Respond helpfully. If asking about products/warehouse, use the state above.
If it looks like they\'re trying to do something with the bot (e.g. scrape, pick images, add product), explain how.
Keep reply short."""
    async with message.channel.typing():
        reply = await call_gemini(prompt)
    if reply:
        await message.reply(reply)
    else:
        # Fallback when Gemini is unavailable
        await message.reply(
            "I'm OBSCURA bot! The AI Sourcing & Reselling Orchestration engine.\n\n"
            "I can process product drops and Chinese marketplace links!\n\n"
            "• Send a 1688, Taobao, or Weidian link → I'll scrape and import it\n"
            "• Send a photo with message → I'll stage it for AI lookbooks"
        )


def parse_message(text):
    """
    Parse the message text to extract: product_name, color, price, link, currency.
    """
    text = text.strip()
    
    # Extract the link
    link_match = LINK_PATTERN.search(text)
    link = link_match.group(1) if link_match else ""
    
    # Remove the link from the text to parse the rest
    remaining = LINK_PATTERN.sub("", text).strip()
    
    product_name = None
    color = None
    price = 0
    currency = "CNY"

    # Extract price — ONLY if explicitly marked with ¥, CNY, $, USD or in a pipe-separated field
    # This prevents "Air Force 1" or "Yeezy 350" from being misread as prices
    price_match = re.search(r'(?:¥|¥|CNY|\$|USD)\s*(\d+(?:\.\d+)?)', remaining)
    if price_match:
        price = price_match.group(1)
        if "." in price:
            price = float(price)
        else:
            price = int(price)
        matched_str = price_match.group(0)
        if "$" in matched_str or "USD" in matched_str:
            currency = "USD"
        remaining = remaining.replace(matched_str, "").strip()
    elif "|" in remaining:
        # Check if any pipe-separated part is a pure number (price field)
        parts_check = [p.strip() for p in remaining.split("|")]
        for i, part in enumerate(parts_check):
            if re.match(r'^\d+(?:\.\d+)?$', part):
                val = float(part) if "." in part else int(part)
                price = val
                parts_check.pop(i)
                remaining = "|".join(parts_check)
                if "$" in text:
                    currency = "USD"
                break
    else:
        # Check if there is a dollar sign with a number elsewhere
        usd_match = re.search(r'\$\s*(\d+(?:\.\d+)?)', text)
        if usd_match:
            price = float(usd_match.group(1)) if "." in usd_match.group(1) else int(usd_match.group(1))
            currency = "USD"
    
    if "|" in remaining:
        # Format: "Product Name | Color"
        parts = remaining.split("|", 1)
        product_name = parts[0].strip() or None
        color_part = parts[1].strip()
        if color_part:
            color = color_part
    elif remaining:
        # Check if the remaining text is just a color name
        if remaining.lower() in COLOR_NAMES:
            color = remaining
        else:
            # Could be "Color Link" or just a product name
            words = remaining.split()
            if len(words) == 1 and words[0].lower() in COLOR_NAMES:
                color = words[0]
            elif len(words) >= 1:
                # Check if the first word is a color
                if words[0].lower() in COLOR_NAMES:
                    color = words[0]
                    product_name = " ".join(words[1:]) if len(words) > 1 else None
                else:
                    product_name = remaining
    
    return product_name, color, price, link, currency


def parse_contact_sheet_reply(text: str) -> dict:
    """
    Parse a reply to a contact sheet message.
    
    Supports complex multi-color, tracksuit set, size chart, and detail picking:
      "1, 2 black"                                 -> black color, 1=front, 2=back
      "1, 2 top black | 3, 4 bottom black"         -> color/part splits
      "1, 2 pink | 3 size | 4 detail"              -> split pink, size chart, detail close-up
    
    Returns: {
        "groups": [
            {"indices": [1, 2], "color": "black", "part": "top", "is_size": False, "is_detail": False},
            ...
        ],
        "product_name": str or None,
        "price": int,
        "link": str or None,
        "select_all": False
    }
    """
    text = text.strip()
    result = {
        "groups": [],
        "product_name": None,
        "price": 0,
        "link": None,
        "select_all": False
    }
    
    # Check for "all" keyword
    if text.lower().strip() in ["all", "all images", "everything"]:
        result["select_all"] = True
        return result

    # 1. Parse global meta parameters (Product Name, Price, Link)
    cleaned_text = text
    
    # Extract link if present
    link_match = LINK_PATTERN.search(cleaned_text)
    if link_match:
        result["link"] = link_match.group(1)
        cleaned_text = LINK_PATTERN.sub("", cleaned_text).strip()
    
    # Extract price if present (e.g. ¥189 or 189)
    price_match = re.search(r'(?:¥|￥|CNY)\s*(\d+)', cleaned_text)
    if price_match:
        result["price"] = int(price_match.group(1))
        cleaned_text = cleaned_text.replace(price_match.group(0), "").strip()
    
    # Check if there is pipe separation for product name (e.g., "Hoodie | Black | 1, 2")
    parts = [p.strip() for p in cleaned_text.split("|") if p.strip()]
    
    # Extract product name if first part contains no numbers
    if parts and not re.search(r'\b\d+\b', parts[0]):
        result["product_name"] = parts[0]
        # Remove product name part from parts to parse
        parts = parts[1:]
        
    # Also check if the next part is color or price
    if parts and len(parts) > 1 and not re.search(r'\b\d+\b', parts[0]):
        # The user might have written color or category as the second part
        # E.g. "Hoodie | Black | 1, 2"
        global_color_match = [c for c in COLOR_NAMES if c == parts[0].lower().strip()]
        if global_color_match:
            # We skip this part as color will be parsed inline or default to this
            parts = parts[1:]
            
    # Now, parse remaining parts (they should contain the image selections)
    # If no pipes were used, the whole remaining text is parsed line-by-line
    selection_lines = []
    if len(parts) == 1:
        # User wrote it line-by-line: "1, 2 black\n3 size"
        selection_lines = [line.strip() for line in parts[0].split("\n") if line.strip()]
    else:
        # User wrote it pipe-separated: "1, 2 black | 3 size"
        for part in parts:
            selection_lines.extend([line.strip() for line in part.split("\n") if line.strip()])
            
    # Parse each selection line
    for line in selection_lines:
        # Extract indices (all numbers)
        indices = [int(n) for n in re.findall(r'\b\d+\b', line)]
        if not indices:
            continue
            
        # Clean indices from line to parse tags
        flags_text = re.sub(r'\b\d+\b', '', line).replace(',', ' ').replace('&', ' ').strip().lower()
        
        # Detect attributes
        color = None
        part = None  # top, bottom, set
        is_size = False
        is_detail = False
        
        # Color detection
        for c in COLOR_NAMES:
            if re.search(r'\b' + c + r'\b', flags_text):
                color = c
                break
                
        # Part detection
        if re.search(r'\b(top|upper|jacket|hoodie|tee|t-shirt|shirt|sweatshirt)\b', flags_text):
            part = "top"
        elif re.search(r'\b(bottom|pants|trousers|shorts|sweatpants|joggers)\b', flags_text):
            part = "bottom"
        elif re.search(r'\b(set|suit|tracksuit)\b', flags_text):
            part = "set"
            
        # Size chart detection
        if re.search(r'\b(size|chart|sizing|measuring|measurements|sz)\b', flags_text):
            is_size = True
            
        # Detail detection
        if re.search(r'\b(detail|close|zoom|tag|label|stitch|neck|collar|brand|det)\b', flags_text):
            is_detail = True
            
        result["groups"].append({
            "indices": indices,
            "color": color,
            "part": part,
            "is_size": is_size,
            "is_detail": is_detail
        })
        
    return result


from utils import slugify


# ════════════════════════════════════════════════════════════
# INTERACTIVE BROWSE UI (Discord Select Menus + Buttons)
# ════════════════════════════════════════════════════════════

class BrowseCategorySelect(discord.ui.Select):
    """Step 1: Pick a seller category (Blanks, Streetwear, etc.)."""

    def __init__(self, sellers_db: dict):
        self.sellers_db = sellers_db
        # Build options from seller categories
        category_labels = {
            "blanks": ("🧵 Blanks & Basics", "Premium heavyweight blanks, OEM tees, hoodies"),
            "replicas_streetwear": ("🔥 Streetwear", "Corteiz, Trapstar, Essentials, Nike Tech"),
            "replicas_designer": ("💎 Designer", "High-end designer fashion replicas"),
            "replicas_shoes": ("👟 Shoes", "Sneakers, dunks, Jordans"),
            "replicas_accessories": ("👜 Accessories", "Bags, watches, jewelry"),
        }
        options = []
        for key, sellers in sellers_db.items():
            if key == "spreadsheets" or not sellers:
                continue
            label, desc = category_labels.get(key, (key.replace("_", " ").title(), ""))
            options.append(discord.SelectOption(
                label=label, value=key,
                description=f"{len(sellers)} sellers — {desc}"[:100]
            ))
        if not options:
            options = [discord.SelectOption(label="No sellers configured", value="none")]
        super().__init__(placeholder="Pick a category...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        category_key = self.values[0]
        if category_key == "none":
            await interaction.response.send_message("⚠️ No sellers in `data/yupoo_sellers.json`.", ephemeral=True)
            return

        sellers = self.sellers_db.get(category_key, [])
        if not sellers:
            await interaction.response.send_message("⚠️ No sellers in this category.", ephemeral=True)
            return

        # Show seller picker
        view = discord.ui.View(timeout=180)
        view.add_item(BrowseSellerSelect(sellers, category_key))
        await interaction.response.send_message(
            f"**Step 2:** Pick a seller to browse:",
            view=view
        )


class BrowseSellerSelect(discord.ui.Select):
    """Step 2: Pick a specific seller from the category."""

    def __init__(self, sellers: list, category_key: str):
        self.sellers_list = sellers
        self.category_key = category_key
        options = []
        for i, s in enumerate(sellers[:25]):  # Discord max 25 options
            label = s.get("name", f"Seller {i+1}")
            desc = s.get("focus", "")[:100]
            options.append(discord.SelectOption(
                label=label, value=str(i),
                description=desc
            ))
        super().__init__(placeholder="Pick a seller...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        seller = self.sellers_list[idx]
        subdomain = seller.get("subdomain", "")
        seller_name = seller.get("name", subdomain)

        await interaction.response.defer(thinking=True)

        try:
            from yupoo_scraper import YupooScraper
            scraper = YupooScraper()

            # Check if seller has categories (sub-sections)
            categories = scraper.get_categories(subdomain)

            if categories and len(categories) > 1:
                # Seller has sub-sections — show category picker
                view = discord.ui.View(timeout=180)
                view.add_item(BrowseSectionSelect(subdomain, seller_name, categories, scraper))
                await interaction.followup.send(
                    f"📂 **{seller_name}** has **{len(categories)} sections**. Pick one:",
                    view=view
                )
            else:
                # Flat seller — scrape page 1 directly
                albums, has_more = scraper.scrape_album_list(subdomain, page=1)
                if not albums:
                    await interaction.followup.send(f"❌ No albums found for **{seller_name}**.")
                    return

                # Update seller last_scraped
                _update_seller_timestamp(subdomain, len(albums))

                # Show albums with dedup markers + pagination
                view = BrowseAlbumsView(
                    subdomain=subdomain, seller_name=seller_name,
                    albums=albums, page=1, has_more=has_more,
                    category_id=None, channel=interaction.channel,
                    message_ref=None
                )
                embed = view.build_embed()
                msg = await interaction.followup.send(embed=embed, view=view)
                view.message_ref = msg
                await view.save_pending(str(msg.id))

        except Exception as e:
            await interaction.followup.send(f"⚠️ Error scraping **{seller_name}**: `{e}`")


class BrowseSectionSelect(discord.ui.Select):
    """Step 2.5: Pick a sub-section (category) within a seller."""

    def __init__(self, subdomain: str, seller_name: str, categories: list, scraper):
        self.subdomain = subdomain
        self.seller_name = seller_name
        self.categories = categories
        self.scraper = scraper

        options = [discord.SelectOption(
            label="📦 All Albums", value="all",
            description="Browse everything (no filter)"
        )]
        for cat in categories[:24]:  # Leave room for "All" option
            options.append(discord.SelectOption(
                label=cat["name"][:100], value=cat["id"],
                description=f"Section ID: {cat['id']}"
            ))
        super().__init__(placeholder="Pick a section...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        section_id = self.values[0]
        cat_id = None if section_id == "all" else section_id
        section_name = "All Albums"
        if cat_id:
            for c in self.categories:
                if c["id"] == cat_id:
                    section_name = c["name"]
                    break

        await interaction.response.defer(thinking=True)

        try:
            albums, has_more = self.scraper.scrape_album_list(
                self.subdomain, page=1, category_id=cat_id
            )
            if not albums:
                await interaction.followup.send(
                    f"❌ No albums in **{self.seller_name}** → {section_name}."
                )
                return

            _update_seller_timestamp(self.subdomain, len(albums))

            view = BrowseAlbumsView(
                subdomain=self.subdomain,
                seller_name=f"{self.seller_name} → {section_name}",
                albums=albums, page=1, has_more=has_more,
                category_id=cat_id, channel=interaction.channel,
                message_ref=None
            )
            embed = view.build_embed()
            msg = await interaction.followup.send(embed=embed, view=view)
            view.message_ref = msg
            await view.save_pending(str(msg.id))

        except Exception as e:
            await interaction.followup.send(f"⚠️ Error: `{e}`")


class BrowseAlbumsView(discord.ui.View):
    """Paginated album list with dedup markers and Next/Prev buttons."""

    def __init__(self, subdomain, seller_name, albums, page, has_more,
                 category_id, channel, message_ref):
        super().__init__(timeout=300)
        self.subdomain = subdomain
        self.seller_name = seller_name
        self.albums = albums
        self.page = page
        self.has_more = has_more
        self.category_id = category_id
        self.channel = channel
        self.message_ref = message_ref

        # Add pagination buttons
        if page > 1:
            self.add_item(BrowsePrevButton(self))
        if has_more:
            self.add_item(BrowseNextButton(self))

    def build_embed(self) -> discord.Embed:
        """Build the album list embed with dedup markers."""
        embed = discord.Embed(
            title=f"📦 {self.seller_name} (Page {self.page})",
            description="Reply to this message with numbers to import (e.g. `1, 3, 5`)\nAlready-imported items marked with ✅",
            color=0x3498db
        )

        # Load history once for batch dedup check (avoids 25 JSON reads)
        _history_cache = load_scrape_history()
        
        for i, album in enumerate(self.albums[:25], start=1):
            # Check if already imported
            dupe, dupe_entry = is_imported(album_url=album.get("album_url"), _cache=_history_cache)
            dupe_mark = "✅ " if dupe else ""

            price_str = f"¥{album['price_cny']}" if album.get("price_cny") else "No price"
            title = album.get("title", f"Album {i}")[:50]

            value = f"Price: **{price_str}**"
            if album.get("weidian_link"):
                value += " | 🔗 Has Weidian link"
            if dupe and dupe_entry:
                value += f"\n*Imported: {dupe_entry.get('imported_at', '?')[:10]}*"

            embed.add_field(
                name=f"[{i}] {dupe_mark}{title}",
                value=value,
                inline=False
            )

        if len(self.albums) > 25:
            embed.set_footer(text=f"Showing 25 of {len(self.albums)} albums on this page. Use Next to see more.")
        else:
            page_note = " | More pages available →" if self.has_more else ""
            embed.set_footer(text=f"{len(self.albums)} albums{page_note}")

        return embed

    async def save_pending(self, message_id):
        """Save album data to review_pending for reply handling."""
        pending_file = REVIEW_PENDING_DIR / f"{message_id}.json"
        pending_data = {
            "type": "yupoo_catalog",
            "subdomain": self.subdomain,
            "seller_name": self.seller_name,
            "albums": self.albums,
            "category_id": self.category_id,
            "page": self.page,
            "timestamp": datetime.now().isoformat()
        }
        with open(pending_file, "w", encoding="utf-8") as f:
            json.dump(pending_data, f, ensure_ascii=False, indent=2)


class BrowsePrevButton(discord.ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="◀ Prev Page", style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            from yupoo_scraper import YupooScraper
            scraper = YupooScraper()
            new_page = self.parent_view.page - 1
            albums, has_more = scraper.scrape_album_list(
                self.parent_view.subdomain, page=new_page,
                category_id=self.parent_view.category_id
            )
            new_view = BrowseAlbumsView(
                subdomain=self.parent_view.subdomain,
                seller_name=self.parent_view.seller_name,
                albums=albums, page=new_page, has_more=has_more,
                category_id=self.parent_view.category_id,
                channel=self.parent_view.channel,
                message_ref=None
            )
            embed = new_view.build_embed()
            msg = await interaction.followup.send(embed=embed, view=new_view)
            new_view.message_ref = msg
            # Save pending for reply handling
            await new_view.save_pending(str(msg.id))
        except Exception as e:
            await interaction.followup.send(f"⚠️ Error: `{e}`")


class BrowseNextButton(discord.ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="Next Page ▶", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            from yupoo_scraper import YupooScraper
            scraper = YupooScraper()
            new_page = self.parent_view.page + 1
            albums, has_more = scraper.scrape_album_list(
                self.parent_view.subdomain, page=new_page,
                category_id=self.parent_view.category_id
            )
            new_view = BrowseAlbumsView(
                subdomain=self.parent_view.subdomain,
                seller_name=self.parent_view.seller_name,
                albums=albums, page=new_page, has_more=has_more,
                category_id=self.parent_view.category_id,
                channel=self.parent_view.channel,
                message_ref=None
            )
            embed = new_view.build_embed()
            msg = await interaction.followup.send(embed=embed, view=new_view)
            new_view.message_ref = msg
            await new_view.save_pending(str(msg.id))
        except Exception as e:
            await interaction.followup.send(f"⚠️ Error: `{e}`")


def _update_seller_timestamp(subdomain: str, album_count: int):
    """Update last_scraped timestamp and album_count in sellers DB."""
    try:
        db = load_sellers_db()
        for category_sellers in db.values():
            if isinstance(category_sellers, list):
                for seller in category_sellers:
                    if seller.get("subdomain") == subdomain:
                        seller["last_scraped"] = datetime.now().isoformat()
                        seller["album_count"] = album_count
                        save_sellers_db(db)
                        return
    except Exception:
        pass


@client.event
async def on_ready():
    safe_print(f"==================================================")
    safe_print(f"[*] Discord Listener v3 Online as {client.user}")
    safe_print(f"[*] Ready to receive product drops + contact sheet replies.")
    safe_print(f"==================================================")
    safe_print(f"")
    safe_print(f"📦 SINGLE PRODUCT:")
    safe_print(f"  [images] Product Name | Color | ¥price | link")
    safe_print(f"  e.g.  Bape Hoodie | Black | ¥189 | https://weidian.com/...")
    safe_print(f"")
    safe_print(f"🎨 MULTIPLE COLOURS (same item):")
    safe_print(f"  Send each colour as a SEPARATE message")
    safe_print(f"  OR in a contact sheet reply:")
    safe_print(f"    Hoodie | ¥189 | 2, 5   colours: black, white, grey")
    safe_print(f"")
    safe_print(f"👕👖 SETS (matching top + bottom):")
    safe_print(f"  Include 'set' or 'tracksuit' in the name:")
    safe_print(f"    [images] Cargo Set | Black | ¥320 | link")
    safe_print(f"")
    safe_print(f"📏 SIZE CHART:")
    safe_print(f"  - Name file 'size.jpg' before attaching")
    safe_print(f"  - OR mention 'size' in message text")
    safe_print(f"  - In contact sheet reply: add   size: 8   at the end")
    safe_print(f"")
    safe_print(f"📋 CONTACT SHEET REPLY:")
    safe_print(f"  Reply to bot's contact sheet with: 2, 5, 12")
    safe_print(f"  Or: Hoodie | Black | ¥189 | 2, 5, 12   size: 8")
    safe_print(f"==================================================")


@client.event
async def on_message(message):
    try:
        print(f"[*] Saw message from {message.author}: '{message.content[:50]}'")
    except UnicodeEncodeError:
        print(f"[*] Saw message from {message.author}: [Content contains special characters]")
    if message.author == client.user:
        return

    text = message.content.strip()

    # ─── COMMAND: !tts / !voice (with shortcuts: !t/!g and !v/!e) ───
    lower_text = text.lower()
    is_gemini = lower_text.startswith("!tts ") or lower_text.startswith("!t ") or lower_text.startswith("!g ")
    is_edge = lower_text.startswith("!voice ") or lower_text.startswith("!v ") or lower_text.startswith("!e ")

    if is_gemini or is_edge:
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("⚠️ **Usage:** `!t [text]` or `!tts [text]` (Gemini Puck) / `!v [text]` or `!voice [text]` (Edge Jenny)")
            return
            
        tts_text = parts[1].strip()
        await message.add_reaction("⏳")
        
        try:
            from voice_generator import VoiceGenerator
            gen = VoiceGenerator()
            output_file = os.path.join(os.getcwd(), "output", f"tts_message_{message.id}.mp3")
            
            if is_gemini:
                # Gemini Puck voice
                res = await gen.generate_audio(tts_text, voice_name="gemini_puck", output_path=output_file)
                label = "Google Gemini Puck (Expressive, Conversational)"
            else:
                # Edge Neural (Jenny)
                res = await gen.generate_audio(tts_text, voice_name="jenny", output_path=output_file)
                label = "Microsoft Jenny (Ultra-clean Neural)"
                
            await message.remove_reaction("⏳", client.user)
            if res and os.path.exists(res):
                await message.add_reaction("✅")
                file_to_send = discord.File(res, filename="voice_note.mp3")
                await message.reply(
                    content=f"🎙️ **Voice note generated!** ({label})\n*\"{tts_text[:120] + ('...' if len(tts_text) > 120 else '')}\"*",
                    file=file_to_send
                )
                try:
                    os.remove(res)
                except: pass
            else:
                await message.add_reaction("❌")
                await message.reply("⚠️ **TTS Generation failed.** Check the bot console logs for details.")
        except Exception as e:
            await message.remove_reaction("⏳", client.user)
            await message.add_reaction("❌")
            await message.reply(f"⚠️ **Error generating voice note:** `{e}`")
        return

    # ─── COMMAND: !sellers / !list ───
    if text.lower() in ["!sellers", "!list"]:
        sellers_info = get_sellers_summary()
        if len(sellers_info) > 1950:
            sellers_info = sellers_info[:1900] + "\n\n*(Truncated due to Discord message length limits)*"
        await message.reply(sellers_info)
        return

    # ─── COMMAND: !browse — Interactive Yupoo browser with dropdowns ───
    if text.lower() in ["!browse", "!b"]:
        db = load_sellers_db()
        if not db:
            await message.reply("⚠️ No sellers configured. Add sellers to `data/yupoo_sellers.json` first.")
            return
        
        view = discord.ui.View(timeout=180)
        view.add_item(BrowseCategorySelect(db))
        await message.reply(
            "🛍️ **OBSCURA Sourcing Browser**\n"
            "**Step 1:** Pick a category to browse:",
            view=view
        )
        return

    # ─── COMMAND: !catalog / !cat ───
    if text.lower() in ["!catalog", "!cat"]:
        sellers_path = BASE_DIR / "data" / "yupoo_sellers.json"
        if not sellers_path.exists():
            await message.reply("⚠️ **Error:** Yupoo sellers database file not found at data/yupoo_sellers.json")
            return
        
        try:
            with open(sellers_path, "r", encoding="utf-8") as f:
                db = json.load(f)
            
            # Send Category by Category
            embeds = []
            
            # Blanks
            if db.get("blanks"):
                blanks_fields = []
                for s in db["blanks"]:
                    blanks_fields.append({
                        "name": f"{s['name']}",
                        "value": f"[🔗 Open Yupoo]({s['url']})\n{s.get('focus', 'Streetwear Blanks')}",
                        "inline": True
                    })
                embeds.append(discord.Embed(
                    title="🏷️ PREMIUM BLANKS & BASIC SUPPLIERS",
                    description="Unbranded heavyweight streetwear - high profit margin, no brand risk.",
                    color=0x2ecc71
                ))
                for field in blanks_fields[:25]: # Discord field limit
                    embeds[-1].add_field(name=field["name"], value=field["value"], inline=field["inline"])
            
            # Replicas Streetwear
            if db.get("replicas_streetwear"):
                sw_fields = []
                for s in db["replicas_streetwear"]:
                    sw_fields.append({
                        "name": f"{s['name']}",
                        "value": f"[🔗 Open Yupoo]({s['url']})\n{s.get('focus', 'Streetwear')}",
                        "inline": True
                    })
                embeds.append(discord.Embed(
                    title="🔥 REPLICA - STREETWEAR & CASUAL HYPE",
                    description="High-demand UK/EU drill streetwear and popular casual brands.",
                    color=0xe74c3c
                ))
                for field in sw_fields[:25]:
                    embeds[-1].add_field(name=field["name"], value=field["value"], inline=field["inline"])
            
            # Replicas Designer
            if db.get("replicas_designer"):
                des_fields = []
                for s in db["replicas_designer"]:
                    des_fields.append({
                        "name": f"{s['name']}",
                        "value": f"[🔗 Open Yupoo]({s['url']})\n{s.get('focus', 'Designer')}",
                        "inline": True
                    })
                embeds.append(discord.Embed(
                    title="💎 REPLICA - LUXURY & DESIGNER BOUTIQUE",
                    description="Premium quality replicas for high-end fashion resale.",
                    color=0x9b59b6
                ))
                for field in des_fields[:25]:
                    embeds[-1].add_field(name=field["name"], value=field["value"], inline=field["inline"])
            
            # Replicas Shoes & Accessories
            shoes = db.get("replicas_shoes", [])
            accs = db.get("replicas_accessories", [])
            if shoes or accs:
                sa_fields = []
                for s in shoes:
                    sa_fields.append({
                        "name": f"{s['name']} (Shoes)",
                        "value": f"[🔗 Open Yupoo]({s['url']})\n{s.get('focus', 'Sneakers')}",
                        "inline": True
                    })
                for s in accs:
                    sa_fields.append({
                        "name": f"{s['name']} (Accessories)",
                        "value": f"[🔗 Open Yupoo]({s['url']})\n{s.get('focus', 'Bags/Accessories')}",
                        "inline": True
                    })
                embeds.append(discord.Embed(
                    title="👟 REPLICA - SHOES & ACCESSORIES",
                    description="Premium batches for sneaker and bag resale.",
                    color=0xf39c12
                ))
                for field in sa_fields[:25]:
                    embeds[-1].add_field(name=field["name"], value=field["value"], inline=field["inline"])
            
            # Send them
            for embed in embeds:
                await message.channel.send(embed=embed)
                await asyncio.sleep(0.5)
            
            # Send the search engines / guides footer
            search_embed = discord.Embed(
                title="🔍 SEARCH ENGINES & SPREADSHEET DATABASES",
                description=(
                    "Use these to search in English and copy Weidian URLs directly:\n\n"
                    "**1. JadeShip** — [jadeship.com](https://www.jadeship.com)\n"
                    "**2. RepSheets** — [repsheets.net](https://repsheets.net)\n"
                    "**3. RepRevs** — [reprevs.com](https://reprevs.com)\n\n"
                    "📌 **How to use:** Paste any Weidian link directly in this channel to scrape it!"
                ),
                color=0x3498db
            )
            await message.channel.send(embed=search_embed)
            
        except Exception as e:
            await message.reply(f"⚠️ **Error loading catalog:** `{e}`")
        return

    # ─── COMMAND: !yupoo <subdomain> ───
    if text.lower().startswith("!yupoo "):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("⚠️ **Usage:** `!yupoo [subdomain]` (e.g. `!yupoo goat-official`)")
            return
        
        subdomain = parts[1].strip().lower()
        if "yupoo.com" in subdomain:
            subdomain = subdomain.replace("https://", "").replace("http://", "").split(".")[0]
            
        await message.add_reaction("⏳")
        status_msg = await message.reply(f"🔍 **Scraping latest albums from `{subdomain}.x.yupoo.com`...**")
        
        try:
            from yupoo_scraper import YupooScraper
            scraper = YupooScraper()
            albums = scraper.scrape_seller(subdomain, max_pages=1)
            
            if not albums:
                await message.remove_reaction("⏳", client.user)
                await message.add_reaction("❌")
                await status_msg.edit(content=f"❌ **No albums found for seller `{subdomain}`.** Make sure the subdomain is correct and public.")
                return
            
            pending_id = str(status_msg.id)
            pending_file = REVIEW_PENDING_DIR / f"{pending_id}.json"
            
            pending_data = {
                "type": "yupoo_catalog",
                "subdomain": subdomain,
                "albums": albums,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(pending_file, "w", encoding="utf-8") as f:
                json.dump(pending_data, f, ensure_ascii=False, indent=2)
            
            # Update seller last_scraped timestamp
            _update_seller_timestamp(subdomain, len(albums))
                
            chunk_size = 25
            total_albums = len(albums)
            imported_count = 0
            _history_cache = load_scrape_history()
            
            for idx in range(0, total_albums, chunk_size):
                chunk = albums[idx:idx+chunk_size]
                embed = discord.Embed(
                    title=f"📦 {subdomain.upper()} Catalog (Items {idx+1} to {min(idx+chunk_size, total_albums)})",
                    description="Reply to this message with numbers to import (e.g. `1, 4, 7`).\nAlready-imported items marked with ✅",
                    color=0x3498db
                )
                
                for k, a in enumerate(chunk, start=idx+1):
                    # Check if already imported
                    dupe, dupe_entry = is_imported(album_url=a.get('album_url'), _cache=_history_cache)
                    dupe_mark = "✅ " if dupe else ""
                    if dupe:
                        imported_count += 1
                    
                    price_str = f"¥{a['price_cny']}" if a.get('price_cny') else "No price"
                    value = f"Price: **{price_str}** | [Link]({a['album_url']})"
                    if dupe and dupe_entry:
                        value += f"\n*Imported: {dupe_entry.get('imported_at', '?')[:10]}*"
                    
                    embed.add_field(
                        name=f"[{k}] {dupe_mark}{a['title'][:50]}",
                        value=value,
                        inline=False
                    )
                
                await message.channel.send(embed=embed, reference=status_msg)
                await asyncio.sleep(0.5)
                
            await message.remove_reaction("⏳", client.user)
            await message.add_reaction("✅")
            dupe_note = f" ({imported_count} already imported)" if imported_count else ""
            await status_msg.edit(content=f"✅ **Scraped {total_albums} items from `{subdomain}`!**{dupe_note}\nReply to any of the catalog lists below with item numbers to select and import them.")
            
        except Exception as e:
            await message.remove_reaction("⏳", client.user)
            await message.add_reaction("❌")
            await status_msg.edit(content=f"⚠️ **Error scraping Yupoo:** `{e}`")
        return

    # ─── COMMAND: !sheet <url> ───
    if text.lower().startswith("!sheet "):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("⚠️ **Usage:** `!sheet [google_sheet_url_or_csv_url]`")
            return
            
        sheet_url = parts[1].strip()
        await message.add_reaction("⏳")
        status_msg = await message.reply(f"📊 **Parsing spreadsheet and extracting product links...**")
        
        try:
            from spreadsheet_ingestor import SpreadsheetIngestor
            ingestor = SpreadsheetIngestor()
            products = ingestor.ingest(sheet_url)
            
            if not products:
                await message.remove_reaction("⏳", client.user)
                await message.add_reaction("❌")
                await status_msg.edit(content="❌ **No Weidian/Taobao/1688 links found in the spreadsheet.** Make sure the sheet is public/shared.")
                return
            
            pending_id = str(status_msg.id)
            pending_file = REVIEW_PENDING_DIR / f"{pending_id}.json"
            
            pending_data = {
                "type": "spreadsheet_import",
                "source_url": sheet_url,
                "products": products,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(pending_file, "w", encoding="utf-8") as f:
                json.dump(pending_data, f, ensure_ascii=False, indent=2)
                
            total_products = len(products)
            chunk_size = 20
            
            for idx in range(0, min(total_products, 100), chunk_size):
                chunk = products[idx:idx+chunk_size]
                embed = discord.Embed(
                    title=f"📊 Spreadsheet Products (Items {idx+1} to {min(idx+chunk_size, total_products)})",
                    description="Reply to this list with numbers to import (e.g. `2, 5, 12`).",
                    color=0xf1c40f
                )
                
                for k, p in enumerate(chunk, start=idx+1):
                    name = p['product_name'][:60] if p.get('product_name') else "Unnamed product"
                    plat = p['platform'].upper()
                    embed.add_field(
                        name=f"[{k}] {name}",
                        value=f"Platform: **{plat}** | Category: *{p.get('category') or 'None'}* | [Source Link]({p['url']})",
                        inline=False
                    )
                
                await message.channel.send(embed=embed, reference=status_msg)
                await asyncio.sleep(0.5)
                
            await message.remove_reaction("⏳", client.user)
            await message.add_reaction("✅")
            
            extra_msg = ""
            if total_products > 100:
                extra_msg = f"\n*(Showing first 100 out of {total_products} items found)*"
                
            await status_msg.edit(content=f"✅ **Extracted {total_products} products!**{extra_msg}\nReply to any of the lists below with numbers to import.")
            
        except Exception as e:
            await message.remove_reaction("⏳", client.user)
            await message.add_reaction("❌")
            await status_msg.edit(content=f"⚠️ **Error parsing spreadsheet:** `{e}`")
        return

    # 🎨 COMMAND: !outfit — Manually curate outfit for on-model generation
    if text.lower().startswith("!outfit "):
        outfit_text = text[8:].strip()
        if not outfit_text:
            await message.reply("⚠️ **Usage:** `!outfit \"product-slug-1\" + \"product-slug-2\"` (e.g. `!outfit \"tech-fleece\" + \"dunk-low\"`)")
            return
        
        await message.add_reaction("👔")
        
        # Parse product slugs from the command
        import re as _re
        slugs = [s.strip().strip('"').strip("'") for s in outfit_text.split("+")]
        slugs = [s for s in slugs if s]
        
        if len(slugs) < 2:
            await message.reply("⚠️ Need at least 2 products for an outfit. Separate with `+`")
            return
        
        # Find matching folders in MANUAL_CURATION
        curation_dir = Path(__file__).parent / "MANUAL_CURATION"
        found_products = []
        not_found = []
        
        for slug in slugs:
            # Search for folder names containing the slug
            matched_folder = None
            if curation_dir.exists():
                for folder in curation_dir.iterdir():
                    if folder.is_dir() and slug.lower() in folder.name.lower():
                        meta_file = folder / "metadata.json"
                        if meta_file.exists():
                            try:
                                with open(meta_file, "r", encoding="utf-8") as f:
                                    meta = json.load(f)
                                found_products.append({
                                    "path": str(folder),
                                    "category": meta.get("category", "clothing"),
                                    "name": meta.get("product_name", folder.name)
                                })
                                matched_folder = folder
                                break
                            except Exception:
                                pass
            
            if not matched_folder:
                not_found.append(slug)
        
        if not_found:
            await message.reply(f"⚠️ **Could not find** these products in MANUAL_CURATION: {', '.join(not_found)}")
            if len(found_products) < 2:
                return
        
        # Determine gender from first product metadata
        first_meta_path = Path(found_products[0]["path"]) / "metadata.json"
        gender = "male"
        try:
            with open(first_meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                gender = meta.get("gender", "male")
        except Exception:
            pass
        
        outfit_name = " + ".join([p["name"][:20] for p in found_products])
        
        outfit_config = {
            "name": outfit_name,
            "products": found_products,
            "gender": gender
        }
        
        # Save outfit config for generation worker
        outfit_file = Path(__file__).parent / "MANUAL_CURATION" / f"_outfit_{int(datetime.now().timestamp())}.json"
        try:
            with open(outfit_file, "w", encoding="utf-8") as f:
                json.dump(outfit_config, f, indent=2)
            
            embed = discord.Embed(
                title="👔 Outfit Curated",
                description=f"**{outfit_name}**\n\nThis outfit will get **on-model editorial shots** (the ONLY time products go on a model).",
                color=0x9b59b6
            )
            for i, p in enumerate(found_products):
                embed.add_field(name=f"Item {i+1}", value=p["name"], inline=True)
            embed.set_footer(text="Generation will run on next worker cycle")
            
            await message.reply(embed=embed)
            await message.remove_reaction("👔", client.user)
            await message.add_reaction("✅")
        except Exception as e:
            await message.reply(f"⚠️ Error saving outfit: `{e}`")
            await message.remove_reaction("👔", client.user)
            await message.add_reaction("❌")
        return

    # ─── CHECK: Is this a REPLY to a contact sheet? ───
    if message.reference and message.reference.message_id:
        ref_id = str(message.reference.message_id)
        pending_path = REVIEW_PENDING_DIR / f"{ref_id}.json"
        
        if pending_path.exists():
            # This is a reply to a contact sheet! Handle the selection flow.
            await handle_contact_sheet_reply(message, pending_path)
            return

    # ─── NEW: Chinese marketplace link-only drop — scrape it directly ───
    if not message.attachments:
        chinese_match = LINK_PATTERN.search(message.content)
        if chinese_match:
            product_url = chinese_match.group(1).strip()
            await trigger_scraper_and_post_result(message, product_url)
            return
        # No attachments AND no Yupoo link — route to brain for Q&A or casual chat
        if message.content.strip():
            await handle_brain_chat(message)
        return


    text = message.content.strip()
    if not text:
        await message.reply(
            "⚠️ **Missing info!** Send the message like this:\n"
            "```\n"
            "[attach images] Product Name | Color | ¥price | link\n"
            "```\n"
            "Examples:\n"
            "```\n"
            "Bape Hoodie | Black | ¥189 | https://weidian.com/...\n"
            "Cargo Shorts | ¥120 | https://kakobuy.com/...\n"
            "https://weidian.com/...\n"
            "```"
        )
        return

    product_name, color, price, link, currency = parse_message(text)
    
    print(f"\n[+] New product drop from {message.author}!")
    print(f"    Product: {product_name or '(unnamed)'}")
    print(f"    Color:   {color or '(default)'}")
    print(f"    Price:   {currency} {price or '0'}")
    print(f"    Link:    {link or '(none)'}")

    # Build folder name
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:4]
    
    if product_name:
        slug = slugify(product_name)
        folder_name = f"{slug}_{color.lower() if color else 'default'}_{ts}_{uid}"
    else:
        folder_name = f"product_{color.lower() if color else 'drop'}_{ts}_{uid}"
    
    product_dir = MANUAL_CURATION_DIR / folder_name
    product_dir.mkdir(parents=True, exist_ok=True)

    # Download images
    saved_images = 0
    for attachment in message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
            file_path = product_dir / attachment.filename
            try:
                await attachment.save(file_path)
                saved_images += 1
                print(f"    [OK] Saved: {attachment.filename}")
            except Exception as e:
                print(f"    [!] Failed: {e}")

    if saved_images > 0:
        # Save metadata (link + product info + color)
        metadata = {
            "product_name": product_name,
            "color": color,
            "price_cny": price if currency == "CNY" else round(price * 7.2),
            "price": price,
            "currency": currency,
            "link": link,
            "timestamp": ts,
            "source": "discord",
            "author": str(message.author),
            "image_count": saved_images
        }
        
        # --- SIZE CHART DETECTION ---
        size_info = "Not specified"
        # Check filenames for "size" or "chart"
        for img in product_dir.glob("*"):
            if "size" in img.name.lower() or "chart" in img.name.lower():
                print(f"    [SIZE] Chart detected: {img.name}. Analyzing...")
                size_info = extract_size_info(str(img))
                print(f"    [SIZE] Extracted: {size_info}")
                break
        # Also check if user mentioned "size" in the Discord message text
        if size_info == "Not specified" and ("size" in text.lower() or "chart" in text.lower()):
            # Try the last attachment as the size chart
            for img in sorted(product_dir.glob("*"), reverse=True):
                if img.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                    print(f"    [SIZE] Message mentions 'size'. Analyzing: {img.name}...")
                    size_info = extract_size_info(str(img))
                    print(f"    [SIZE] Extracted: {size_info}")
                    break
        
        # --- CATEGORIZATION & SET DETECTION ---
        detected_cat, is_set = detect_category(product_name or "", text)

        metadata["size_info"] = size_info
        metadata["category"] = detected_cat
        metadata["is_set"] = is_set

        # Save link.txt (for the manual_worker)
        with open(product_dir / "link.txt", "w", encoding="utf-8") as f:
            f.write(link)
        
        # Save full metadata
        with open(product_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        # ── AUTO-TAG with Style Intelligence ──
        # Uses Gemini Vision to tag gender/niche/category/weight in background
        niche = "?"
        gender = "?"
        if auto_tag:
            try:
                tags = auto_tag(product_dir)
                niche = tags.get("niche", "?").title()
                gender = tags.get("gender", "?").title()
                scene = tags.get("scene_style", "?").replace("_", " ").title()
                weight = tags.get("weight_kg", 0.4)
                print(f"    [TAG] {gender} · {niche} · {scene} · ~{weight}kg")
            except Exception as e:
                print(f"    [TAG] Style tagging failed (non-critical): {e}")
        
        # Category detection is now done above

        inv_data = {
            "productName": product_name or "Unknown Item",
            "category": detected_cat,
            "productUrl": link,
            "localImagePath": str(next(product_dir.glob("*.png"), next(product_dir.glob("*.jpg"), next(product_dir.glob("*"), "")))),
            "price": price,
            "size_info": size_info,
            "metadata_path": str(product_dir / "metadata.json")
        }
        update_inventory(inv_data)

        print(f"    [OK] Saved metadata + Inventory [{detected_cat}]")
        
        # Build confirmation reply
        await message.add_reaction("✅")
        
        # ── REPLY TRACKING: Mark the original scout card as processed ──
        # If the user REPLIED to a scout card, swap 📋 → ✅ on it
        if message.reference and message.reference.message_id:
            try:
                original_msg = await message.channel.fetch_message(message.reference.message_id)
                # Remove the 📋 "pending" reaction from the bot
                try:
                    await original_msg.remove_reaction("📋", client.user)
                except Exception:
                    pass  # May not have the reaction
                # Add ✅ "processed" reaction to the original scout card
                await original_msg.add_reaction("✅")
                print(f"    [TRACK] Marked original scout card as ✅ processed")
            except Exception as e:
                print(f"    [TRACK] Could not update original card: {e}")
        
        reply_parts = [f"🎯 **Product queued for AI generation!**"]
        if product_name:
            reply_parts.append(f"📦 **Name**: `{product_name}`")
        if color:
            reply_parts.append(f"🎨 **Color**: `{color}`")
        if size_info and size_info != "Not specified":
            reply_parts.append(f"📏 **Size Info**: `{size_info}`")
        if gender != "?" or niche != "?":
            reply_parts.append(f"🏷️ **Tags**: `{gender} / {niche}`")
        if link:
            reply_parts.append(f"🔗 Link saved for checkout")
        else:
            reply_parts.append(f"⚠️ No purchase link detected")
            
        # Attach the first image
        first_img_path = next(product_dir.glob("*.png"), next(product_dir.glob("*.jpg"), next(product_dir.glob("*.jpeg"), next(product_dir.glob("*.webp"), None))))
        
        if first_img_path:
            await message.reply("\n".join(reply_parts), file=discord.File(str(first_img_path)))
        else:
            await message.reply("\n".join(reply_parts))
    else:
        product_dir.rmdir()
        await message.add_reaction("❌")
        await message.reply("⚠️ No valid images found.")


async def create_yupoo_contact_sheet(yupoo_images, yupoo_referer):
    """Download Yupoo images temporarily and generate a contact sheet."""
    import tempfile
    import shutil
    import uuid
    from sourcing_utils import create_contact_sheets
    import httpx
    
    # Download images
    temp_dir = BASE_DIR / f"yupoo_temp_{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(exist_ok=True)
    
    local_paths = []
    url_mapping = {}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for i, url in enumerate(yupoo_images[:40]):
            try:
                resp = await client.get(url, headers={
                    "Referer": yupoo_referer or "https://yupoo.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                if resp.status_code == 200:
                    ext = url.split('.')[-1].split('?')[0].lower()
                    if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                        ext = 'jpg'
                    path = temp_dir / f"img_{i+1}.{ext}"
                    path.write_bytes(resp.content)
                    local_paths.append(str(path))
                    url_mapping[str(i+1)] = url
            except Exception as e:
                safe_print(f"      [Yupoo Sheet] Failed to download {url}: {e}")
                
    if not local_paths:
        try:
            shutil.rmtree(temp_dir)
        except: pass
        return [], {}
        
    # Generate contact sheets
    contact_sheets = create_contact_sheets(local_paths)
    
    # Clean up downloaded raw files
    try:
        shutil.rmtree(temp_dir)
    except: pass
    
    return contact_sheets, url_mapping


async def trigger_scraper_and_post_result(message, product_url, yupoo_images=None, yupoo_referer=None, yupoo_title=None):
    """Trigger Weidian scraper and post the rich embed to Discord."""
    # ── PHASE 2C: Deduplication check before scraping ──
    try:
        from chinese_sourcing_agent import parse_item_id
        import urllib.parse as _urlparse
        _parsed_domain = _urlparse.urlparse(product_url).netloc.replace("www.", "")
        _platform = "weidian" if ("weidian" in _parsed_domain or "youshop" in _parsed_domain) else ("1688" if "1688" in _parsed_domain else "taobao")
        check_item_id = parse_item_id(product_url, _platform)
        
        # Check review_pending for existing imports
        dupe_found = None
        for pf in REVIEW_PENDING_DIR.glob("*.json"):
            try:
                pdata = json.loads(pf.read_text(encoding="utf-8"))
                if pdata.get("item_id") == check_item_id or pdata.get("album_url") == product_url:
                    dupe_found = (pdata.get("product_name", "Unknown"), pdata.get("timestamp", "?"))
                    break
            except Exception:
                continue
        
        # Check MANUAL_CURATION for existing imports
        if not dupe_found:
            for mc_dir in MANUAL_CURATION_DIR.iterdir():
                mc_meta = mc_dir / "metadata.json"
                if mc_meta.exists():
                    try:
                        mdata = json.loads(mc_meta.read_text(encoding="utf-8"))
                        if mdata.get("item_id") == check_item_id:
                            dupe_found = (mdata.get("product_name", "Unknown"), mdata.get("timestamp", "?"))
                            break
                    except Exception:
                        continue
        
        # Check permanent scrape history (catches old imports even if pending/curation cleaned up)
        if not dupe_found:
            hist_dupe, hist_entry = is_imported(item_id=check_item_id, platform=_platform)
            if hist_dupe and hist_entry:
                dupe_found = (hist_entry.get("product_name", "Unknown"), hist_entry.get("imported_at", "?"))
        
        if dupe_found:
            warn_msg = await message.reply(
                f"⚠️ **Duplicate detected!** This product was already imported as "
                f"**\"{dupe_found[0]}\"** on `{dupe_found[1]}`.\n"
                f"React with 👍 within 30s to import again, or ignore to skip."
            )
            await warn_msg.add_reaction("indigo_approvals" if False else "👍")
            
            def check_reaction(reaction, user):
                return (str(reaction.emoji) == "👍" and 
                        reaction.message.id == warn_msg.id and 
                        user != client.user)
            try:
                await client.wait_for("reaction_add", timeout=30.0, check=check_reaction)
                safe_print(f"    [DEDUP] User confirmed re-import of {check_item_id}")
            except asyncio.TimeoutError:
                await warn_msg.edit(content="⏭️ **Skipped** — duplicate product, no confirmation received.")
                return
    except Exception as dedup_err:
        safe_print(f"    [DEDUP] Check failed (non-blocking): {dedup_err}")
    
    await message.add_reaction("⏳")
    import_source = "Yupoo Album" if yupoo_images else "Chinese Marketplace"
    status_indicator = await message.reply(
        f"🔍 **Got it!** Importing product details from {import_source}...\n"
        f"📂 `{product_url}`\n"
        f"I'm scraping sizes, colors, price, material, and seller info."
    )
    try:
        from chinese_sourcing_agent import ChineseSourcingAgent
        agent = ChineseSourcingAgent(headless=True)
        res = await agent.scrape_product(product_url, generate_contact_sheet=True)
        await message.remove_reaction("⏳", client.user)
        
        if isinstance(res, dict):
            meta = res.get("metadata", {})
            title = yupoo_title or meta.get("product_name", "Unknown Title")
            price_str = meta.get("price_string", "Check link")
            price_cny = meta.get("price_cny", 0)
            colors = meta.get("colors", [])
            sizes = meta.get("sizes", [])
            url_mapping = res.get("url_mapping", {})
            sheets = res.get("sheets", [])
            
            # Overwrite Weidian images with high-quality Yupoo photos if available
            if yupoo_images:
                status_update = await message.channel.send("🎨 *Overwriting Weidian images with high-quality Yupoo photos...*")
                yupoo_sheets, yupoo_map = await create_yupoo_contact_sheet(yupoo_images, yupoo_referer)
                if yupoo_sheets and yupoo_map:
                    # Clean up Weidian sheets from disk to avoid temp files leak
                    for sheet in sheets:
                        if os.path.exists(sheet):
                            try:
                                os.remove(sheet)
                            except: pass
                    
                    sheets = yupoo_sheets
                    url_mapping = yupoo_map
                    try:
                        await status_update.delete()
                    except: pass
                else:
                    await status_update.edit(content="⚠️ *Failed to load Yupoo photos. Falling back to Weidian photos.*")
            
            # ── Calculate retail price estimate ──
            try:
                from pricing_engine import calculate_final_price
                price_res = calculate_final_price(price_cny, "CNY") if price_cny > 0 else None
                retail_usd = round(price_res["final_usd"]) if price_res else 0
            except Exception:
                retail_usd = round(price_cny / 7.2 * 1.8) if price_cny > 0 else 0
            
            usd_cost = round(price_cny / 7.2, 2) if price_cny > 0 else 0
            
            # ── PHASE 2A: Rich Discord embed with ALL metadata ──
            embed = discord.Embed(
                title=f"📦 {title}",
                description=meta.get("description", "")[:200] or "Product imported from Chinese marketplace",
                color=0x1a1a2e
            )
            
            # Price field
            price_text = f"¥{price_str}"
            if usd_cost > 0:
                price_text += f" (~${usd_cost} USD)"
            if retail_usd > 0:
                price_text += f" → **${retail_usd} retail**"
            embed.add_field(name="💰 Price", value=price_text, inline=True)
            
            # Brand
            brand = meta.get("brand_name", "")
            if brand:
                embed.add_field(name="🏷️ Brand", value=brand, inline=True)
            
            # Category
            category = meta.get("product_category", "")
            if category:
                embed.add_field(name="📊 Category", value=category.title(), inline=True)
            
            # Material
            material = meta.get("material", "")
            if material:
                embed.add_field(name="📦 Material", value=material, inline=False)
            
            # Sizes & Colors
            colors_str = " ┃ ".join(colors[:15]) if colors and colors != ["default"] else "Check link"
            sizes_str = " ┃ ".join(sizes[:20]) if sizes else "Check link"
            embed.add_field(name="📏 Sizes", value=sizes_str, inline=True)
            embed.add_field(name="🎨 Colors", value=colors_str, inline=True)
            
            # Measurements
            measurements = meta.get("measurements", {})
            if measurements:
                embed.add_field(name="📐 Measurements", value=f"Available ({len(measurements)} sizes)", inline=True)
            
            # Seller info
            seller = meta.get("seller", {})
            seller_name = seller.get("name", "")
            if seller_name:
                seller_text = f"{seller_name}"
                if seller.get("rating"):
                    seller_text += f" (⭐{seller['rating']}"
                    if seller.get("sales_volume"):
                        seller_text += f", {seller['sales_volume']:,} sales"
                    seller_text += ")"
                embed.add_field(name="🏪 Seller", value=seller_text, inline=True)
            
            # Shipping origin
            ship_origin = seller.get("shipping_origin", "")
            ship_cost = seller.get("domestic_shipping_cny", 0)
            if ship_origin or ship_cost:
                ship_text = ship_origin or "China"
                if ship_cost:
                    ship_text += f", ¥{ship_cost} domestic"
                embed.add_field(name="🚚 Ships From", value=ship_text, inline=True)
            
            # Model info
            model_info = meta.get("model_info", "")
            if model_info:
                embed.add_field(name="👤 Model", value=model_info, inline=False)
            
            # Links
            embed.add_field(
                name="🔗 Links",
                value=f"[Source Product]({product_url})" if not yupoo_referer else f"[Yupoo Album]({yupoo_referer}) ┃ [Weidian Link]({product_url})",
                inline=False
            )
            
            # Image count & instructions
            embed.set_footer(text=f"{len(url_mapping)} images scraped ┃ Reply with numbers to select (e.g. 2, 5, 8) or \"all\"")
            embed.timestamp = datetime.utcnow()
            
            files = [discord.File(sheet) for sheet in sheets if os.path.exists(sheet)]
            sent_msg = await message.reply(embed=embed, files=files)
            await message.add_reaction("✅")
            try:
                await status_indicator.delete()
            except:
                pass
            
            # ── Save ALL enriched metadata to review_pending ──
            pending_data = {
                "product_name": title,
                "item_id": meta.get("item_id", ""),
                "platform": meta.get("platform", ""),
                "album_url": product_url,
                "referer": yupoo_referer or product_url,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_images": len(url_mapping),
                "url_mapping": url_mapping,
                "source": "chinese_sourcing_agent" if not yupoo_images else "yupoo_scraper",
                "metadata": {
                    "price_cny": price_cny,
                    "price_string": price_str,
                    "link": product_url,
                    "item_id": meta.get("item_id", ""),
                    "platform": meta.get("platform", ""),
                    "whatsapp": "",
                    "wechat": "",
                    "discord_invite": "",
                    "purchase_links": [product_url],
                    "variant_mappings": meta.get("variant_mappings", {"colors": {}, "sizes": {}}),
                    "description": meta.get("description", ""),
                    "material": meta.get("material", ""),
                    "weight_gsm": meta.get("weight_gsm", 0),
                    "care_instructions": meta.get("care_instructions", ""),
                    "model_info": meta.get("model_info", ""),
                    "brand_name": meta.get("brand_name", ""),
                    "product_category": meta.get("product_category", ""),
                    "measurements": meta.get("measurements", {}),
                    "stock_status": meta.get("stock_status", {}),
                    "seller": meta.get("seller", {}),
                    "colors": colors,
                    "sizes": sizes
                }
            }
            
            pending_path = REVIEW_PENDING_DIR / f"{sent_msg.id}.json"
            with open(pending_path, "w", encoding="utf-8") as f:
                json.dump(pending_data, f, indent=2, ensure_ascii=False)
                
            # Add 📋 reaction to mark as pending review
            await sent_msg.add_reaction("📋")
        else:
            await message.add_reaction("❌")
            await message.reply("⚠️ **Import failed.** Make sure the link is a valid 1688, Taobao, or Weidian product page.")
    except Exception as e:
        await message.remove_reaction("⏳", client.user)
        await message.add_reaction("❌")
        await message.reply(f"⚠️ **Error during import:** `{e}`")

async def handle_catalog_or_sheet_selection(message, pending_data, p_type):
    """Handle selections for !yupoo or !sheet commands."""
    parsed = parse_contact_sheet_reply(message.content)
    
    indices = []
    if parsed.get("select_all"):
        if p_type == "yupoo_catalog":
            indices = list(range(1, len(pending_data.get("albums", [])) + 1))
        else:
            indices = list(range(1, len(pending_data.get("products", [])) + 1))
    else:
        for g in parsed.get("groups", []):
            indices.extend(g["indices"])
            
    # Sort and deduplicate
    indices = sorted(list(set(indices)))
    
    if not indices:
        await message.reply("⚠️ **No item numbers detected!** Reply to the list with item numbers like `1, 4, 7` to select them.")
        return
        
    await message.add_reaction("⏳")
    
    if p_type == "yupoo_catalog":
        albums = pending_data.get("albums", [])
        selected_albums = []
        for idx in indices:
            if 1 <= idx <= len(albums):
                selected_albums.append(albums[idx-1])
        
        if not selected_albums:
            await message.reply("⚠️ **Invalid selection numbers.** Make sure they match the list.")
            return
            
        await message.reply(f"🚀 **Importing {len(selected_albums)} selected albums...**")
        
        from yupoo_scraper import YupooScraper
        scraper = YupooScraper()
        
        for album in selected_albums:
            await message.channel.send(f"🔍 *Fetching detail page for: `{album['title'][:40]}`...*")
            try:
                detail = scraper.scrape_album_detail(album['album_url'])
                weidian_url = detail.get('weidian_link')
                
                if not weidian_url:
                    await message.channel.send(f"⚠️ No Weidian/Taobao/1688 link found in description for: `{album['title'][:40]}`")
                    continue
                    
                await message.channel.send(f"📥 *Found link: `{weidian_url}`. Triggering scraper...*")
                await trigger_scraper_and_post_result(
                    message, 
                    weidian_url, 
                    yupoo_images=detail.get('images', []), 
                    yupoo_referer=album['album_url'],
                    yupoo_title=album['title']
                )
                
                # Record to permanent history for dedup
                record_import(
                    album_url=album.get('album_url'),
                    product_name=album.get('title', ''),
                    seller=pending_data.get('subdomain', ''),
                    platform=detail.get('platform', 'yupoo'),
                    source="discord_yupoo"
                )
                
            except Exception as e:
                await message.channel.send(f"❌ Error importing `{album['title'][:40]}`: `{e}`")
                
    elif p_type == "spreadsheet_import":
        products = pending_data.get("products", [])
        selected_products = []
        for idx in indices:
            if 1 <= idx <= len(products):
                selected_products.append(products[idx-1])
                
        if not selected_products:
            await message.reply("⚠️ **Invalid selection numbers.** Make sure they match the list.")
            return
            
        await message.reply(f"🚀 **Importing {len(selected_products)} selected products from spreadsheet...**")
        
        for p in selected_products:
            url = p.get('url')
            if not url:
                continue
            await message.channel.send(f"📥 *Importing `{p.get('product_name', 'Unnamed')[:40]}` (`{url}`)...*")
            try:
                await trigger_scraper_and_post_result(message, url)
            except Exception as e:
                await message.channel.send(f"❌ Error importing `{p.get('product_name', 'Unnamed')[:40]}`: `{e}`")
                
    await message.remove_reaction("⏳", client.user)


# ─── CONTACT SHEET REPLY HANDLER ────────────────────────────────

async def handle_contact_sheet_reply(message, pending_path: Path):
    """
    Handle a user's reply to a contact sheet message.
    Downloads selected HQ images, splits into folders for color/part, auto-poses front/back.
    """
    print(f"\n[+] Contact sheet reply from {message.author}!")
    
    # Load the pending data
    try:
        pending_data = json.loads(pending_path.read_text(encoding="utf-8"))
    except Exception as e:
        await message.reply(f"⚠️ Error reading pending data: {e}")
        return
    
    # Check for Yupoo catalog or Spreadsheet import type
    p_type = pending_data.get("type")
    if p_type in ("yupoo_catalog", "spreadsheet_import"):
        await handle_catalog_or_sheet_selection(message, pending_data, p_type)
        return
    
    # Parse the user's selection
    parsed = parse_contact_sheet_reply(message.content)
    
    # Handle "all" selection
    if parsed.get("select_all"):
        total = pending_data.get("total_images", 0)
        # Create a single default group with all images
        parsed["groups"] = [{
            "indices": list(range(1, total + 1)),
            "color": "default",
            "part": None,
            "is_size": False,
            "is_detail": False
        }]
    
    if not parsed.get("groups"):
        await message.reply(
            "⚠️ **No image numbers detected!** Reply with numbers like:\n"
            "```\n"
            "1, 2 black\n"
            "1, 2 top red | 3, 4 bottom red\n"
            "```"
        )
        return
        
    meta = pending_data.get("metadata", {})
    product_name = parsed.get("product_name") or pending_data.get("product_name", "Unknown Product")
    price = parsed.get("price") or meta.get("price_cny", 0)
    link = parsed.get("link") or meta.get("link", "")
    
    url_mapping = pending_data.get("url_mapping", {})
    
    # 1. Collect and categorize all selections
    size_indices = []
    detail_indices = []
    product_groups = []
    all_selected_indices = set()
    
    for g in parsed["groups"]:
        # Validate indices exist in contact sheet
        g_indices = [idx for idx in g["indices"] if str(idx) in url_mapping]
        if not g_indices:
            continue
            
        all_selected_indices.update(g_indices)
        
        if g["is_size"]:
            size_indices.extend(g_indices)
        elif g["is_detail"]:
            detail_indices.extend(g_indices)
        else:
            product_groups.append({
                "indices": g_indices,
                "color": g["color"],
                "part": g["part"]
            })
            
    # If the user only specified sizes or details (no regular product shots),
    # treat all other images as a default product group
    if all_selected_indices and not product_groups:
        remaining_indices = list(all_selected_indices - set(size_indices) - set(detail_indices))
        if remaining_indices:
            product_groups.append({
                "indices": remaining_indices,
                "color": "default",
                "part": None
            })
            
    if not all_selected_indices:
        await message.reply(f"⚠️ None of the selected numbers exist in the contact sheet. Max is {len(url_mapping)}.")
        return
    
    # ── COLOR CROSS-REFERENCE: Validate user-picked colors against Weidian stock ──
    weidian_colors = [c.lower() for c in meta.get("colors", [])]
    if weidian_colors:
        color_warnings = []
        for g in product_groups:
            user_color = (g.get("color") or "").lower()
            if user_color and user_color != "default" and user_color not in weidian_colors:
                # Find closest match
                closest = None
                for wc in weidian_colors:
                    if user_color in wc or wc in user_color:
                        closest = wc
                        break
                if closest:
                    color_warnings.append(f"You said **{user_color}** → closest Weidian match: **{closest}**")
                else:
                    avail = ", ".join(weidian_colors[:8])
                    color_warnings.append(f"⚠️ Color **{user_color}** not found on Weidian! Available: {avail}")
        if color_warnings:
            warning_text = "\n".join(color_warnings)
            await message.reply(f"🎨 **Color Check:**\n{warning_text}\n\n_Proceeding anyway — double-check if needed._")
        
    await message.add_reaction("⏳")
    
    # 2. Download all selected images to a temporary directory once
    import tempfile
    import shutil
    temp_download_dir = Path(tempfile.gettempdir()) / f"hq_download_{uuid.uuid4().hex[:8]}"
    temp_download_dir.mkdir(parents=True, exist_ok=True)
    
    from sourcing_utils import download_selected_hq_images
    downloaded_paths = await download_selected_hq_images(
        pending_data, list(all_selected_indices), str(temp_download_dir)
    )
    
    if not downloaded_paths:
        await message.remove_reaction("⏳", client.user)
        await message.add_reaction("❌")
        await message.reply("⚠️ Failed to download any HQ images. The links may have expired.")
        try:
            shutil.rmtree(temp_download_dir)
        except: pass
        return
        
    # Map from original index to temporary file path
    temp_files_map = {}
    for path in downloaded_paths:
        match = re.search(r'img_(\d+)\.', os.path.basename(path))
        if match:
            idx = int(match.group(1))
            temp_files_map[idx] = path
            
    # 3. Create folders for each product group and copy/rename images
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:4]
    slug = slugify(product_name) if product_name != "Unknown Product" else "sourcing-pick"
    
    created_folders = []
    total_products = 0
    total_charts = 0
    size_info = "Not specified"
    
    for g_idx, group in enumerate(product_groups):
        grp_color = group["color"] or "default"
        grp_part = group["part"]
        
        # Build folder name specific to this color and set-part
        suffix_parts = []
        if grp_part:
            suffix_parts.append(grp_part.lower())
        suffix_parts.append(grp_color.lower())
        
        suffix = "_".join(suffix_parts)
        folder_name = f"{slug}_{suffix}_{ts}_{uid}_{g_idx+1}"
        product_dir = MANUAL_CURATION_DIR / folder_name
        product_dir.mkdir(parents=True, exist_ok=True)
        
        grp_saved_products = 0
        grp_saved_charts = 0
        
        # A. Copy regular product shots with front/back auto-ordering
        for i, idx in enumerate(group["indices"]):
            src_path = temp_files_map.get(idx)
            if not src_path or not os.path.exists(src_path):
                continue
                
            # Auto-pose renaming
            ext = os.path.splitext(src_path)[1]
            if i == 0:
                final_name = f"front_angle{ext}"
            elif i == 1:
                final_name = f"back_angle{ext}"
            elif i == 2:
                final_name = f"side_angle{ext}"
            else:
                final_name = f"angle_{i+1}{ext}"
                
            shutil.copy2(src_path, str(product_dir / final_name))
            grp_saved_products += 1
            total_products += 1
            
        # B. Copy size charts to this folder
        from size_chart_reader import extract_size_info
        for i, idx in enumerate(size_indices):
            src_path = temp_files_map.get(idx)
            if not src_path or not os.path.exists(src_path):
                continue
                
            ext = os.path.splitext(src_path)[1]
            final_name = f"size_chart_{i+1}{ext}"
            dest_path = product_dir / final_name
            shutil.copy2(src_path, str(dest_path))
            grp_saved_charts += 1
            total_charts += 1
            
            # Extract size info from the size chart image
            try:
                chart_info = extract_size_info(str(dest_path))
                if chart_info and chart_info != "Not specified":
                    size_info = chart_info
            except Exception as e:
                print(f"    [SIZE] Error reading size chart: {e}")
                
        # C. Copy detail images to this folder
        for i, idx in enumerate(detail_indices):
            src_path = temp_files_map.get(idx)
            if not src_path or not os.path.exists(src_path):
                continue
                
            ext = os.path.splitext(src_path)[1]
            final_name = f"detail_close_{i+1}{ext}"
            shutil.copy2(src_path, str(product_dir / final_name))
            
        # D. Write metadata.json for this folder
        detected_cat, is_set = detect_category(product_name, message.content)
        if grp_part:
            is_set = True
            
        metadata = {
            "product_name": f"{product_name} ({grp_part.title()})" if grp_part else product_name,
            "color": grp_color,
            "part": grp_part,
            "item_id": pending_data.get("item_id", meta.get("item_id", "")),
            "platform": pending_data.get("platform", meta.get("platform", "")),
            "price_cny": price,
            "link": link,
            "album_url": pending_data.get("album_url", ""),
            "timestamp": ts,
            "source": pending_data.get("source", "yupoo_contact_sheet"),
            "author": str(message.author),
            "image_count": grp_saved_products + grp_saved_charts + len(detail_indices),
            "product_images": grp_saved_products,
            "size_charts": grp_saved_charts,
            "size_info": size_info,
            "category": detected_cat,
            "product_category": meta.get("product_category", detected_cat),
            "is_set": is_set,
            "set_partner": None,  # Auto-computed below for sets
            "brand_name": meta.get("brand_name", ""),
            "selected_indices": group["indices"],
            "material": meta.get("material", ""),
            "weight_gsm": meta.get("weight_gsm", 0),
            "care_instructions": meta.get("care_instructions", ""),
            "model_info": meta.get("model_info", ""),
            "description": meta.get("description", ""),
            "variant_mappings": meta.get("variant_mappings", {"colors": {}, "sizes": {}}),
            "measurements": meta.get("measurements", {}),
            "stock_status": meta.get("stock_status", {}),
            "colors": meta.get("colors", []),
            "sizes": meta.get("sizes", []),
            "seller": meta.get("seller", {}),
            "seller_contact": {
                "whatsapp": meta.get("whatsapp", ""),
                "wechat": meta.get("wechat", ""),
                "discord": meta.get("discord_invite", "")
            },
            "purchase_links": meta.get("purchase_links", []),
            "generation_status": "pending",
            "storefront_status": "not_listed",
            "storefront_product_id": None
        }
        
        # Auto-compute set_partner for tracksuit/set items
        if grp_part and grp_part.lower() in ("top", "bottom"):
            partner_part = "bottom" if grp_part.lower() == "top" else "top"
            partner_name = f"{product_name}-{partner_part}"
            metadata["set_partner"] = partner_name
        
        with open(product_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        with open(product_dir / "link.txt", "w", encoding="utf-8") as f:
            f.write(link)
            
        # Style auto-tagging
        niche = "?"
        gender = "?"
        if auto_tag:
            try:
                tags = auto_tag(product_dir)
                niche = tags.get("niche", "?").title()
                gender = tags.get("gender", "?").title()
            except Exception as e:
                print(f"    [TAG] Style tagging failed: {e}")
                
        # Register in inventory spreadsheet
        inv_data = {
            "productName": metadata["product_name"],
            "category": detected_cat,
            "productUrl": link,
            "localImagePath": str(next(product_dir.glob("front_angle*"), next(product_dir.glob("angle_*"), next(product_dir.glob("*.jpg"), "")))),
            "price": price,
            "size_info": size_info,
            "metadata_path": str(product_dir / "metadata.json")
        }
        update_inventory(inv_data)
        
        created_folders.append({
            "color": grp_color,
            "part": grp_part,
            "folder": folder_name,
            "preview_img": inv_data["localImagePath"]
        })
        
    # Clean up temporary downloads
    try:
        shutil.rmtree(temp_download_dir)
    except: pass
    
    # ── UPDATE DISCORD REACTIONS ──
    await message.remove_reaction("⏳", client.user)
    await message.add_reaction("✅")
    
    # Swap 📋 → ✅ on the original contact sheet message
    try:
        original_msg = await message.channel.fetch_message(message.reference.message_id)
        try:
            await original_msg.remove_reaction("📋", client.user)
        except Exception: pass
        await original_msg.add_reaction("✅")
    except Exception as e:
        print(f"    [TRACK] Could not update original card: {e}")
        
    # ── BUILD REPLY ──
    reply_parts = [f"🎯 **Product queued for AI generation!**"]
    reply_parts.append(f"📦 **Base Name**: `{product_name}`")
    
    if len(created_folders) > 1:
        reply_parts.append(f"📂 **Spelled Folders** ({len(created_folders)} splits):")
        for cf in created_folders:
            lbl = f"{cf['color']}"
            if cf['part']:
                lbl = f"{cf['part']} in {lbl}"
            reply_parts.append(f"  • `{lbl}`")
    else:
        cf = created_folders[0]
        lbl = f"{cf['color']}"
        if cf['part']:
            lbl = f"{cf['part']} in {lbl}"
        reply_parts.append(f"🎨 **Color/Part**: `{lbl}`")
        
    reply_parts.append(f"📸 **Totals**: {total_products} product shots + {total_charts} size charts")
    if size_info and size_info != "Not specified":
        reply_parts.append(f"📏 **Size Info**: `{size_info}`")
    if price:
        reply_parts.append(f"💰 **Price**: ¥{price}")
        
    # Send preview file of the first created folder's front view
    preview_file_path = created_folders[0]["preview_img"]
    if preview_file_path and os.path.exists(preview_file_path):
        await message.reply("\n".join(reply_parts), file=discord.File(preview_file_path))
    else:
        await message.reply("\n".join(reply_parts))
        
    print(f"    [DONE] Queued {len(created_folders)} splits for: {product_name}")
    
    # Record to permanent scrape history AFTER images are actually saved
    record_import(
        item_id=meta.get("item_id", ""),
        album_url=pending_data.get("referer", link),
        product_name=product_name,
        seller=meta.get("seller", {}).get("name", "") if isinstance(meta.get("seller"), dict) else "",
        platform=meta.get("platform", ""),
        source="discord_contact_sheet"
    )


@client.event
async def on_raw_reaction_add(payload):
    """
    Handle raw reaction add events.
    Checks if user reacted with ✅ on an Auto-Matcher card to merge outfits.
    """
    # Only process reactions in the review channel
    review_channel_id = os.getenv("DISCORD_REVIEW_CHANNEL", "")
    if not review_channel_id or str(payload.channel_id) != str(review_channel_id):
        return
        
    # Ignore bot's own reactions
    if payload.user_id == client.user.id:
        return
        
    # We only care about ✅ approvals
    if str(payload.emoji) != "✅":
        return
        
    channel = client.get_channel(payload.channel_id)
    if not channel:
        try:
            channel = await client.fetch_channel(payload.channel_id)
        except Exception:
            return
            
    try:
        message = await channel.fetch_message(payload.message_id)
    except Exception:
        return
        
    # Check if this message was sent by the bot and has embeds
    if message.author != client.user or not message.embeds:
        return
        
    embed = message.embeds[0]
    footer_text = embed.footer.text if embed.footer else ""
    
    if not footer_text or "Pair ID: " not in footer_text:
        return
        
    try:
        pair_id = footer_text.split("Pair ID: ")[1].split(" | ")[0].strip()
        parts = pair_id.split("_x_")
        if len(parts) != 2:
            return
            
        folder_a_name, folder_b_name = parts[0], parts[1]
        
        # Load item details
        folder_a = MANUAL_CURATION_DIR / folder_a_name
        folder_b = MANUAL_CURATION_DIR / folder_b_name
        
        if not folder_a.exists() or not folder_b.exists():
            await message.reply("⚠️ **Could not merge:** One of the original product folders has already been deleted or generated.")
            return
            
        # Send processing message
        processing_msg = await message.reply("⏳ **Merging outfit pieces and copying assets...**")
        
        # Call Auto-Matcher's merge function
        from auto_matcher import create_merged_folder
        
        # Load metadata and tags for both to pass to create_merged_folder
        def load_tags_or_meta(folder):
            tags_file = folder / "style_tags.json"
            meta_file = folder / "metadata.json"
            tags = {}
            if tags_file.exists():
                try:
                    tags.update(json.loads(tags_file.read_text(encoding="utf-8")))
                except Exception: pass
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    tags.setdefault("product_name", meta.get("product_name", folder.name))
                    tags.setdefault("category", meta.get("category", "top"))
                except Exception: pass
            tags["folder_path"] = str(folder)
            tags["folder_name"] = folder.name
            return tags
            
        item_a = load_tags_or_meta(folder_a)
        item_b = load_tags_or_meta(folder_b)
        
        # Create the merged folder
        merged_folder = create_merged_folder(item_a, item_b)
        
        # Delete original folders to prevent double-generation of individual items
        import shutil
        shutil.rmtree(folder_a, ignore_errors=True)
        shutil.rmtree(folder_b, ignore_errors=True)
        
        # Update confirmation message
        await processing_msg.edit(
            content=(
                f"🎨 **Outfit Merged successfully!**\n"
                f"Combined **{item_a.get('product_name', folder_a_name)}** and **{item_b.get('product_name', folder_b_name)}** into a single set.\n"
                f"Unified campaign queued for generation: `{merged_folder.name}`"
            )
        )
        
        # Swap reaction to show processed status
        try:
            await message.remove_reaction("📋", client.user)
        except Exception: pass
        await message.add_reaction("✅")
        
    except Exception as e:
        print(f"[!] Error in reaction merge: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("[!] DISCORD_TOKEN is missing from your .env file!")
    else:
        client.run(DISCORD_TOKEN)
