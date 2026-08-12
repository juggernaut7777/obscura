import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def download_yupoo_album_hq(album_url, output_dir="input_sourcing"):
    """
    Downloads high-resolution images from a Yupoo album.
    Ensures correct Referer headers to bypass anti-hotlinking.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": album_url
    }

    print(f"[*] Accessing album: {album_url}")
    try:
        resp = requests.get(album_url, headers=headers, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"[!] Error accessing album: {e}")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Find all image items in the album
    # Yupoo usually has images in div class="showalbum_item" or similar
    image_items = soup.find_all('div', class_='showalbum_item')
    if not image_items:
        # Try generic image finding if the structure changed
        image_items = soup.find_all('img')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    download_count = 0
    for item in image_items:
        img_tag = item.find('img') if hasattr(item, 'find') and item.name != 'img' else item
        if not img_tag: continue
        
        # Look for the source. Yupoo often uses data-src for lazy loading
        img_url = img_tag.get('data-src') or img_tag.get('src')
        if not img_url: continue
        
        # Yupoo specific: convert thumbnail URL to original/big URL
        # Thumbnails often have '/small/' or '/medium/' in the path
        # Originals usually have '/big/' or are the base path
        hq_url = img_url.replace('/small/', '/big/').replace('/medium/', '/big/')
        if not hq_url.startswith('http'):
            hq_url = "https:" + hq_url if hq_url.startswith('//') else urljoin(album_url, hq_url)

        # Skip non-Yupoo images (like icons)
        if "yupoo.com" not in hq_url:
            continue

        filename = hq_url.split('/')[-1]
        # Remove any query params
        filename = filename.split('?')[0]
        
        filepath = os.path.join(output_dir, filename)
        
        print(f"[*] Downloading HQ Image: {filename}...")
        try:
            # Crucial: Referer must be set to the album URL
            img_resp = requests.get(hq_url, headers=headers, timeout=30)
            img_resp.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(img_resp.content)
            download_count += 1
            print(f"[OK] Saved to {filepath}")
        except Exception as e:
            print(f"[!] Failed to download {hq_url}: {e}")

    print(f"\n[DONE] Successfully downloaded {download_count} HQ images to '{output_dir}'.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        album_url = sys.argv[1]
        download_yupoo_album_hq(album_url)
    else:
        print("Usage: python yupoo_hq_downloader.py [ALBUM_URL]")
