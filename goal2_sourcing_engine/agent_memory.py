"""
Agent Memory — Persistent State & Learning
===========================================
JSON-based memory that persists between runs.
Tracks everything the brain has done, learned, and planned.

The brain uses this to:
- Know what model sheets exist (or need creating)
- Track which products have been processed
- Remember which brands have been contacted
- Learn what content performs best
- Plan next actions based on state
"""
import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

AGENTMEMORY_URL = "http://localhost:3111/agentmemory"

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "brain_memory.json")


def _default_memory() -> dict:
    """Create a fresh memory structure."""
    return {
        "created_at": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat(),
        "version": "1.0",

        # ── GOALS ──
        "primary_goal": "Make money through AI-generated fashion & sneaker ads",
        "priority_categories": ["fashion", "sneakers", "shoes", "beauty", "wigs", "accessories"],
        "platforms": ["tiktok", "instagram", "facebook"],

        # ── MODEL SHEETS ──
        "models": {
            # "f1_black_female": {
            #     "path": "models/character_sheets/f1_black_female.png",
            #     "ethnicity": "black", "gender": "female",
            #     "created": "2026-04-03", "angles": ["front"]
            # }
        },

        # ── PRODUCT CATALOG ──
        "products_scraped": [],       # All products found
        "products_processed": [],     # Products with ads generated
        "products_posted": [],        # Products posted to social

        # ── BRAND OUTREACH ──
        "brands_discovered": [],      # Brands found for agency model
        "brands_contacted": [],       # Brands we've DMed
        "brands_responded": [],       # Brands that replied

        # ── DIGITAL PRODUCTS ──
        "digital_products": [],       # Courses, prompt packs, templates for sale

        # ── CONTENT PERFORMANCE ──
        "posts": [],                  # All posts with engagement data
        "performance": {
            "best_product_type": None,
            "best_time_to_post": None,
            "best_caption_style": None,
            "best_ad_format": None,
            "total_posts": 0,
            "total_engagement": 0,
        },

        # ── LEARNINGS ──
        "learnings": [],              # What the brain has figured out
        "fashion_rules": [],          # Fashion coordination rules learned

        # ── ACCOUNTS ──
        "social_accounts": {
            "tiktok": {"logged_in": False, "cookies_saved": False},
            "instagram": {"logged_in": False, "cookies_saved": False},
            "facebook": {"logged_in": False, "cookies_saved": False},
            "google_flow": {"logged_in": False, "cookies_saved": False},
            "gumroad": {"logged_in": False, "cookies_saved": False},
        },

        # ── AGENT STATE ──
        "current_phase": "setup",     # setup | creating_models | sourcing | generating | posting | outreach
        "last_action": None,
        "last_error": None,
        "actions_today": 0,
        "daily_limits": {
            "max_posts": 10,
            "max_dms": 5,
            "max_generations": 50,
            "max_scrapes": 20,
        },

        # ── SUPPLIER SOURCES ──
        "suppliers": {
            "usfans": {"url": "https://www.usfans.com", "active": True},
            "cnfans": {"url": "https://www.cnfans.com", "active": True},
            "yupoo_catalogs": [],     # Yupoo sellers to scrape
        },
    }


