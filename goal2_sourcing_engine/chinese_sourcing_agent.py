import os

import sys

import json

import re

import asyncio

import uuid

import base64

from datetime import datetime

import urllib.parse

from playwright.async_api import async_playwright

from bs4 import BeautifulSoup



try:

    from litellm_router import shared_router

except ImportError:

    shared_router = None



# Force UTF-8 stdout/stderr on Windows to prevent cp1252 charmap encoding errors

if sys.platform.startswith("win"):

    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')



# Safe print for Windows (fallback wrapper)

def safe_print(msg: str):

    print(msg, flush=True)





def parse_item_id(url: str, platform: str) -> str:

    """

    Extract the platform-specific item/product ID from a URL.

    Used for deduplication and reordering.

    

    Examples:

      Weidian:  https://weidian.com/item.html?itemID=7543891234 → "7543891234"

      1688:     https://detail.1688.com/offer/756321456789.html → "756321456789"

      Taobao:   https://item.taobao.com/item.htm?id=789456123    → "789456123"

    """

    parsed = urllib.parse.urlparse(url)

    params = urllib.parse.parse_qs(parsed.query)

    

    if platform == "weidian":

        # Weidian uses itemID or itemId in query params

        item_id = params.get("itemID", params.get("itemId", params.get("itemid", [None])))[0]

        if item_id:

            return item_id

        # Some Weidian URLs use path format: /item/p/XXXXXXXXXX

        path_match = re.search(r'/item/p/(\d+)', parsed.path)

        if path_match:

            return path_match.group(1)

    elif platform == "1688":

        # 1688 uses /offer/XXXXXXXXXX.html in path

        path_match = re.search(r'/offer/(\d+)', parsed.path)

        if path_match:

            return path_match.group(1)

    elif platform == "taobao":

        # Taobao uses id= in query params

        item_id = params.get("id", [None])[0]

        if item_id:

            return item_id

    

    # Fallback: hash the URL

    import hashlib

    return hashlib.md5(url.encode()).hexdigest()[:12]





def parse_price_float(price_str: str) -> float:

    """

    Parse a price string into a float. Handles:

    - "189" → 189.0

    - "¥189" → 189.0

    - "189-239" → 189.0 (takes the lower bound)

    - "Check link" → 0.0

    """

    if not price_str or price_str == "Check link":

        return 0.0

    # Remove currency symbols and whitespace

    cleaned = re.sub(r'[¥￥$€£\s]', '', str(price_str))

    # Handle price ranges (take lower bound)

    if '-' in cleaned:

        cleaned = cleaned.split('-')[0]

    try:

        return float(cleaned)

    except (ValueError, TypeError):

        return 0.0





