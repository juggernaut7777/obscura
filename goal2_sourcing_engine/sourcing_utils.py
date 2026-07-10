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

async def download_selected_hq_images(
    pending_data: dict,
    selected_indices: List[int],
    output_dir: str
) -> List[str]:
    """
    Download only the user-selected full-resolution images.
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
                if resp.status_code == 200 and len(resp.content) > 100:
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