class AgentMemory:
    """Persistent memory for the autonomous agent."""

    def __init__(self, memory_path: str = MEMORY_FILE):
        self.path = memory_path
        self.data = self._load()

    def _load(self) -> dict:
        """Load memory from disk or create fresh."""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    data = json.load(f)
                print(f"[BRAIN] Memory loaded ({len(data.get('learnings', []))} learnings, "
                      f"{len(data.get('products_posted', []))} posts)")
                return data
            except json.JSONDecodeError:
                print("[!]  Corrupted memory file, starting fresh")
                return _default_memory()
        else:
            print("[BRAIN] Fresh memory initialized")
            return _default_memory()

    def save(self):
        """Persist memory to disk."""
        self.data["last_active"] = datetime.now().isoformat()
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    # ── GETTERS ──

    @property
    def phase(self) -> str:
        return self.data.get("current_phase", "setup")

    @property
    def has_models(self) -> bool:
        return len(self.data.get("models", {})) > 0

    @property
    def model_count(self) -> int:
        return len(self.data.get("models", {}))

    @property
    def models(self) -> dict:
        return self.data.get("models", {})

    @property
    def products_ready(self) -> list:
        """Products scraped but not yet processed."""
        processed_ids = {p.get("id") for p in self.data.get("products_processed", [])}
        return [p for p in self.data.get("products_scraped", [])
                if p.get("id") not in processed_ids]

    @property
    def actions_today(self) -> int:
        return self.data.get("actions_today", 0)

    # ── SETTERS ──

    def set_phase(self, phase: str):
        self.data["current_phase"] = phase
        self.save()

    def add_model(self, model_id: str, path: str, ethnicity: str = "",
                  gender: str = "", angles: list = None):
        self.data["models"][model_id] = {
            "path": path,
            "ethnicity": ethnicity,
            "gender": gender,
            "created": datetime.now().isoformat(),
            "angles": angles or ["front"],
        }
        self.save()

    def add_product(self, product: dict):
        """Add a scraped product to catalog (with deduplication)."""
        # Dedup by URL or product name
        existing_urls = {p.get("productUrl", "") for p in self.data["products_scraped"] if p.get("productUrl")}
        existing_names = {p.get("productName", "").lower().strip() for p in self.data["products_scraped"] if p.get("productName")}
        
        url = product.get("productUrl", "")
        name = product.get("productName", "").lower().strip()
        
        if url and url in existing_urls:
            print(f"[MEMORY] Skipped duplicate (URL): {url[:60]}")
            return
        if name and name in existing_names:
            print(f"[MEMORY] Skipped duplicate (name): {name[:60]}")
            return
            
        product["_scraped_at"] = datetime.now().isoformat()
        product["id"] = product.get("id", f"prod_{len(self.data['products_scraped'])}")
        self.data["products_scraped"].append(product)
        self.save()

    def add_products_batch(self, products: list):
        existing_urls = {p.get("productUrl", "") for p in self.data["products_scraped"] if p.get("productUrl")}
        existing_names = {p.get("productName", "").lower().strip() for p in self.data["products_scraped"] if p.get("productName")}
        added = 0
        for p in products:
            url = p.get("productUrl", "")
            name = p.get("productName", "").lower().strip()
            if url and url in existing_urls:
                continue
            if name and name in existing_names:
                continue
            p["_scraped_at"] = datetime.now().isoformat()
            p["id"] = p.get("id", f"prod_{len(self.data['products_scraped'])}")
            self.data["products_scraped"].append(p)
            existing_urls.add(url)
            existing_names.add(name)
            added += 1
        if added:
            self.save()
        print(f"[MEMORY] Batch: added {added}, skipped {len(products) - added} dupes")

    def mark_product_processed(self, product: dict, ad_paths: list = None):
        product["_processed_at"] = datetime.now().isoformat()
        product["_ad_paths"] = ad_paths or []
        self.data["products_processed"].append(product)
        self.save()

    def mark_product_posted(self, product: dict, platform: str, post_url: str = ""):
        product["_posted_at"] = datetime.now().isoformat()
        product["_platform"] = platform
        product["_post_url"] = post_url
        self.data["products_posted"].append(product)
        self.data["performance"]["total_posts"] += 1
        self.save()

    def add_brand(self, brand: dict):
        self.data["brands_discovered"].append({
            **brand,
            "_discovered_at": datetime.now().isoformat(),
        })
        self.save()

    def mark_brand_contacted(self, brand_handle: str, message: str = ""):
        self.data["brands_contacted"].append({
            "handle": brand_handle,
            "message": message,
            "contacted_at": datetime.now().isoformat(),
        })
        self.save()

    def _push_to_sidecar(self, observation: str, memory_type: str):
        """Push an observation to the AgentMemory REST API sidecar."""
        try:
            requests.post(
                f"{AGENTMEMORY_URL}/remember",
                json={"observation": observation, "type": memory_type},
                headers={"Content-Type": "application/json"},
                timeout=2
            )
        except requests.exceptions.RequestException:
            pass # Sidecar might not be running, fail gracefully

    def add_learning(self, learning: str):
        self.data["learnings"].append({
            "text": learning,
            "learned_at": datetime.now().isoformat(),
        })
        self.save()
        self._push_to_sidecar(learning, "semantic")
        print(f"[LEARN] Learned: {learning}")

    def add_fashion_rule(self, rule: str):
        self.data["fashion_rules"].append(rule)
        self.save()
        self._push_to_sidecar(rule, "procedural")

    def log_action(self, action: str, result: str = "", success: bool = True):
        self.data["last_action"] = {
            "action": action,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }
        self.data["actions_today"] += 1
        
        # Push to episodic memory
        status = "Success" if success else f"Failed: {result}"
        self._push_to_sidecar(f"Action: {action} -> {status}", "episodic")
        
        if not success:
            self.data["last_error"] = {
                "action": action,
                "error": result,
                "timestamp": datetime.now().isoformat(),
            }
        self.save()

    def reset_daily_counters(self):
        self.data["actions_today"] = 0
        self.save()

    def add_yupoo_supplier(self, name: str, url: str):
        self.data["suppliers"]["yupoo_catalogs"].append({
            "name": name, "url": url,
            "added_at": datetime.now().isoformat(),
        })
        self.save()

    def update_account_status(self, platform: str, logged_in: bool, cookies: bool = False):
        if platform in self.data["social_accounts"]:
            self.data["social_accounts"][platform]["logged_in"] = logged_in
            self.data["social_accounts"][platform]["cookies_saved"] = cookies
            self.save()

    # ── STATE SUMMARY (for LLM context) ──

    def get_state_summary(self) -> str:
        """Generate a COMPACT state summary for the LLM brain.
        
        IMPORTANT: Keep this small to fit within smaller LLM context windows.
        ~1500 tokens max. Show counts, not full lists.
        """
        d = self.data
        models = d.get("models", {})
        
        # Show count + last 3 models (not all 238!)
        models_str = "; ".join(f"{k} ({len(v.get('angles', []))} angles)" for k,v in d.get('models', {}).items()) or 'none'
        accounts_str = "; ".join(f"{k}: {'LOGGED IN' if v.get('cookies') else 'NO LOGIN'}" for k,v in d.get('accounts', {}).items()) or 'none'
        digital = d.get('digital_products', [])
        last_action = d.get('last_action') or {}
        last_error = d.get('last_error') or {}
        
        return f"""=== STATE ===
Phase: {d.get('current_phase', 'setup')} | Actions today: {d.get('actions_today', 0)}

Models: {models_str}
Products: {len(d.get('products_scraped', []))} scraped, {len(d.get('products_processed', []))} processed, {len(d.get('products_posted', []))} posted
Digital products: {len(digital)} created, {len([p for p in digital if p.get('listed')])} listed
Accounts: {accounts_str}
Brands: {len(d.get('brands_discovered', []))} found, {len(d.get('brands_contacted', []))} contacted

Last action: {last_action.get('action', 'none')} ({'✅' if last_action.get('success') else '❌'})
Last error: {last_error.get('error', 'none')[:100]}

Recent learnings: {'; '.join(l.get('text', str(l))[:60] for l in d.get('learnings', [])[-3:]) or 'none'}""".strip()


# ── CLI ──
if __name__ == "__main__":
    mem = AgentMemory()
    print(mem.get_state_summary())
