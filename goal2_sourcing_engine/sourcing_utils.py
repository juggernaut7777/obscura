"""
Shared Sourcing Utilities for Curation and Image Downloading
============================================================
Provides contact sheet creation, image downloading, and VLM evaluation helpers
without relying on replica-specific code.
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
os.makedirs(INPUT_SOURCING_DIR, exist_ok=True)
os.makedirs(REVIEW_PENDING_DIR, exist_ok=True)
os.makedirs(MANUAL_CURATION_DIR, exist_ok=True)

# Contact Sheet Configuration
GRID_COLS = 4          # 4 thumbnails per row
THUMB_SIZE = 200       # Each thumbnail is 200x200px
BADGE_RADIUS = 18      # Size of the numbered circle badge
BADGE_COLOR = (220, 20, 60)   # Crimson red
BADGE_TEXT = (255, 255, 255)   # White text
SHEET_BG = (18, 18, 18)       # Dark background
PADDING = 8                    # Padding between thumbnails

def create_contact_sheets(thumb_paths: List[str], start_index: int = 1) -> List[str]:
    """
    Build numbered contact sheet grids from a list of thumbnail image paths.
    Returns a list of contact sheet image paths.
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
                img.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
                # Center the image in the cell
                offset_x = x + (THUMB_SIZE - img.width) // 2
                offset_y = y + (THUMB_SIZE - img.height) // 2
                sheet.paste(img, (offset_x, offset_y))
            except Exception as e:
                safe_print(f"      [!] Failed to paste thumbnail {i}: {e}")
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


