import os
import sys
import json
import re
import urllib.parse
import httpx
import asyncio
from datetime import datetime

# Safe print for Windows
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

def clean_shopify_img_url(url: str) -> str:
    """Ensure the Shopify image URL starts with https: and strips dimensions parameters to get the highest resolution."""
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    
    # Remove resolution limiting query params
    for param in ["width", "height", "crop"]:
        query.pop(param, None)
        
    new_query = urllib.parse.urlencode(query, doseq=True)
    
    # Strip scaling suffixes in the path like _large, _1024x1024, _2048x2048
    path = parsed.path
    path = re.sub(r'_(?:[0-9]+x[0-9]+|large|grande|master|medium|small|compact|pico|icon)\.', '.', path)
    
    new_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, new_query, parsed.fragment))
    return new_url

async def scrape_shopify_product(url: str):
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path.rstrip("/")
    
    if not path.startswith("/products/"):
        safe_print("[!] URL must be a shopify product page (containing /products/[handle]).")
        return False
        
    domain = parsed_url.netloc
    brand_name = domain.replace("www.", "").split(".")[0]
    
    # Append .js to Shopify product URL
    if not path.endswith(".js"):
        json_url = f"https://{domain}{path}.js"
    else:
        json_url = f"https://{domain}{path}"
        
    safe_print(f"[*] Fetching Shopify product metadata from: {json_url}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(json_url, headers=headers, follow_redirects=True)
            if resp.status_code != 200:
                safe_print(f"[!] Failed to fetch product data (HTTP Status: {resp.status_code})")
                return False
                
            data = resp.json()
        except Exception as e:
            safe_print(f"[!] Error fetching JSON data: {e}")
            return False
            
    title = data.get("title", "Unknown Product")
    price = data.get("price", 0)
    price_string = f"${price / 100:.2f}"
    description = data.get("description", "")
    images = data.get("images", [])
    
    clean_desc = re.sub(r'<[^>]+>', '', description).strip()
    
    safe_print(f"[+] Product Found: {title} | Price: {price_string}")
    safe_print(f"[+] Found {len(images)} images in Shopify catalog.")
    
    if not images:
        safe_print("[!] No images found in product catalog.")
        return False
        
    # Target root folder inside goal2_sourcing_engine/input_sourcing
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_root = os.path.join(base_dir, "input_sourcing")
    os.makedirs(target_root, exist_ok=True)
    
    slug = re.sub(r'[^\w\s-]', '', title.lower().strip())
    slug = re.sub(r'[\s_]+', '-', slug)
    folder_name = f"brand_{brand_name}_{slug}"
    product_dir = os.path.join(target_root, folder_name)
    os.makedirs(product_dir, exist_ok=True)
    
    saved_count = 0
    async with httpx.AsyncClient(timeout=30.0) as img_client:
        for idx, img_url in enumerate(images):
            clean_url = clean_shopify_img_url(img_url)
            safe_print(f"   [-] Downloading image {idx+1}/{len(images)}: {clean_url}")
            try:
                img_resp = await img_client.get(clean_url)
                if img_resp.status_code == 200:
                    ext = clean_url.split(".")[-1].split("?")[0].lower()
                    if ext not in ["jpg", "jpeg", "png", "webp"]:
                        ext = "jpg"
                    
                    file_name = f"angle_{idx+1}.{ext}"
                    file_path = os.path.join(product_dir, file_name)
                    with open(file_path, "wb") as f:
                        f.write(img_resp.content)
                    saved_count += 1
                    safe_print(f"      [SAVED] {file_name}")
            except Exception as e:
                safe_print(f"      [!] Failed to download image {idx+1}: {e}")
                
    # Save standard metadata.json
    metadata = {
        "product_name": title,
        "color": "default",
        "price_string": price_string,
        "link": url,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "shopify_catalog_scraper",
        "author": "autonomous_sourcer",
        "image_count": saved_count,
        "size_info": "See site",
        "description": clean_desc[:500]
    }
    
    with open(os.path.join(product_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    with open(os.path.join(product_dir, "link.txt"), "w", encoding="utf-8") as f:
        f.write(url)
        
    safe_print(f"\n[OK] Scraped Shopify Product. Grouped {saved_count} images in {folder_name}\n")
    return True

async def main():
    if len(sys.argv) < 2:
        safe_print("==================================================")
        safe_print("SHOPIFY DIRECT CATALOG PRODUCT SCRAPER")
        safe_print("==================================================")
        safe_print("Usage: python scrape_shopify_product.py [shopify_product_url]")
        safe_print("Example: python scrape_shopify_product.py https://adsumnyc.com/products/core-logo-hoody-navy")
        return
        
    url = sys.argv[1]
    await scrape_shopify_product(url)
    # Force exit to prevent background hangs if any libraries load async run loops
    os._exit(0)

if __name__ == "__main__":
    asyncio.run(main())
