"""
PRODUCT DATABASE & INVENTORY TRACKER
====================================
Maintains a persistent record of every product ever sent to the bot.
Allows the AI Matchmaker to "Mix and Match" old shirts with new pants.

Stored in: output/product_inventory.json
"""

import json
import os
from pathlib import Path
from datetime import datetime

INVENTORY_FILE = Path("output/product_inventory.json")

def update_inventory(product_data):
    """Adds or updates a product in the persistent database."""
    inventory = load_inventory()
    
    # Use a unique key (Source URL + Name)
    p_id = product_data.get("productUrl", product_data.get("productName", str(datetime.now().timestamp())))
    
    # Update or Add
    inventory[p_id] = {
        **product_data,
        "last_seen": datetime.now().isoformat(),
        "status": "available" # manual toggle if needed later
    }
    
    save_inventory(inventory)
    return p_id

def load_inventory():
    if not INVENTORY_FILE.exists():
        return {}
    try:
        with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_inventory(inventory):
    os.makedirs(INVENTORY_FILE.parent, exist_ok=True)
    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

def get_available_pool():
    """Returns items grouped by category for the Matchmaker."""
    inv = load_inventory()
    pool = {"top": [], "bottom": [], "shoes": [], "accessory": []}
    
    for p_id, p in inv.items():
        if p.get("status") != "available": continue
        
        cat = p.get("category", "top").lower()
        if "shoe" in cat: pool["shoes"].append(p)
        elif "pant" in cat or "short" in cat or "bottom" in cat or "trous" in cat: pool["bottom"].append(p)
        elif "accessory" in cat: pool["accessory"].append(p)
        else: pool["top"].append(p)
        
    return pool