def create_color_grouped_contact_sheets(
    grouped_paths: Dict[str, List[str]], 
    output_prefix: str = "color_sheet",
    ai_labels: Optional[Dict[str, List[dict]]] = None
) -> Dict[str, str]:
    """
    Build clean, high-resolution mini contact sheets for individual color/category groups.
    Each mini sheet has thumbnails numbered 1, 2, 3... with a dark aesthetic title banner.
    Returns: dict mapping group_name -> sheet_file_path
    """
    result_sheets = {}
    HEADER_HEIGHT = 45

    for group_name, paths in grouped_paths.items():
        if not paths:
            continue
            
        num_imgs = len(paths)
        cols = min(4, num_imgs)
        num_rows = math.ceil(num_imgs / cols)
        
        sheet_w = cols * (THUMB_SIZE + PADDING) + PADDING
        sheet_h = HEADER_HEIGHT + num_rows * (THUMB_SIZE + PADDING) + PADDING
        
        sheet = Image.new("RGB", (sheet_w, sheet_h), SHEET_BG)
        draw = ImageDraw.Draw(sheet)
        
        try:
            font = ImageFont.truetype("arial.ttf", 18)
            title_font = ImageFont.truetype("arial.ttf", 20)
        except (IOError, OSError):
            font = ImageFont.load_default()
            title_font = font
            
        # Draw header banner
        draw.rectangle([0, 0, sheet_w, HEADER_HEIGHT], fill=(30, 30, 45))
        header_text = f"🎨 {group_name.replace('_', ' ').title()} ({num_imgs} Photos)"
        draw.text((PADDING + 5, 12), header_text, fill=(255, 255, 255), font=title_font)
        
        for i, thumb_path in enumerate(paths):
            row = i // cols
            col = i % cols
            
            x = PADDING + col * (THUMB_SIZE + PADDING)
            y = HEADER_HEIGHT + PADDING + row * (THUMB_SIZE + PADDING)
            
            try:
                img = Image.open(thumb_path)
                img.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
                offset_x = x + (THUMB_SIZE - img.width) // 2
                offset_y = y + (THUMB_SIZE - img.height) // 2
                sheet.paste(img, (offset_x, offset_y))
            except Exception as e:
                draw.rectangle([x, y, x + THUMB_SIZE, y + THUMB_SIZE], fill=(60, 60, 60))
                
            # Draw badge 1, 2, 3...
            badge_x = x + 10
            badge_y = y + 10
            draw.ellipse(
                [badge_x - BADGE_RADIUS, badge_y - BADGE_RADIUS,
                 badge_x + BADGE_RADIUS, badge_y + BADGE_RADIUS],
                fill=BADGE_COLOR
            )
            text = str(i + 1)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text(
                (badge_x - tw // 2, badge_y - th // 2 - 1),
                text, fill=BADGE_TEXT, font=font
            )
            
            # Draw AI label badge below the number (if available)
            if ai_labels and group_name in ai_labels:
                labels = ai_labels[group_name]
                if i < len(labels):
                    label_info = labels[i]
                    badge_text_label = label_info.get("badge", "?")
                    
                    # Color-code by view angle
                    label_colors = {
                        "F": (34, 139, 34),    # Green for Front
                        "B": (65, 105, 225),   # Blue for Back
                        "D": (128, 128, 128),  # Grey for Detail
                        "SC": (218, 165, 32),  # Gold for Size Chart
                        "TG": (148, 103, 189), # Purple for Tag
                        "S": (0, 191, 255),    # Cyan for Side
                        "?": (100, 100, 100),  # Dark grey for unknown
                    }
                    label_bg = label_colors.get(badge_text_label, (100, 100, 100))
                    
                    # Draw label pill below number badge
                    label_y = badge_y + BADGE_RADIUS + 4
                    pill_w = max(24, len(badge_text_label) * 10 + 8)
                    pill_h = 18
                    if hasattr(draw, 'rounded_rectangle'):
                        draw.rounded_rectangle(
                            [badge_x - pill_w//2, label_y, badge_x + pill_w//2, label_y + pill_h],
                            radius=4, fill=label_bg
                        )
                    else:
                        draw.rectangle(
                            [badge_x - pill_w//2, label_y, badge_x + pill_w//2, label_y + pill_h],
                            fill=label_bg
                        )
                    
                    # Draw label text
                    try:
                        small_font = ImageFont.truetype("arial.ttf", 12)
                    except:
                        small_font = font
                    lbox = draw.textbbox((0, 0), badge_text_label, font=small_font)
                    ltw = lbox[2] - lbox[0]
                    lth = lbox[3] - lbox[1]
                    draw.text(
                        (badge_x - ltw//2, label_y + (pill_h - lth)//2 - 1),
                        badge_text_label, fill=(255, 255, 255), font=small_font
                    )
                    
                    # If it's a top/bottom set piece, add piece indicator
                    piece = label_info.get("garment_piece", "")
                    if piece in ("top", "bottom"):
                        piece_text = "TOP" if piece == "top" else "BOT"
                        piece_y = label_y + pill_h + 2
                        piece_w = 30
                        piece_bg = (139, 69, 19) if piece == "bottom" else (70, 130, 180)
                        if hasattr(draw, 'rounded_rectangle'):
                            draw.rounded_rectangle(
                                [badge_x - piece_w//2, piece_y, badge_x + piece_w//2, piece_y + 14],
                                radius=3, fill=piece_bg
                            )
                        else:
                            draw.rectangle(
                                [badge_x - piece_w//2, piece_y, badge_x + piece_w//2, piece_y + 14],
                                fill=piece_bg
                            )
                        try:
                            tiny_font = ImageFont.truetype("arial.ttf", 10)
                        except:
                            tiny_font = small_font
                        pbox = draw.textbbox((0, 0), piece_text, font=tiny_font)
                        ptw = pbox[2] - pbox[0]
                        draw.text(
                            (badge_x - ptw//2, piece_y + 1),
                            piece_text, fill=(255, 255, 255), font=tiny_font
                        )
            
        sheet_path = os.path.join(
            INPUT_SOURCING_DIR,
            f"{output_prefix}_{group_name}_{datetime.now().strftime('%H%M%S')}.jpg"
        )
        sheet.save(sheet_path, "JPEG", quality=85)
        result_sheets[group_name] = sheet_path
        safe_print(f"   [MINI-SHEET] Created {group_name} contact sheet: {os.path.basename(sheet_path)}")

    return result_sheets

async def pre_classify_thumbnails(
    thumb_paths: List[str], 
    product_name: str = ""
) -> List[dict]:
    """
    Batch-classify thumbnails using Gemini Vision via LiteLLM Router.
    Returns a list of dicts (one per image) with AI labels.
    
    Each result dict:
    {
        "index": 1,                    # 1-based image number
        "garment_piece": "top",        # "top" | "bottom" | "accessory" | "full_set" | "unknown"
        "view_angle": "front",         # "front" | "back" | "side" | "detail" | "size_chart" | "tag" | "other"
        "garment_type": "hoodie",      # specific type like "hoodie", "cargo_pants", "sneakers"
        "design_group": null,          # "A", "B" if different prints/graphics detected, null if single design
        "label": "👕 Hoodie front",    # human-readable emoji label for Discord
        "badge": "F"                   # short badge for contact sheet: "F", "B", "D", "SC", "TG"
    }
    
    On error, returns fallback labels with "?" badges.
    """
    try:
        from litellm_router import LiteLLMRouter
        
        content_items = [
            {
                "type": "text",
                "text": (
                    f"You are classifying product images for a fashion sourcing pipeline.\n"
                    f"Product: \"{product_name}\"\n\n"
                    "Analyze each numbered image and return a JSON object with key \"images\" containing an array.\n"
                    "For each image provide:\n"
                    "- index: the image number (1-based)\n"
                    "- garment_piece: \"top\" (hoodie, tee, jacket, shirt) | \"bottom\" (pants, shorts, joggers) | \"accessory\" (bag, hat, shoes) | \"full_set\" (shows both top+bottom together) | \"unknown\"\n"
                    "- view_angle: \"front\" | \"back\" | \"side\" | \"detail\" (closeup of fabric/logo/stitching) | \"size_chart\" (measurement table) | \"tag\" (brand tag/label) | \"other\"\n"
                    "- garment_type: specific type like \"hoodie\", \"cargo_pants\", \"t_shirt\", \"sneakers\" etc.\n"
                    "- design_group: if you see DIFFERENT print/graphic designs on the same garment type and color, label them \"A\", \"B\", \"C\". If all images show the same design, use null.\n\n"
                    "Return ONLY valid JSON: {\"images\": [{...}, ...]}"
                )
            }
        ]
        
        for i, thumb_path in enumerate(thumb_paths):
            with Image.open(thumb_path) as img:
                img.thumbnail((512, 512))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                b64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                content_items.append({
                    "type": "text",
                    "text": f"Image {i + 1}:"
                })
                content_items.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_img}"}
                })
        
        messages = [{"role": "user", "content": content_items}]
        
        router = LiteLLMRouter()
        response = await router.get_chat_completion(
            model_group="gemini-lite", 
            messages=messages, 
            temperature=0.0, 
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        data = json.loads(result_text)
        images_data = data.get("images", [])
        
        # Build labels and badges
        for img_info in images_data:
            piece = img_info.get("garment_piece", "unknown")
            piece_emoji = {
                "top": "👕",
                "bottom": "👖",
                "accessory": "👜",
                "full_set": "👕👖",
                "unknown": "📦"
            }.get(piece, "📦")
            
            gtype = img_info.get("garment_type", "item")
            vangle = img_info.get("view_angle", "other")
            
            img_info["label"] = f"{piece_emoji} {gtype.replace('_',' ').title()} {vangle}"
            
            view_to_badge = {
                "front": "F",
                "back": "B",
                "side": "S",
                "detail": "D",
                "size_chart": "SC",
                "tag": "TG",
                "other": "?"
            }
            img_info["badge"] = view_to_badge.get(vangle, "?")
            
        safe_print(f"   [AI-LABEL] Classified {len(thumb_paths)} thumbnails for '{product_name}'")
        return images_data

    except Exception as e:
        safe_print(f"      [!] Error classifying thumbnails: {e}")
        fallback = []
        for i in range(len(thumb_paths)):
            fallback.append({
                "index": i + 1,
                "garment_piece": "unknown",
                "view_angle": "other",
                "garment_type": "unknown",
                "design_group": None,
                "label": f"#{i + 1}",
                "badge": "?"
            })
        return fallback

def ensure_yupoo_doh(url_or_host: str = "photo.yupoo.com"):
    """Ensure Yupoo host (e.g. photo.yupoo.com) is resolved via DoH for requests/socket compatibility."""
    from urllib.parse import urlparse
    try:
        from yupoo_scraper import YupooScraper
        scraper = YupooScraper()
        
        host = "photo.yupoo.com"
        if "://" in url_or_host:
            parsed = urlparse(url_or_host)
            if parsed.hostname:
                host = parsed.hostname
        elif url_or_host:
            host = url_or_host

        scraper._resolve_clean_ip("photo.yupoo.com")
        if host != "photo.yupoo.com":
            scraper._resolve_clean_ip(host)
    except Exception as e:
        safe_print(f"      [Yupoo DoH] Warning: {e}")

async def download_selected_hq_images(
    pending_data: dict,
    selected_indices: List[int],
    output_dir: str
) -> List[str]:
    """
    Download only the user-selected full-resolution images.
    Returns list of downloaded file paths.
    """
    import requests
    ensure_yupoo_doh("photo.yupoo.com")
    url_mapping = pending_data.get("url_mapping", {})
    referer = pending_data.get("referer", pending_data.get("album_url", ""))
    if referer:
        ensure_yupoo_doh(referer)
    downloaded = []
    loop = asyncio.get_running_loop()

    def _dl_hq_single(hq_url, ref_url, save_path):
        try:
            resp = requests.get(
                hq_url,
                headers={
                    "Referer": ref_url or "https://yupoo.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=25
            )
            if resp.status_code == 200 and len(resp.content) > 100:
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                return len(resp.content)
        except Exception as e:
            safe_print(f"      [!] HQ download error for {hq_url}: {e}")
        return None

    for idx in selected_indices:
        hq_url = url_mapping.get(str(idx))
        if not hq_url:
            safe_print(f"      [!] Index {idx} not found in mapping. Skipping.")
            continue

        ext = hq_url.split('.')[-1].split('?')[0].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'webp']:
            ext = 'jpg'
        save_path = os.path.join(output_dir, f"img_{idx:03d}.{ext}")

        size_bytes = await loop.run_in_executor(None, _dl_hq_single, hq_url, referer, save_path)
        if size_bytes:
            size_kb = size_bytes / 1024
            safe_print(f"      [HQ] #{idx} → {size_kb:.0f}KB → {os.path.basename(save_path)}")
            downloaded.append(save_path)
        else:
            safe_print(f"      [!] HQ download #{idx} failed")

    return downloaded

async def evaluate_image_with_vlm(image_path: str, title: str) -> Tuple[str, int]:
    """
    Classifies the image as product, size_chart, or other using LiteLLM/Gemini router.
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

    try:
        from litellm_router import LiteLLMRouter
        router = LiteLLMRouter()
        
        # Construct visions prompt payload
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": vlm_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_img}"}
                    }
                ]
            }
        ]
        
        # Use gemini-lite or fallbacks via router
        response = await router.get_chat_completion(
            model_group="gemini-lite",
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        data = json.loads(result_text)
        category = data.get("category", "other").strip().lower()
        score = int(data.get("score", 0))
        return category, score
    except Exception as e:
        print(f"      [!] VLM evaluation error: {e}")
        return "product", 7  # Safe default on error
