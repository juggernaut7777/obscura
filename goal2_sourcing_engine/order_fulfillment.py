"""
ORDER FULFILLMENT ENGINE — Multi-Product, Multi-Pipeline
==========================================================
Handles full order lifecycle for ALL order types:

  Pipeline A (DDP AGENT)    → Items sourced from Weidian/1688/Taobao
                               → DDP agent on Alibaba buys + ships to Africa
                               → Door-to-door, all duties & shipping included
                               → Weight-based DDP shipping cost

  Pipeline B (CJ)           → Legit branded, dropshipped (future use)
                               → CJ auto-fulfills and ships directly
                               → CJ calculates their own shipping

  Mixed Orders              → Both pipelines → Customer gets 2 packages
                               → Disclosed upfront at checkout

Shipping Cost Logic (DDP Agent via Alibaba):
  DDP agents quote per-kg rates (air freight) or per-CBM (sea freight).
  Air freight DDP to Africa typically: $8-17/kg all-inclusive.
  We estimate using $12/kg average for pricing calculations.
  Actual cost confirmed with DDP agent per shipment.

Variant Reverse-Mapping:
  When a customer selects "Black / Size L" on the storefront,
  this engine maps it back to the original Chinese text (e.g. 黑色, L码)
  so the DDP agent purchases the correct variant.

Usage:
  from order_fulfillment import OrderFulfiller
  fulfiller = OrderFulfiller()
  result = fulfiller.create_order_from_checkout(checkout_data)
"""

import os
import json
import time
import hashlib
import logging
import requests
from pathlib import Path
from datetime import datetime
from enum import Enum

# ── Config ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
ORDERS_DIR = BASE_DIR / "data" / "orders"
ORDERS_DIR.mkdir(parents=True, exist_ok=True)

DISCORD_WEBHOOK = os.environ.get("DISCORD_SCOUT_WEBHOOK", "")
CJ_API_KEY = os.environ.get("CJ_API_KEY", "")
CJ_EMAIL = os.environ.get("CJ_EMAIL", "")
CJ_BASE_URL = "https://developers.cjdropshipping.com/api2.0/v1"
CNY_TO_USD = 7.2  # 1 USD = 7.2 CNY

# Private supplier mappings for variant reverse-mapping
SUPPLIER_MAPPINGS_FILE = BASE_DIR / "supplier_mappings.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [FULFILL] %(message)s")
log = logging.getLogger("fulfillment")


# ── Enums ────────────────────────────────────────────────────────
class Pipeline(Enum):
    DDP_AGENT = "ddp_agent"  # DDP shipping agent via Alibaba (Weidian/1688/Taobao items)
    CJ       = "cj"         # Legit branded auto-fulfilled (future)
    MANUAL   = "manual"     # Edge case — needs direct intervention


class OrderStatus(Enum):
    PENDING          = "pending"
    AWAITING_PAYMENT = "awaiting_payment"
    PURCHASED        = "purchased"
    IN_WAREHOUSE     = "in_warehouse"
    QC_REVIEW        = "qc_review"
    COMBINING        = "combining"        # Kakobuy: consolidating multi-items
    SHIPPED          = "shipped"
    DELIVERED        = "delivered"
    CANCELLED        = "cancelled"


# ── DDP Agent Shipping Cost Estimate (Air Freight to Africa) ────
# DDP (Delivered Duty Paid) all-inclusive per-kg rates via Alibaba agents
# These rates include: domestic China shipping + international freight + customs + duties + local delivery
DDP_SHIPPING_RATE_PER_KG = 12.00  # USD per kg average air freight DDP to Africa
DDP_MIN_SHIPPING = 15.00          # Minimum shipping charge

# Estimated item weights by category (kg)
ITEM_WEIGHTS = {
    "hoodie": 0.60, "jacket": 0.90, "coat": 1.20, "puffer": 1.10,
    "tee": 0.25, "t-shirt": 0.25, "shirt": 0.30, "sweatshirt": 0.55,
    "shorts": 0.35, "pants": 0.55, "jeans": 0.70, "joggers": 0.50,
    "skirt": 0.35, "dress": 0.55,
    "sneakers": 0.90, "boots": 1.20, "sandals": 0.50, "slides": 0.40,
    "bag": 0.60, "backpack": 0.80, "hat": 0.15, "cap": 0.15,
    "belt": 0.20, "chain": 0.15, "watch": 0.25, "socks": 0.10,
    "default": 0.40,
}


def estimate_weight(category: str, quantity: int = 1) -> float:
    cat = (category or "default").lower()
    for key, weight in ITEM_WEIGHTS.items():
        if key in cat:
            return weight * quantity
    return ITEM_WEIGHTS["default"] * quantity


