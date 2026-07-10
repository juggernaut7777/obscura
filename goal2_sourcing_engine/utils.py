import os
import sys
import re
import json
from typing import Optional
from datetime import datetime
from pathlib import Path

# Common Paths
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output_ugc"
INPUT_DIR = BASE_DIR / "input_sourcing"
MODELS_DIR = BASE_DIR / "models" / "character_sheets"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

def safe_print(msg: str):
    """Safely print messages on Windows to avoid UnicodeEncodeErrors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding, errors='replace'))
        except Exception:
            print("[Print Error] Unable to encode output print message.")

def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text

def log(msg: str, log_file_path: Optional[str] = None):
    """Logs message with timestamp to console and log file."""
    if log_file_path is None:
        log_file_path = str(BASE_DIR / "worker_log.txt")
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    safe_print(line)
    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def detect_category(product_name: str, context_text: str = "") -> tuple:
    """
    Detects product category and whether it is a set based on keywords.
    Returns: (detected_category, is_set)
    """
    name_lower = product_name.lower()
    text_lower = context_text.lower()
    
    bottom_kw = ["pant", "short", "jogger", "trouser", "jeans", "cargo", "bottom"]
    shoe_kw = ["shoe", "sneaker", "boot", "jordan", "yeezy", "af1", "dunk", "trainer", "slide", "foam"]
    acc_kw = ["bag", "belt", "chain", "ring", "watch", "hat", "cap", "sunglasses", "balaclava"]
    set_kw = ["set", "suit", "tracksuit", "sweatsuit"]
    
    is_set = False
    detected_cat = "top"
    
    if any(k in name_lower for k in set_kw) or any(k in text_lower for k in set_kw):
        detected_cat = "set"
        is_set = True
    elif any(k in name_lower for k in shoe_kw):
        detected_cat = "shoes"
    elif any(k in name_lower for k in bottom_kw):
        detected_cat = "bottom"
    elif any(k in name_lower for k in acc_kw):
        detected_cat = "accessory"
        
    return detected_cat, is_set