class ChineseSourcingAgent:

    def __init__(self, headless: bool = True):

        self.headless = headless



    async def scrape_product(self, url: str, generate_contact_sheet: bool = False, max_retries: int = 3):

        """

        Scrape a Chinese marketplace product page and extract ALL available data.

        

        Supports: Weidian, 1688, Taobao

        

        Returns:

          - If generate_contact_sheet=True: dict with metadata, sheets, url_mapping

          - If generate_contact_sheet=False: True/False based on success

          - False on failure

        """

        safe_print(f"[*] Starting scrape for: {url} (contact_sheet={generate_contact_sheet})")

        parsed_url = urllib.parse.urlparse(url)

        domain = parsed_url.netloc.replace("www.", "")

        

        # Determine platform

        platform = "unknown"

        if "weidian" in domain or "youshop" in domain:

            platform = "weidian"

        elif "1688" in domain:

            platform = "1688"

        elif "taobao" in domain or "tmall" in domain:

            platform = "taobao"

            

        safe_print(f"[*] Detected platform: {platform.upper()}")

        

        # Parse item ID for deduplication

        item_id = parse_item_id(url, platform)

        safe_print(f"[*] Item ID: {item_id}")

        

        # Retry loop with exponential backoff

        last_error = None

        for attempt in range(1, max_retries + 1):

            try:

                result = await self._do_scrape(url, platform, item_id, generate_contact_sheet, attempt)

                if result is not False:

                    return result

                # If _do_scrape returned False (login/captcha), retry with backoff

                if attempt < max_retries:

                    wait_time = 2 ** attempt  # 2s, 4s, 8s

                    safe_print(f"[!] Attempt {attempt}/{max_retries} failed. Retrying in {wait_time}s...")

                    await asyncio.sleep(wait_time)

                    last_error = "Login/CAPTCHA wall detected"

            except Exception as e:

                last_error = str(e)

                safe_print(f"[!] Attempt {attempt}/{max_retries} error: {e}")

                if attempt < max_retries:

                    wait_time = 2 ** attempt

                    safe_print(f"[!] Retrying in {wait_time}s...")

                    await asyncio.sleep(wait_time)

        

        safe_print(f"[!] All {max_retries} attempts failed. Last error: {last_error}")

        return False



    async def _do_scrape(self, url: str, platform: str, item_id: str, generate_contact_sheet: bool, attempt: int):

        """Internal scrape logic for a single attempt."""

        

        async with async_playwright() as p:

            # Configure viewport/user agent based on platform

            # Weidian is mobile-first, mobile user-agent works best

            is_mobile = (platform == "weidian")

            

            safe_print(f"[*] Launching ephemeral Playwright browser (attempt {attempt})")

            

            browser = await p.chromium.launch(

                headless=self.headless,

                args=[

                    "--disable-blink-features=AutomationControlled",

                    "--no-sandbox",

                    "--disable-dev-shm-usage",

                    "--disable-web-security",

                    "--allow-running-insecure-content"

                ]

            )

            

            if is_mobile:

                # Emulate iPhone 12

                device = p.devices["iPhone 12"]

                context = await browser.new_context(**device)

            else:

                context = await browser.new_context(

                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",

                    viewport={"width": 1280, "height": 800}

                )

                

            page = await context.new_page()

            # Bypass headless detection

            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            

            # Set stealth scripts/headers

            await page.set_extra_http_headers({"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})

            

            try:

                # Go to the product page

                safe_print(f"[*] Navigating to {url}...")

                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                await asyncio.sleep(3.0)  # Initial wait for JS rendering

                

                # ── PHASE 1B: Progressive scrolling to trigger lazy-loaded images ──

                safe_print("[*] Scrolling page to load all images...")

                for scroll_step in range(6):

                    await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(scroll_step + 1) / 6})")

                    await asyncio.sleep(0.8)

                # Scroll back to top

                await page.evaluate("window.scrollTo(0, 0)")

                await asyncio.sleep(1.0)

                

                # Check for login redirection

                current_url = page.url

                if "login" in current_url or "login.taobao.com" in current_url:

                    safe_print("[!] Scraper redirected to Login page. Sourcing blocked by authentication wall.")

                    await context.close()

                    await browser.close()

                    return False

                    

                content = await page.content()

                if "rgv587" in content or "punish" in content:

                    safe_print("[!] Scraper blocked by CAPTCHA/Punish wall.")

                    await context.close()

                    await browser.close()

                    return False

                

                # ══════════════════════════════════════════════════════════════

                # DYNAMIC VARIANT DRAWER INTERACTION

                # ══════════════════════════════════════════════════════════════

                drawer_opened = False

                sku_selectors = [

                    ".sku-button", ".sku-title", ".select-sku", ".goods-sku", 

                    ".sku-selector", "[class*='sku']", "[class*='spec']", 

                    "text=选择", "text=Select", "text=规格"

                ]

                img_urls = []

                python_stock_status = {}

                

                for sel in sku_selectors:

                    try:

                        locator = page.locator(sel).first

                        if await locator.is_visible():

                            await locator.click(timeout=3000)

                            safe_print(f"[+] Opened SKU/variant selector drawer using: {sel}")

                            await asyncio.sleep(2.0)

                            drawer_opened = True

                            break

                    except Exception:

                        continue



                # If drawer opened, click color options sequentially to load variant images

                if drawer_opened:

                    try:

                        sku_rows = await page.query_selector_all(".sku-row")

                        if sku_rows:

                            color_items = await sku_rows[0].query_selector_all(".sku-item, li, span, button")

                            safe_print(f"[+] Found {len(color_items)} variant option elements in first SKU row.")

                            

                            for c_idx, item in enumerate(color_items):

                                try:

                                    item_text = await item.inner_text()

                                    item_text = item_text.strip()

                                    if not item_text or len(item_text) > 40:

                                        continue

                                    

                                    # Click to select color variant

                                    safe_print(f"  [*] Selecting variant option: '{item_text}' to load variant images...")

                                    await item.click(timeout=2000)

                                    await asyncio.sleep(1.5)

                                    

                                    # Read sizes row to check stock status

                                    sku_rows_el = await page.query_selector_all(".sku-row")

                                    if len(sku_rows_el) > 1:

                                        size_items = await sku_rows_el[1].query_selector_all(".sku-item, li, span, button")

                                        for sz_el in size_items:

                                            sz_text = await sz_el.inner_text()

                                            sz_text = sz_text.strip()

                                            if not sz_text:

                                                continue

                                            

                                            # Clean up size text for key

                                            sz_clean = re.sub(r'码|\s*[\(（].*?[\)）]', '', sz_text).strip()

                                            sz_clean = sz_clean.replace("Size ", "").replace("size ", "").strip()

                                            

                                            # Check if disabled

                                            classes = await sz_el.get_attribute("class") or ""

                                            aria_disabled = await sz_el.get_attribute("aria-disabled") or ""

                                            is_out_of_stock = "disable" in classes.lower() or "disabled" in classes.lower() or aria_disabled.lower() == "true"

                                            

                                            # Map English names if possible

                                            en_color = item_text

                                            if "黑" in item_text: en_color = "Black"

                                            elif "白" in item_text: en_color = "White"

                                            elif "灰" in item_text: en_color = "Grey"

                                            elif "蓝" in item_text: en_color = "Blue"

                                            elif "红" in item_text: en_color = "Red"

                                            elif "绿" in item_text: en_color = "Green"

                                            elif "粉" in item_text: en_color = "Pink"

                                            

                                            stock_key = f"{en_color}-{sz_clean}"

                                            python_stock_status[stock_key] = not is_out_of_stock

                                    

                                    # Harvest images loaded for this color variant

                                    temp_content = await page.content()

                                    temp_soup = BeautifulSoup(temp_content, "html.parser")

                                    

                                    for img in temp_soup.find_all("img"):

                                        src = img.get("src") or img.get("data-src") or img.get("original-src")

                                        if src and ("weidian" in src or "wdwdimg" in src or "geilicdn" in src) and not src.endswith(".gif"):

                                            if src.startswith("//"):

                                                src = "https:" + src

                                            if "geilicdn" in src and "?" in src:

                                                src = src.split("?")[0]

                                            src = re.sub(r'[?&]imageView2?/\d+/w/\d+.*$', '', src)

                                            if src not in img_urls:

                                                img_urls.append(src)

                                                safe_print(f"    [+] Sourced variant image: {src[:60]}...")

                                except Exception as e_click:

                                    safe_print(f"    [!] Failed to click color option: {e_click}")

                            

                            # Handle single row stock status (no color, just sizes)

                            if len(sku_rows) == 1:

                                size_items = await sku_rows[0].query_selector_all(".sku-item, li, span, button")

                                for sz_el in size_items:

                                    sz_text = await sz_el.inner_text()

                                    sz_text = sz_text.strip()

                                    if not sz_text:

                                        continue

                                    sz_clean = re.sub(r'码|\s*[\(（].*?[\)）]', '', sz_text).strip()

                                    sz_clean = sz_clean.replace("Size ", "").replace("size ", "").strip()

                                    classes = await sz_el.get_attribute("class") or ""

                                    aria_disabled = await sz_el.get_attribute("aria-disabled") or ""

                                    is_out_of_stock = "disable" in classes.lower() or "disabled" in classes.lower() or aria_disabled.lower() == "true"

                                    python_stock_status[f"Default-{sz_clean}"] = not is_out_of_stock

                    except Exception as e_drawer:

                        safe_print(f"    [!] Error clicking variant options: {e_drawer}")



                # Regenerate content and soup so the open drawer text is visible to BeautifulSoup and Gemini LLM

                content = await page.content()

                soup = BeautifulSoup(content, "html.parser")

                

                # ── Python/BeautifulSoup option extraction fallback (for sizes and colors) ──

                python_colors = []

                python_sizes = []

                try:

                    sku_rows = soup.find_all("div", class_="sku-row")

                    for r_idx, row in enumerate(sku_rows):

                        row_title_el = row.find(class_=re.compile("title|row-title|header"))

                        row_title = row_title_el.get_text().lower() if row_title_el else ""

                        

                        items = row.find_all(class_=re.compile("sku-item|item"))

                        item_list = []

                        for item in items:

                            txt = item.get_text().strip()

                            txt_clean = re.sub(r'\s*[\(（].*?[\)）]', '', txt).strip()

                            if txt_clean and txt_clean not in item_list:

                                item_list.append(txt_clean)

                                

                        is_size_row = "尺码" in row_title or "size" in row_title or "yard" in row_title or "规格" in row_title or "尺寸" in row_title

                        if not is_size_row and item_list:

                            # Heuristic: check if options look like sizes (letters or numbers like 26-48)

                            size_like_cnt = 0

                            for item_val in item_list:

                                val_lower = item_val.lower()

                                val_clean = re.sub(r'码|\s*[\(（].*?[\)）]', '', val_lower).strip()

                                # Check if it's a numeric range common in clothing/shoes

                                num_match = re.search(r'\b(2[6-9]|3[0-9]|4[0-8])\b', val_clean)

                                is_letter = val_clean in ["s", "m", "l", "xl", "xxl", "xxxl", "2xl", "3xl", "4xl", "xs"]

                                if num_match or is_letter:

                                    size_like_cnt += 1

                            if size_like_cnt / len(item_list) > 0.5:

                                is_size_row = True

                                

                        if is_size_row:

                            python_sizes.extend(item_list)

                        else:

                            python_colors.extend(item_list)

                    safe_print(f"[+] Python option parser found sizes: {python_sizes} | colors: {python_colors}")

                except Exception as e_parse:

                    safe_print(f"[!] Error parsing options in Python fallback: {e_parse}")

                

                # ══════════════════════════════════════════════════════════════

                # INITIALIZE ALL FIELDS — These are the complete product data

                # ══════════════════════════════════════════════════════════════

                title = ""

                price = "Check link"

                price_float = 0.0

                colors = ["default"]

                sizes = []

                description = ""

                variant_mappings = {"colors": {}, "sizes": {}}

                

                # ── PHASE 1A: New extended fields ──

                material = ""

                weight_gsm = 0

                measurements = {}     # e.g. {"S": {"shoulder": 52, "chest": 112, ...}, ...}

                seller_name = ""

                seller_rating = 0.0

                sales_volume = 0

                shipping_origin = ""

                shipping_cost_cny = 0.0

                stock_status = {}     # e.g. {"Black-S": True, "Black-M": False, ...}

                brand_name = ""

                product_category = ""

                care_instructions = ""

                model_info = ""

                

                # ══════════════════════════════════════════════════════════════

                # LLM EXTRACTION — Extract ALL product data via Gemini

                # ══════════════════════════════════════════════════════════════

                if shared_router:

                    try:

                        safe_print("[*] Extracting and translating ALL product details via Gemini...")

                        page_text = await page.evaluate("() => document.body.innerText")

                        prompt = f"Page Text Content:\n{page_text[:120000]}"

                        system_instr = (

                            "You are an expert Chinese fashion sourcing assistant. Your job is to extract EVERY SINGLE "

                            "piece of product information from a Chinese marketplace page (Weidian, Taobao, or 1688).\n"

                            "Translate ALL Chinese text into clean, natural English.\n"

                            "Do not guess or assume. Only extract data that is clearly visible in the text.\n"

                            "For measurements, convert Chinese units if needed (1寸 ≈ 3.33cm).\n"

                            "Output ONLY a valid JSON object matching this schema:\n"

                            "{\n"

                            '  "product_name": "translated english product name",\n'

                            '  "price": "CNY price amount (just the number, e.g. 189)",\n'

                            '  "description": "translated product description (2-4 sentences, include key selling points)",\n'

                            '  "material": "fabric composition and weight (e.g. 100% Cotton, 380gsm Heavyweight French Terry)",\n'

                            '  "weight_gsm": 380,\n'

                            '  "care_instructions": "translated care/wash instructions if listed",\n'

                            '  "model_info": "model measurements if listed (e.g. Model is 180cm/72kg wearing size L)",\n'

                            '  "brand_name": "brand name if mentioned, empty string if unbranded",\n'

                            '  "product_category": "one of: hoodie, t-shirt, sweatshirt, jacket, coat, pants, shorts, jeans, shoes, bag, hat, accessory, set",\n'

                            '  "seller_name": "shop/store name if visible",\n'

                            '  "seller_rating": 4.8,\n'

                            '  "sales_volume": 12400,\n'

                            '  "shipping_origin": "province/city if listed (e.g. Guangdong)",\n'

                            '  "shipping_cost_cny": 8,\n'

                            '  "variant_mappings": {\n'

                            '    "colors": {\n'

                            '      "Clean English Color (e.g. Black)": "Exact original Chinese color option text as it appears on the page (e.g. 黑色 (水洗加绒))",\n'

                            '      "Clean English Color (e.g. Cream)": "Exact original Chinese color option text as it appears on the page (e.g. 米白色)"\n'

                            '    },\n'

                            '    "sizes": {\n'

                            '      "Clean English Size (e.g. L)": "Exact original Chinese size option text as it appears on the page (e.g. L码 (建议130-150斤))",\n'

                            '      "Clean English Size (e.g. M)": "Exact original Chinese size option text as it appears on the page (e.g. M码)"\n'

                            '    }\n'

                            '  },\n'

                            '  "measurements": {\n'

                            '    "S": {"shoulder_cm": 52, "chest_cm": 112, "length_cm": 68, "sleeve_cm": 56},\n'

                            '    "M": {"shoulder_cm": 54, "chest_cm": 116, "length_cm": 70, "sleeve_cm": 58}\n'

                            '  },\n'

                            '  "stock_status": {\n'

                            '    "Color-Size": true,\n'

                            '    "Black-S": true,\n'

                            '    "Black-M": false\n'

                            '  }\n'

                            "}\n"

                            "IMPORTANT RULES:\n"

                            "- PREMIUM STREETWEAR NAMING RULE (Tugoslook Style): If the Chinese product name contains replicas of major designer brands (such as Yeezy, Gap, Nike, Travis Scott, Off-White, Jordan, Balenciaga, Essentials, Chrome Hearts, Cole Buxton, Represent, Arc'teryx), DO NOT use those brand names in the extracted 'product_name'. Instead, translate it into a premium-sounding independent streetwear brand product name. Choose an elegant, street-style aesthetic name using words like: Obsidian, Void, Phantom, Alcatraz, Carbon, Sand, Sage, Dust, Clay, Earth, Fade, Weathered, Heavyweight, Boxy, Dropped, Archival, Slub, Oversized. For example, instead of 'Yeezy Gap Balenciaga Hoodie' use 'Void Heavyweight Drop-Shoulder Hoodie', and instead of 'Off-White Dunk Sneaker' use 'Phantom Retro Court Lows'. Make it sound high-end, premium, and professional.\n"

                            "- For measurements: return ALL sizes listed. Use keys like shoulder_cm, chest_cm, length_cm, sleeve_cm, waist_cm, hip_cm.\n"

                            "- For stock_status: only include if stock info is clearly visible. Use format 'Color-Size' as keys.\n"

                            "- For weight_gsm: extract the fabric weight in grams per square meter if mentioned (e.g. 380g, 380gsm, 380克).\n"

                            "- For price: return ONLY the numeric value, no currency symbols.\n"

                            "- For seller_rating: return as a float (e.g. 4.8).\n"

                            "- For sales_volume: return as an integer (e.g. 12400).\n"

                            "- If a field is not found on the page, use empty string for strings, 0 for numbers, empty object for objects.\n"

                        )

                        response = await shared_router.get_chat_completion(

                            messages=[{"role": "user", "content": prompt}],

                            primary_model="gemini-lite",

                            system_instruction=system_instr,

                            temperature=0.2,

                            response_format={"type": "json_object"}

                        )

                        result_text = response.choices[0].message.content.strip()

                        extracted = json.loads(result_text)

                        

                        # ── Core fields ──

                        title = extracted.get("product_name", "").strip()

                        price = extracted.get("price", "").strip()

                        price_float = parse_price_float(price)

                        description = extracted.get("description", "").strip()

                        variant_mappings = extracted.get("variant_mappings", {"colors": {}, "sizes": {}})

                        

                        # ── Extended fields (Phase 1A) ──

                        material = extracted.get("material", "").strip()

                        weight_gsm = int(extracted.get("weight_gsm", 0) or 0)

                        measurements = extracted.get("measurements", {})

                        seller_name = extracted.get("seller_name", "").strip()

                        seller_rating = float(extracted.get("seller_rating", 0) or 0)

                        sales_volume = int(extracted.get("sales_volume", 0) or 0)

                        shipping_origin = extracted.get("shipping_origin", "").strip()

                        shipping_cost_cny = float(extracted.get("shipping_cost_cny", 0) or 0)

                        stock_status = extracted.get("stock_status", {})

                        brand_name = extracted.get("brand_name", "").strip()

                        product_category = extracted.get("product_category", "").strip()

                        care_instructions = extracted.get("care_instructions", "").strip()

                        model_info = extracted.get("model_info", "").strip()

                        

                        # ── Derive color/size lists from variant mappings ──

                        if variant_mappings.get("colors"):

                            colors = list(variant_mappings["colors"].keys())

                        else:

                            colors = extracted.get("colors", ["default"])

                            

                        if variant_mappings.get("sizes"):

                            sizes = list(variant_mappings["sizes"].keys())

                        else:

                            sizes = extracted.get("sizes", [])



                        # ── Merge Python-scraped options to handle LLM gaps ──

                        if python_colors:

                            if "colors" not in variant_mappings:

                                variant_mappings["colors"] = {}

                            for col in python_colors:

                                col_clean = re.sub(r'\s*[\(（].*?[\)）]', '', col).strip()

                                # Check if color is already in variant mappings values

                                if col_clean not in colors and col_clean not in variant_mappings["colors"].values():

                                    # Fallback simple translation or direct map

                                    en_color = col_clean

                                    if "黑" in col_clean: en_color = "Black"

                                    elif "白" in col_clean: en_color = "White"

                                    elif "灰" in col_clean: en_color = "Grey"

                                    elif "蓝" in col_clean: en_color = "Blue"

                                    elif "红" in col_clean: en_color = "Red"

                                    elif "绿" in col_clean: en_color = "Green"

                                    elif "粉" in col_clean: en_color = "Pink"

                                    

                                    # Handle duplicate English keys

                                    orig_en = en_color

                                    dup_cnt = 1

                                    while en_color in colors:

                                        en_color = f"{orig_en} {dup_cnt}"

                                        dup_cnt += 1

                                        

                                    colors.append(en_color)

                                    variant_mappings["colors"][en_color] = col_clean



                        if python_sizes:

                            if "sizes" not in variant_mappings:

                                variant_mappings["sizes"] = {}

                            for sz in python_sizes:

                                sz_clean = re.sub(r'码|\s*[\(（].*?[\)）]', '', sz).strip()

                                sz_clean = sz_clean.replace("Size ", "").replace("size ", "").strip()

                                if sz_clean not in sizes:

                                    sizes.append(sz_clean)

                                if sz_clean not in variant_mappings["sizes"]:

                                    variant_mappings["sizes"][sz_clean] = sz



                        # ── Merge Python-scraped stock status ──

                        if python_stock_status:

                            if "stock_status" not in extracted or not isinstance(stock_status, dict):

                                stock_status = {}

                            for key, val in python_stock_status.items():

                                stock_status[key] = val

                        

                        safe_print(f"[+] LLM Extracted Title: {title}")

                        safe_print(f"[+] LLM Extracted Price: ¥{price}")

                        safe_print(f"[+] LLM Extracted Colors: {colors}")

                        safe_print(f"[+] LLM Extracted Sizes: {sizes}")

                        safe_print(f"[+] LLM Extracted Material: {material}")

                        safe_print(f"[+] LLM Extracted Weight: {weight_gsm}gsm")

                        safe_print(f"[+] LLM Extracted Category: {product_category}")

                        safe_print(f"[+] LLM Extracted Seller: {seller_name} (⭐{seller_rating}, {sales_volume} sales)")

                        safe_print(f"[+] LLM Extracted Measurements: {len(measurements)} sizes")

                        safe_print(f"[+] LLM Extracted Variant Mappings: {variant_mappings}")

                    except Exception as le:

                        safe_print(f"[!] LLM Extraction failed, falling back to BeautifulSoup: {le}")

                

                # ══════════════════════════════════════════════════════════════

                # BEAUTIFULSOUP FALLBACK — Title, Price, Images (per platform)

                # ══════════════════════════════════════════════════════════════

                if platform == "weidian":

                    # Title

                    if not title:

                        title_el = soup.find("div", class_=re.compile(r"goods-title|item-title|title")) or soup.find("h1")

                        title = title_el.get_text().strip() if title_el else "Weidian Product"

                    

                    # Price

                    if price == "Check link" or not price:

                        price_el = soup.find("span", class_=re.compile(r"price|goods-price|item-price"))

                        price = price_el.get_text().strip() if price_el else "Check link"

                        price_float = parse_price_float(price)

                    

                    # Images — Weidian CDN domains

                    for img in soup.find_all("img"):

                        src = img.get("src") or img.get("data-src") or img.get("original-src")

                        if src and ("weidian" in src or "wdwdimg" in src or "wdimg" in src or "geilicdn" in src) and not src.endswith(".gif"):

                            if src.startswith("//"):

                                src = "https:" + src

                            if "geilicdn" in src and "?" in src:

                                src = src.split("?")[0]

                            # Try to get full-res by removing dimension params

                            src = re.sub(r'[?&]imageView2?/\d+/w/\d+.*$', '', src)

                            if src not in img_urls:

                                img_urls.append(src)

                                

                elif platform == "1688":

                    # Title

                    if not title:

                        title_el = soup.find("h1", class_=re.compile(r"title|d-title")) or soup.find("div", class_=re.compile(r"title|d-title"))

                        title = title_el.get_text().strip() if title_el else "1688 Product"

                    

                    # Price

                    if price == "Check link" or not price:

                        price_el = soup.find("span", class_=re.compile(r"price|discount-price")) or soup.find("div", class_=re.compile(r"price"))

                        price = price_el.get_text().strip() if price_el else "Check link"

                        price_float = parse_price_float(price)

                    

                    # Images — Alibaba CDN domains

                    for img in soup.find_all("img"):

                        src = img.get("src") or img.get("data-src") or img.get("lazy-src")

                        if src and ("cbu01" in src or "alicdn" in src) and not src.endswith(".gif") and "summ" not in src:

                            if src.startswith("//"):

                                src = "https:" + src

                            # Clean dimensions to get high-res images

                            src = re.sub(r'_\d+x\d+.*$', '', src)

                            if src not in img_urls:

                                img_urls.append(src)

                                

                elif platform == "taobao":

                    # Title

                    if not title:

                        title_el = soup.find("h3", class_=re.compile(r"main-title|title")) or soup.find("h1")

                        title = title_el.get_text().strip() if title_el else "Taobao Product"

                    

                    # Price

                    if price == "Check link" or not price:

                        price_el = soup.find("em", class_=re.compile(r"tb-promo-price|price")) or soup.find("span", class_=re.compile(r"price"))

                        price = price_el.get_text().strip() if price_el else "Check link"

                        price_float = parse_price_float(price)

                    

                    # Images — Taobao/Alibaba CDN

                    for img in soup.find_all("img"):

                        src = img.get("src") or img.get("data-src")

                        if src and ("alicdn" in src or "taobao" in src) and not src.endswith(".gif") and "sum" not in src:

                            if src.startswith("//"):

                                src = "https:" + src

                            src = re.sub(r'_\d+x\d+.*$', '', src)

                            if src not in img_urls:

                                img_urls.append(src)

                

                # ── PHASE 1D: Extract description section images (measurement diagrams, fabric close-ups) ──

                # Chinese product pages embed the most detailed images in the long description HTML

                desc_containers = soup.find_all("div", class_=re.compile(r"desc|detail|content|info-detail", re.IGNORECASE))

                desc_img_count = 0

                for container in desc_containers:

                    for img in container.find_all("img"):

                        src = img.get("src") or img.get("data-src") or img.get("data-lazyload")

                        if src and not src.endswith(".gif") and len(src) > 15:

                            if src.startswith("//"):

                                src = "https:" + src

                            # Clean dimension suffixes for full-res

                            src = re.sub(r'_\d+x\d+.*$', '', src)

                            if "geilicdn" in src and "?" in src:

                                src = src.split("?")[0]

                            if src not in img_urls:

                                img_urls.append(src)

                                desc_img_count += 1

                if desc_img_count:

                    safe_print(f"[+] Found {desc_img_count} additional images from description section")

                                

                # Clean up title for folder name

                title_clean = re.sub(r'[^\w\s-]', '', title.lower().strip())

                title_clean = re.sub(r'[\s_]+', '-', title_clean)

                if not title_clean:

                    title_clean = "product"

                

                # ── PHASE 1E: Use item_id in folder name to prevent collisions ──

                folder_name = f"brand_{platform}_{title_clean[:40]}_{item_id}"

                

                # Setup staging folder or temp thumbnail folder

                base_dir = os.path.dirname(os.path.abspath(__file__))

                target_root = os.path.join(base_dir, "input_sourcing")

                os.makedirs(target_root, exist_ok=True)

                

                if generate_contact_sheet:

                    product_dir = os.path.join(target_root, f"_thumbs_{uuid.uuid4().hex[:8]}")

                else:

                    product_dir = os.path.join(target_root, folder_name)

                    

                os.makedirs(product_dir, exist_ok=True)

                

                safe_print(f"[+] Product Title: {title}")

                safe_print(f"[+] Price: ¥{price} (${price_float / 7.2:.2f} USD)" if price_float > 0 else f"[+] Price: {price}")

                safe_print(f"[+] Sourced {len(img_urls)} product images.")

                

                # If we couldn't get any images from the parse, try to grab whatever large images are visible on page

                if not img_urls:

                    safe_print("[-] Direct parsing found no images. Extracting all unique large images...")

                    for img in soup.find_all("img"):

                        src = img.get("src") or img.get("data-src")

                        if src and not src.endswith(".gif") and len(src) > 15:

                            if src.startswith("//"):

                                src = "https:" + src

                            if "geilicdn" in src and "?" in src:

                                src = src.split("?")[0]

                            if src not in img_urls:

                                img_urls.append(src)

                

                # ── PHASE 1C: Increased image limits (15→40 contact sheet, 10→20 direct) ──

                max_imgs = 40 if generate_contact_sheet else 20

                img_urls = img_urls[:max_imgs]

                

                saved_count = 0

                thumb_paths = []

                # Download images using Playwright's page fetch to reuse cookies/session

                for idx, img_url in enumerate(img_urls):

                    safe_print(f"  [-] Fetching image {idx+1}/{len(img_urls)}: {img_url[:80]}...")

                    try:

                        # Fetch the image in browser context

                        response = await page.evaluate(f"""

                            async (url) => {{

                                const res = await fetch(url);

                                const blob = await res.blob();

                                return new Promise((resolve) => {{

                                    const reader = new FileReader();

                                    reader.onloadend = () => resolve(reader.result);

                                    reader.readAsDataURL(blob);

                                }});

                            }}

                        """, img_url)

                        

                        if response and response.startswith("data:image"):

                            # Convert base64 back to binary data

                            header, base64_data = response.split(",", 1)

                            img_data = base64.b64decode(base64_data)

                            

                            # Skip tiny images (icons, spacers) — minimum 5KB

                            if len(img_data) < 5120:

                                safe_print(f"      [SKIP] Too small ({len(img_data)} bytes)")

                                continue

                            

                            file_name = f"angle_{idx+1}.jpg"

                            file_path = os.path.join(product_dir, file_name)

                            with open(file_path, "wb") as f:

                                f.write(img_data)

                            saved_count += 1

                            thumb_paths.append(file_path)

                            safe_print(f"      [SAVED] {file_name} ({len(img_data) / 1024:.0f}KB)")

                    except Exception as e:

                        safe_print(f"      [!] Failed to download image: {e}")

                

                # ══════════════════════════════════════════════════════════════

                # BUILD COMPLETE METADATA — Single source of truth for pipeline

                # ══════════════════════════════════════════════════════════════

                metadata = {

                    # ── Core identification ──

                    "product_name": title,

                    "item_id": item_id,

                    "platform": platform,

                    "link": url,

                    

                    # ── Pricing ──

                    "price_string": price,

                    "price_cny": price_float,

                    

                    # ── Variants ──

                    "colors": colors,

                    "sizes": sizes,

                    "variant_mappings": variant_mappings,

                    "stock_status": stock_status,

                    

                    # ── Product details ──

                    "description": description or title,

                    "material": material,

                    "weight_gsm": weight_gsm,

                    "product_category": product_category,

                    "brand_name": brand_name,

                    "care_instructions": care_instructions,

                    "model_info": model_info,

                    

                    # ── Measurements (size chart data) ──

                    "measurements": measurements,

                    

                    # ── Seller info ──

                    "seller": {

                        "name": seller_name,

                        "rating": seller_rating,

                        "sales_volume": sales_volume,

                        "shipping_origin": shipping_origin,

                        "domestic_shipping_cny": shipping_cost_cny

                    },

                    

                    # ── Meta ──

                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

                    "source": f"chinese_sourcing_agent_{platform}",

                    "author": "autonomous_sourcer",

                    "image_count": saved_count,

                    

                    # ── Pipeline status ──

                    "generation_status": "pending",

                    "storefront_status": "not_listed",

                    "storefront_product_id": None

                }

                

                # Expose metadata as an attribute for the discord bot to read

                self.last_metadata = metadata

                

                if generate_contact_sheet:

                    # Create contact sheets

                    from sourcing_utils import create_contact_sheets

                    contact_sheets = create_contact_sheets(thumb_paths)

                    

                    # Clean up temp thumbnail images & directory

                    import shutil

                    shutil.rmtree(product_dir, ignore_errors=True)

                    

                    safe_print(f"\n[OK] Sourced {platform.upper()} Product. Created {len(contact_sheets)} contact sheets ({saved_count} images).\n")

                    

                    await context.close()

                    await browser.close()

                    

                    return {

                        "metadata": metadata,

                        "sheets": contact_sheets,

                        "url_mapping": {str(i+1): url for i, url in enumerate(img_urls)}

                    }

                else:

                    with open(os.path.join(product_dir, "metadata.json"), "w", encoding="utf-8") as f:

                        json.dump(metadata, f, indent=2, ensure_ascii=False)

                        

                    with open(os.path.join(product_dir, "link.txt"), "w", encoding="utf-8") as f:

                        f.write(url)

                        

                    safe_print(f"\n[OK] Sourced {platform.upper()} Product. Grouped {saved_count} images in {folder_name}\n")

                    

                    await context.close()

                    await browser.close()

                    return saved_count > 0

                

            except Exception as e:

                safe_print(f"[!] Scrape Error: {e}")

                try:

                    await context.close()

                except:

                    pass

                try:

                    await browser.close()

                except:

                    pass

                raise  # Re-raise so retry loop can catch it





