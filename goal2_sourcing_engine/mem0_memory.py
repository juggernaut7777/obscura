"""
Mem0 Resilient Memory Adapter
==============================
Replaces legacy corruptible JSON memory (brain_memory.json) with:
1. SQLite relational tables for transactional state (scraped products, model sheets, counters).
2. Mem0 local semantic vector store for long-term learnings, episodic memory, and fashion rules.
"""
import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "data", "brain_sqlite.db")
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

class Mem0Memory:
    """
    Drop-in adapter replacing legacy AgentMemory.
    Stores relational data in SQLite and unstructured knowledge in Mem0.
    """
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()
        self.mem0 = None
        self._init_mem0()

    def _init_db(self):
        """Creates SQLite tables for robust state persistence if they do not exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # State config table (phase, daily limit counters, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                model_id TEXT PRIMARY KEY,
                path TEXT,
                ethnicity TEXT,
                gender TEXT,
                created TEXT,
                angles TEXT
            )
        """)
        
        # Products catalog table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                productName TEXT,
                category TEXT,
                productUrl TEXT,
                price REAL,
                size_info TEXT,
                scraped_at TEXT,
                processed_at TEXT,
                posted_at TEXT,
                ad_paths TEXT,
                extra_json TEXT
            )
        """)
        
        # Suppliers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                name TEXT PRIMARY KEY,
                url TEXT,
                added_at TEXT
            )
        """)
        
        # Setup default state
        cursor.execute("INSERT OR IGNORE INTO state_metadata (key, value) VALUES ('current_phase', 'setup')")
        cursor.execute("INSERT OR IGNORE INTO state_metadata (key, value) VALUES ('actions_today', '0')")
        
        conn.commit()
        conn.close()

    def _init_mem0(self):
        """Initialise Mem0 client locally using qdrant in-memory vector store (zero-cost, no OpenAI required)."""
        try:
            from mem0 import Memory
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "collection_name": "sourcing_agent_memory",
                        "host": "localhost",
                        "port": 6333,
                        "on_disk": False,      # In-memory, no server needed
                        "path": os.path.join(BASE_DIR, "data", "qdrant_store")
                    }
                },
                "llm": {
                    "provider": "groq",
                    "config": {
                        "model": "llama-3.1-8b-instant",
                        "api_key": os.getenv("GROQ_API_KEY", "")
                    }
                },
                "embedder": {
                    "provider": "huggingface",
                    "config": {
                        "model": "all-MiniLM-L6-v2"
                    }
                }
            }
            self.mem0 = Memory.from_config(config)
            print("[MEM0] Semantic Memory loaded (qdrant + HuggingFace embedder).")
        except Exception as e:
            print(f"[MEM0 WARNING] {e}. SQLite-only mode active — all operations use structured DB.")
            self.mem0 = None

    # ─── DATABASE METADATA GETTERS & SETTERS ───
    
    def _get_metadata(self, key: str, default: str = "") -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM state_metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def _set_metadata(self, key: str, value: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO state_metadata (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()

    # ─── LEGACY COMPATIBLE PROPERTIES ───

    @property
    def phase(self) -> str:
        return self._get_metadata("current_phase", "setup")

    @property
    def has_models(self) -> bool:
        return self.model_count > 0

    @property
    def model_count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM models")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    @property
    def models(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models")
        rows = cursor.fetchall()
        conn.close()
        
        result = {}
        for r in rows:
            result[r[0]] = {
                "path": r[1],
                "ethnicity": r[2],
                "gender": r[3],
                "created": r[4],
                "angles": json.loads(r[5]) if r[5] else []
            }
        return result

    @property
    def products_ready(self) -> list:
        """Products scraped but not yet processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE processed_at IS NULL")
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for r in rows:
            extra = json.loads(r[10]) if r[10] else {}
            products.append({
                "id": r[0],
                "productName": r[1],
                "category": r[2],
                "productUrl": r[3],
                "price": r[4],
                "size_info": r[5],
                "_scraped_at": r[6],
                **extra
            })
        return products

    @property
    def actions_today(self) -> int:
        return int(self._get_metadata("actions_today", "0"))

    @property
    def data(self) -> Dict[str, Any]:
        """Backward-compatible dictionary access for metadata state and product logs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Fetch all metadata
        cursor.execute("SELECT key, value FROM state_metadata")
        rows = cursor.fetchall()
        metadata_dict = {row[0]: row[1] for row in rows}
        
        # 2. Fetch products logged
        cursor.execute("SELECT id FROM products")
        products_scraped = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM products WHERE processed_at IS NOT NULL")
        products_processed = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM products WHERE posted_at IS NOT NULL")
        products_posted = [row[0] for row in cursor.fetchall()]
        
        # 3. Fetch learnings (metadata keys starting with 'learning_')
        learnings = [v for k, v in metadata_dict.items() if k.startswith("learning_")]
        
        # 4. Fetch brands contacted (if stored in metadata)
        brands_contact = []
        for k, v in metadata_dict.items():
            if k.startswith("brand_contacted_"):
                brands_contact.append(v)
                
        conn.close()
        
        # Build dictionary matching legacy AgentMemory structure
        return {
            "last_active": metadata_dict.get("last_active", datetime.now().strftime("%Y-%m-%d")),
            "products_scraped": products_scraped,
            "products_processed": products_processed,
            "products_posted": products_posted,
            "brands_contacted": brands_contact,
            "learnings": learnings,
            "performance": {
                "total_posts": len(products_posted)
            }
        }

    # ─── STATE MODIFIERS ───

    def set_phase(self, phase: str):
        self._set_metadata("current_phase", phase)

    def add_model(self, model_id: str, path: str, ethnicity: str = "", gender: str = "", angles: list = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        angles_str = json.dumps(angles or ["front"])
        cursor.execute(
            "INSERT OR REPLACE INTO models (model_id, path, ethnicity, gender, created, angles) VALUES (?, ?, ?, ?, ?, ?)",
            (model_id, path, ethnicity, gender, datetime.now().isoformat(), angles_str)
        )
        conn.commit()
        conn.close()

    def add_product(self, product: dict):
        """Add scraped product with deduplication."""
        url = product.get("productUrl", "")
        name = product.get("productName", "").strip()
        
        # Deduplication check
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if url:
            cursor.execute("SELECT id FROM products WHERE productUrl = ?", (url,))
            if cursor.fetchone():
                conn.close()
                return
        if name:
            cursor.execute("SELECT id FROM products WHERE LOWER(productName) = ?", (name.lower(),))
            if cursor.fetchone():
                conn.close()
                return

        prod_id = product.get("id", f"prod_{int(datetime.now().timestamp())}")
        extra = {k: v for k, v in product.items() if k not in ("id", "productName", "category", "productUrl", "price", "size_info")}
        
        cursor.execute(
            "INSERT INTO products (id, productName, category, productUrl, price, size_info, scraped_at, extra_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (prod_id, name, product.get("category", "top"), url, product.get("price", 0), product.get("size_info"), datetime.now().isoformat(), json.dumps(extra))
        )
        conn.commit()
        conn.close()
        
        # Push into Mem0 episodic vector memory
        if self.mem0:
            self.mem0.add(f"Scraped new product drop: {name} under category {product.get('category')} for ¥{product.get('price')}.", user_id="sourcing_agent")

    def add_products_batch(self, products: list):
        for p in products:
            self.add_product(p)

    def mark_product_processed(self, product: dict, ad_paths: list = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        prod_id = product.get("id")
        ad_paths_str = json.dumps(ad_paths or [])
        cursor.execute(
            "UPDATE products SET processed_at = ?, ad_paths = ? WHERE id = ?",
            (datetime.now().isoformat(), ad_paths_str, prod_id)
        )
        conn.commit()
        conn.close()

    def mark_product_posted(self, product: dict, platform: str, post_url: str = ""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        prod_id = product.get("id")
        cursor.execute(
            "UPDATE products SET posted_at = ? WHERE id = ?",
            (datetime.now().isoformat(), prod_id)
        )
        conn.commit()
        conn.close()
        if self.mem0:
            self.mem0.add(f"Successfully posted product {product.get('productName')} to platform {platform}.", user_id="sourcing_agent")

    # ─── UNSTRUCTURED SEMANTIC MEMORY (Mem0 Integration) ───

    def add_learning(self, learning: str):
        """Persist structured facts or learnings into Mem0 long-term memory."""
        print(f"[MEM0 LEARN] {learning}")
        if self.mem0:
            self.mem0.add(learning, user_id="sourcing_agent")
            
        # SQLite raw fallback
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO state_metadata (key, value) VALUES (?, ?)", (f"learning_{datetime.now().timestamp()}", learning))
        conn.commit()
        conn.close()

    def add_fashion_rule(self, rule: str):
        print(f"[MEM0 FASHION RULE] {rule}")
        if self.mem0:
            self.mem0.add(f"Fashion coordinate rule: {rule}", user_id="sourcing_agent")

    def log_action(self, action: str, result: str = "", success: bool = True):
        # Update daily actions count and last active timestamp
        actions = self.actions_today + 1
        self._set_metadata("actions_today", str(actions))
        self._set_metadata("last_active", datetime.now().isoformat())
        
        status = "Success" if success else f"Failed: {result}"
        print(f"[ACTION LOG] {action} -> {status}")
        if self.mem0:
            self.mem0.add(f"Episodic Log: Action '{action}' completed with status '{status}'.", user_id="sourcing_agent")

    def reset_daily_counters(self):
        self._set_metadata("actions_today", "0")

    def add_yupoo_supplier(self, name: str, url: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO suppliers (name, url, added_at) VALUES (?, ?, ?)",
            (name, url, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def get_state_summary(self) -> str:
        """Expose small context state summary for the thinking brain."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Active counts
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE processed_at IS NOT NULL")
        processed_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE posted_at IS NOT NULL")
        posted_products = cursor.fetchone()[0]
        
        conn.close()
        
        return f"""=== STATE (MEM0 ADAPTER) ===
Phase: {self.phase} | Actions today: {self.actions_today}
Models loaded: {self.model_count}
Products: {total_products} scraped, {processed_products} processed, {posted_products} posted
Database engine: SQLite + Mem0 Local Vectors
""".strip()