def ddp_shipping_cost(total_weight_kg: float) -> float:
    """Calculate DDP all-inclusive shipping cost to Africa by weight."""
    cost = total_weight_kg * DDP_SHIPPING_RATE_PER_KG
    return max(cost, DDP_MIN_SHIPPING)


# ── Variant Reverse-Mapping ─────────────────────────────────────
def reverse_map_to_chinese(product_id: str, color: str, size: str) -> dict:
    """
    Given a storefront product ID + English color/size,
    returns the exact Chinese variant text + source URL for purchasing.
    
    This is the CRITICAL function that enables automated procurement.
    The DDP agent needs the exact Chinese variant text to select the
    correct option on Weidian/1688/Taobao.
    
    Args:
        product_id: Storefront product slug (e.g. "heavy-vintage-wash-hoodie-abc123")
        color: English color name (e.g. "Black")
        size: English size (e.g. "L")
    
    Returns:
        dict with source_url, platform, item_id, chinese_color, chinese_size, cost_cny, seller_name
        Returns None if product not found in mappings.
    """
    if not SUPPLIER_MAPPINGS_FILE.exists():
        log.warning(f"supplier_mappings.json not found")
        return None
    
    try:
        mappings = json.loads(SUPPLIER_MAPPINGS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.error(f"Failed to load supplier mappings: {e}")
        return None
    
    product = mappings.get(product_id)
    if not product:
        log.warning(f"Product {product_id} not found in supplier mappings")
        return None
    
    variant_mappings = product.get("variant_mappings", {})
    color_mappings = variant_mappings.get("colors", {})
    size_mappings = variant_mappings.get("sizes", {})
    
    # Look up Chinese text for the English variant names
    chinese_color = color_mappings.get(color, "")
    chinese_size = size_mappings.get(size, "")
    
    # Case-insensitive fallback
    if not chinese_color:
        for en, zh in color_mappings.items():
            if en.lower() == color.lower():
                chinese_color = zh
                break
    if not chinese_size:
        for en, zh in size_mappings.items():
            if en.lower() == size.lower():
                chinese_size = zh
                break
    
    seller = product.get("seller", {})
    
    return {
        "source_url": product.get("source_url", ""),
        "platform": product.get("platform", ""),
        "item_id": product.get("item_id", ""),
        "chinese_color": chinese_color,
        "chinese_size": chinese_size,
        "english_color": color,
        "english_size": size,
        "cost_cny": product.get("cost_cny", 0),
        "seller_name": seller.get("name", "Unknown")
    }


# ── Main Fulfillment Engine ──────────────────────────────────────
class OrderFulfiller:

    def __init__(self):
        self.orders_file = ORDERS_DIR / "active_orders.json"
        self.orders = self._load_orders()

    def _load_orders(self) -> list:
        if self.orders_file.exists():
            try:
                return json.loads(self.orders_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _save_orders(self):
        self.orders_file.write_text(
            json.dumps(self.orders, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )

    # ── Main Entry Point: Called by Checkout Webhook ─────────────
    def create_order_from_checkout(self, checkout_data: dict) -> dict:
        """
        Process a checkout from the website.
        checkout_data should contain:
          - customer: {name, email, address, country}
          - items: [{name, product_id, url, size, color, qty, price_usd, price_cny, category, pipeline}]
          - subtotal_usd: float
          - shipping_paid_usd: float
        """
        order_id = "OBS-" + hashlib.md5(
            f"{checkout_data.get('customer',{}).get('email','')}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:10].upper()

        items = checkout_data.get("items", [])
        customer = checkout_data.get("customer", {})

        # Split items by pipeline
        ddp_items = [i for i in items if i.get("pipeline", "ddp_agent") != "cj"]
        cj_items  = [i for i in items if i.get("pipeline") == "cj"]

        # Calculate total DDP weight
        ddp_weight = sum(
            estimate_weight(i.get("category", "default"), i.get("qty", 1))
            for i in ddp_items
        )
        ddp_shipping = ddp_shipping_cost(ddp_weight) if ddp_items else 0

        # Build master order record
        order = {
            "order_id":   order_id,
            "created_at": datetime.now().isoformat(),
            "status":     OrderStatus.PENDING.value,
            "customer":   customer,
            "items":      items,
            "financials": {
                "subtotal_usd":         round(checkout_data.get("subtotal_usd", 0), 2),
                "shipping_paid_usd":    round(checkout_data.get("shipping_paid_usd", 0), 2),
                "ddp_weight_kg":        round(ddp_weight, 3),
                "ddp_shipping_est":     ddp_shipping,
                "total_usd":            round(
                    checkout_data.get("subtotal_usd", 0) +
                    checkout_data.get("shipping_paid_usd", 0), 2
                ),
            },
            "pipelines": {
                "ddp_agent": {
                    "items":      ddp_items,
                    "status":     "pending" if ddp_items else "not_applicable",
                    "purchase_briefs": [],
                    "tracking":   "",
                    "weight_kg":  ddp_weight,
                    "shipping_est": ddp_shipping,
                },
                "cj": {
                    "items":     cj_items,
                    "status":    "pending" if cj_items else "not_applicable",
                    "cj_order_id": "",
                    "tracking":  "",
                },
            },
            "is_mixed": bool(ddp_items and cj_items),
            "history": [{"timestamp": datetime.now().isoformat(), "event": "Order created from checkout"}],
        }

        self.orders.append(order)
        self._save_orders()

        log.info(f"📦 Order {order_id} created | {len(ddp_items)} DDP items ({ddp_weight:.2f}kg) | {len(cj_items)} CJ items")

        # Route to pipelines
        if ddp_items:
            self._route_ddp_agent(order)
        if cj_items:
            self._route_cj(order)

        return order

    # ── DDP Agent Pipeline (Alibaba Shipping Agent) ───────────────
    def _route_ddp_agent(self, order: dict):
        """
        Generate purchase briefs for DDP agent.
        Each brief contains the exact Chinese variant text needed to purchase
        the correct item on Weidian/1688/Taobao.
        """
        ddp = order["pipelines"]["ddp_agent"]
        items = ddp["items"]

        purchase_briefs = []
        embed_lines = [
            f"**🔴 NEW DDP ORDER — {order['order_id']}**\n",
            f"👤 **Customer:** {order['customer'].get('name', 'Unknown')}",
            f"📍 **Ship to:** {order['customer'].get('address', 'No address')}, {order['customer'].get('country', '')}",
            f"⚖️ **Total weight:** ~{ddp['weight_kg']:.2f}kg",
            f"🚚 **Shipping est:** ${ddp['shipping_est']:.2f} (DDP Air)\n",
            f"**━━━ PURCHASE BRIEF FOR DDP AGENT ━━━**",
        ]

        for i, item in enumerate(items, 1):
            product_id = item.get("product_id", "")
            color = item.get("color", "")
            size = item.get("size", "")
            
            # ── PHASE 5A: Reverse-map to Chinese variants ──
            chinese_variant = reverse_map_to_chinese(product_id, color, size)
            
            source_url = item.get("url", "")
            chinese_color = color
            chinese_size = size
            
            if chinese_variant:
                source_url = chinese_variant["source_url"] or source_url
                chinese_color = chinese_variant.get("chinese_color") or color
                chinese_size = chinese_variant.get("chinese_size") or size
            
            brief = {
                "item_number": i,
                "product_name": item.get("name", f"Item {i}"),
                "source_url": source_url,
                "platform": chinese_variant.get("platform", "unknown") if chinese_variant else "unknown",
                "select_color_chinese": chinese_color,
                "select_color_english": color,
                "select_size_chinese": chinese_size,
                "select_size_english": size,
                "quantity": item.get("qty", 1),
                "expected_cost_cny": item.get("price_cny", 0),
            }
            purchase_briefs.append(brief)
            
            qty = item.get("qty", 1)
            price_cny = item.get("price_cny", 0)
            
            embed_lines.append(
                f"\n**{i}. {item.get('name', 'Item')}**\n"
                f"   🔗 URL: {source_url[:80]}...\n"
                f"   🎨 Color: **{chinese_color}** (EN: {color})\n"
                f"   📏 Size: **{chinese_size}** (EN: {size})\n"
                f"   📦 Qty: {qty} | 💰 ¥{price_cny}"
            )

        embed_lines += [
            f"\n\n**━━━ SHIPPING INSTRUCTIONS ━━━**",
            f"📦 Consolidate all items into ONE shipment",
            f"✈️ Ship DDP Air Freight to customer address",
            f"🏷️ Declare as 'fashion clothing' / 'cotton garments'",
            f"💡 Customer shipping address is above",
        ]

        ddp["purchase_briefs"] = purchase_briefs
        ddp["status"] = "awaiting_purchase"
        self._update_status(order, OrderStatus.AWAITING_PAYMENT, "DDP purchase briefs generated")
        self._save_orders()

        self._send_discord_embed(
            title=f"🔴 DDP AGENT ORDER — {order['order_id']}",
            description="\n".join(embed_lines),
            color=0xFF4444
        )

        log.info(f"📋 Generated {len(purchase_briefs)} purchase briefs for DDP agent | Order {order['order_id']}")

    # ── CJ Dropshipping Pipeline ─────────────────────────────────
    def _route_cj(self, order: dict):
        """Auto-fulfill CJ items. CJ handles consolidation & shipping."""
        cj = order["pipelines"]["cj"]
        items = cj["items"]

        if not CJ_API_KEY:
            log.warning("CJ API key not set — order queued for manual setup")
            cj["status"] = "needs_api_key"
            self._send_discord_embed(
                title=f"🟡 CJ ORDER — {order['order_id']}",
                description=(
                    f"**{len(items)} CJ item(s) need auto-fulfillment**\n"
                    f"⚠️ CJ API key not configured — set CJ_API_KEY and CJ_EMAIL in .env\n"
                    f"Items: {', '.join(i.get('name','?') for i in items)}"
                ),
                color=0xFFAA00
            )
            self._save_orders()
            return

        try:
            # Authenticate with CJ
            auth = requests.post(
                f"{CJ_BASE_URL}/authentication/getAccessToken",
                json={"email": CJ_EMAIL, "password": CJ_API_KEY},
                timeout=30
            )
            token = auth.json().get("data", {}).get("accessToken", "")
            if not token:
                raise ValueError("CJ authentication failed")

            headers = {"CJ-Access-Token": token, "Content-Type": "application/json"}

            cj_products = [
                {"vid": i.get("cj_variant_id", ""), "quantity": i.get("qty", 1)}
                for i in items
            ]

            resp = requests.post(
                f"{CJ_BASE_URL}/shopping/order/createOrder",
                headers=headers,
                json={
                    "orderNumber":          order["order_id"],
                    "shippingCustomerName": order["customer"].get("name", ""),
                    "shippingAddress":      order["customer"].get("address", ""),
                    "products":             cj_products,
                },
                timeout=30
            )

            if resp.status_code == 200 and resp.json().get("result"):
                cj_id = resp.json()["data"]["orderId"]
                cj["cj_order_id"] = cj_id
                cj["status"] = "auto_fulfilled"
                self._update_status(order, OrderStatus.PURCHASED, f"CJ auto-fulfilled: {cj_id}")
                self._send_discord_msg(order, f"🟢 CJ AUTO-FULFILLED | CJ#{cj_id} | {len(items)} items")
            else:
                raise ValueError(f"CJ order failed: {resp.text[:200]}")

        except Exception as e:
            log.error(f"CJ pipeline error for {order['order_id']}: {e}")
            cj["status"] = "failed"
            cj["error"] = str(e)
            self._send_discord_embed(
                title=f"🔴 CJ FAILED — {order['order_id']}",
                description=f"Error: {str(e)[:300]}\n\nManual intervention needed.",
                color=0xFF0000
            )

        self._save_orders()

    # ── Status Management ────────────────────────────────────────
    def _update_status(self, order: dict, status: OrderStatus, event: str = ""):
        order["status"] = status.value
        order["history"].append({"timestamp": datetime.now().isoformat(), "event": event or status.value})
        self._save_orders()

    def mark_purchased(self, order_id: str):
        order = self._find(order_id)
        if order:
            if order["pipelines"].get("ddp_agent", {}).get("items"):
                order["pipelines"]["ddp_agent"]["status"] = "purchased"
            self._update_status(order, OrderStatus.PURCHASED, "Items purchased by DDP agent — waiting for consolidation")
            self._send_discord_msg(order, "💰 PAID — DDP agent has purchased all items")

    def mark_combining(self, order_id: str):
        """Call this when DDP agent confirms all items received and is packing."""
        order = self._find(order_id)
        if order:
            if order["pipelines"].get("ddp_agent", {}).get("items"):
                order["pipelines"]["ddp_agent"]["status"] = "combining"
            self._update_status(order, OrderStatus.COMBINING, "DDP agent consolidating shipment")
            self._send_discord_msg(order, "📦 DDP AGENT — All items received, consolidating for DDP shipment")

    def mark_shipped(self, order_id: str, tracking: str, pipeline: str = "kakobuy", method: str = ""):
        order = self._find(order_id)
        if order:
            order["pipelines"][pipeline]["tracking"] = tracking
            order["pipelines"][pipeline]["status"] = "shipped"
            order["pipelines"][pipeline]["shipping_method"] = method
            self._update_status(order, OrderStatus.SHIPPED, f"Shipped via {pipeline}: {tracking}")
            self._send_discord_msg(order, f"✈️ SHIPPED ({pipeline.upper()}) | {method or 'Standard'} | {tracking}")

    def get_dashboard(self) -> dict:
        return {
            "total":      len(self.orders),
            "by_status":  self._count_by("status"),
            "pipelines":  {
                "ddp_agent": len([o for o in self.orders if o["pipelines"].get("ddp_agent", {}).get("items")]),
                "cj":        len([o for o in self.orders if o["pipelines"].get("cj", {}).get("items")]),
                "mixed":     len([o for o in self.orders if o.get("is_mixed")]),
            },
            "pending_purchase": [
                o["order_id"] for o in self.orders
                if o["pipelines"].get("ddp_agent", {}).get("status") == "awaiting_purchase"
            ],
            "in_warehouse": [
                o["order_id"] for o in self.orders
                if o["status"] == OrderStatus.IN_WAREHOUSE.value
            ],
        }

    def _count_by(self, field: str) -> dict:
        counts = {}
        for o in self.orders:
            v = o.get(field, "unknown")
            counts[v] = counts.get(v, 0) + 1
        return counts

    def _find(self, order_id: str) -> dict:
        for o in self.orders:
            if o["order_id"] == order_id:
                return o
        log.warning(f"Order {order_id} not found")
        return None

    # ── Discord ──────────────────────────────────────────────────
    def _send_discord_msg(self, order: dict, message: str):
        if not DISCORD_WEBHOOK:
            return
        try:
            requests.post(DISCORD_WEBHOOK, json={
                "content": f"**{message}**\nOrder: `{order['order_id']}`"
            }, timeout=10)
        except Exception:
            pass

    def _send_discord_embed(self, title: str, description: str, color: int = 0x00FF88):
        if not DISCORD_WEBHOOK:
            return
        try:
            requests.post(DISCORD_WEBHOOK, json={"embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "footer": {"text": f"Obscura Fulfillment | {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
            }]}, timeout=10)
        except Exception:
            pass


# ── CLI ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, argparse

    parser = argparse.ArgumentParser(description="Obscura Fulfillment Engine")
    parser.add_argument("--dashboard", action="store_true")
    parser.add_argument("--mark-paid",       metavar="ORDER_ID")
    parser.add_argument("--mark-combining",  metavar="ORDER_ID")
    parser.add_argument("--mark-shipped",    nargs=3, metavar=("ORDER_ID","TRACKING","PIPELINE"))
    parser.add_argument("--checkout-file",    metavar="JSON_PATH", help="Process checkout from a JSON file")
    parser.add_argument("--test",            action="store_true")
    args = parser.parse_args()

    f = OrderFulfiller()

    if args.dashboard:
        print(json.dumps(f.get_dashboard(), indent=2))

    elif args.mark_paid:
        f.mark_purchased(args.mark_paid)

    elif args.mark_combining:
        f.mark_combining(args.mark_combining)

    elif args.mark_shipped:
        f.mark_shipped(args.mark_shipped[0], args.mark_shipped[1], args.mark_shipped[2])

    elif args.checkout_file:
        try:
            with open(args.checkout_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            order = f.create_order_from_checkout(data)
            print(f"SUCCESS_ORDER_ID:{order['order_id']}")
        except Exception as e:
            print(f"ERROR:{e}")
            sys.exit(1)

    elif args.test:
        # Simulate a mixed order
        test_checkout = {
            "customer": {
                "name": "Test Customer",
                "email": "test@obscura.store",
                "address": "14 Fashion St, Lagos, Nigeria",
                "country": "NG",
            },
            "items": [
                {
                    "name": "Heavy Vintage Wash Hoodie",
                    "product_id": "heavy-vintage-wash-hoodie-abc123",
                    "url": "https://weidian.com/item.html?itemID=7543891234",
                    "size": "L", "color": "Black", "qty": 1,
                    "price_usd": 48, "price_cny": 189,
                    "category": "hoodie", "pipeline": "ddp_agent"
                },
                {
                    "name": "Cargo Shorts",
                    "product_id": "cargo-shorts-def456",
                    "url": "https://weidian.com/item.html?itemID=999999",
                    "size": "M", "color": "Olive", "qty": 1,
                    "price_usd": 24, "price_cny": 89,
                    "category": "shorts", "pipeline": "ddp_agent"
                },
            ],
            "subtotal_usd": 72,
            "shipping_paid_usd": 15.00,
        }
        result = f.create_order_from_checkout(test_checkout)
        print(json.dumps(result, indent=2, default=str))