async def main():

    if len(sys.argv) < 2:

        safe_print("==================================================")

        safe_print("CHINESE PLATFORM DIRECT SOURCING AGENT")

        safe_print("==================================================")

        safe_print("Usage: python chinese_sourcing_agent.py [weidian/1688/taobao_url]")

        safe_print("Example: python chinese_sourcing_agent.py https://weidian.com/item.html?itemID=5876239121")

        return

        

    url = sys.argv[1]

    agent = ChineseSourcingAgent(headless=True)

    result = await agent.scrape_product(url)

    if result and isinstance(result, dict):

        safe_print(f"\n{'='*60}")

        safe_print("EXTRACTION SUMMARY")

        safe_print(f"{'='*60}")

        meta = result.get("metadata", {})

        safe_print(f"  Product:    {meta.get('product_name', 'N/A')}")

        safe_print(f"  Price:      ¥{meta.get('price_cny', 0)} (~${meta.get('price_cny', 0) / 7.2:.2f} USD)")

        safe_print(f"  Material:   {meta.get('material', 'N/A')}")

        safe_print(f"  Weight:     {meta.get('weight_gsm', 0)}gsm")

        safe_print(f"  Category:   {meta.get('product_category', 'N/A')}")

        safe_print(f"  Colors:     {meta.get('colors', [])}")

        safe_print(f"  Sizes:      {meta.get('sizes', [])}")

        safe_print(f"  Seller:     {meta.get('seller', {}).get('name', 'N/A')} (⭐{meta.get('seller', {}).get('rating', 0)})")

        safe_print(f"  Images:     {meta.get('image_count', 0)}")

        safe_print(f"  Measurements: {len(meta.get('measurements', {}))} sizes")

        safe_print(f"{'='*60}")

    elif result:

        safe_print("[OK] Product scraped and saved to input_sourcing/")

    else:

        safe_print("[FAIL] Could not scrape product.")

    os._exit(0)



if __name__ == "__main__":

    asyncio.run(main())

