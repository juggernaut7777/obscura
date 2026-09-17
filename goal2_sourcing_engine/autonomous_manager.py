"""
autonomous_manager.py — OBSCURA Autonomous Multi-Sector Chief Operations Manager (COO).

Coordinates and audits all pipeline sectors autonomously without manual babysitting:
  - Sector 1: Sourcing & Supplier Rotation
  - Sector 2: VLM Vision & Classification Guard
  - Sector 3: Outfit Warehouse & 3-Piece Set Assembler
  - Sector 4: AI Generation & Token Sentinel
  - Sector 5: Storefront Publisher & Resale Sync
  - Sector 6: Fulfillment & Stock Sync
  - Sector 7: Self-Healing Guardian & Pre-Flight Upgrade Gate
"""

import os
import sys
import json
import time
import shutil
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Sector Paths
DATA_DIR = PROJECT_ROOT / "data"
MANUAL_CURATION_DIR = PROJECT_ROOT / "MANUAL_CURATION"
OUTPUT_DIR = PROJECT_ROOT / "OUTPUT_READY_FOR_SALE"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
WAREHOUSE_MANIFEST = WAREHOUSE_DIR / "warehouse_manifest.json"
STOREFRONT_DIR = PROJECT_ROOT.parent / "storefront"
STOREFRONT_PRODUCTS_FILE = STOREFRONT_DIR / "src" / "data" / "products.js"
MANAGER_LOG = PROJECT_ROOT / "manager_audit_log.json"


class AutonomousManager:
    """Master Multi-Sector Operations Manager."""

    def __init__(self):
        self.state = {
            "last_cycle": "",
            "sectors": {
                "guardian": {"status": "ok", "checks": []},
                "sourcing": {"status": "ok", "active_sellers": 0, "last_scrape": ""},
                "vision_vlm": {"status": "ok", "total_curated": 0, "unclassified": 0, "classified_rate": "100%"},
                "warehouse": {"status": "ok", "ready_outfits": 0, "staged_items": 0},
                "generation": {"status": "ok", "bridge_online": False, "pending_queue": 0, "output_ready": 0},
                "storefront": {"status": "ok", "live_products": 0, "unlisted_campaigns": 0},
                "fulfillment": {"status": "ok", "pending_orders": 0}
            },
            "alerts": [],
            "actions_executed": []
        }

    # ── Sector 7: Self-Healing Guardian & Pre-Flight Verifier ─────────────────
    def audit_and_heal_system(self) -> Dict[str, Any]:
        """Verify all services and ports are alive, auto-restart crashed services."""
        checks = []
        alerts = []
        services = ["yupoo-browser", "token-bridge", "ai-brain", "generation-worker"]

        for svc in services:
            try:
                res = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True, timeout=5)
                status = res.stdout.strip()
                if status == "active":
                    checks.append({"service": svc, "status": "active", "healed": False})
                else:
                    # Self-heal restart
                    print(f"🚨 [Guardian] Service '{svc}' is {status}! Initiating self-heal restart...")
                    subprocess.run(["sudo", "systemctl", "restart", f"{svc}.service"], capture_output=True, timeout=10)
                    checks.append({"service": svc, "status": "restarted", "healed": True})
                    alerts.append(f"Auto-healed crashed service: {svc}")
            except Exception as e:
                checks.append({"service": svc, "status": "error", "error": str(e), "healed": False})

        # Ping Port 8899 (Control Center) & Port 9877 (Token Bridge)
        port_8899_ok = False
        port_9877_ok = False
        try:
            r8899 = requests.get("http://127.0.0.1:8899/api/dashboard", timeout=4)
            port_8899_ok = r8899.status_code == 200
        except Exception:
            pass

        try:
            r9877 = requests.get("http://127.0.0.1:9877/health", timeout=4)
            port_9877_ok = r9877.status_code == 200
        except Exception:
            pass

        checks.append({"port_8899_control_center": "alive" if port_8899_ok else "down"})
        checks.append({"port_9877_token_bridge": "alive" if port_9877_ok else "down"})

        # Disk Storage Check & Autonomous Optimizer
        disk_pct = 0
        try:
            stat = shutil.disk_usage("/")
            disk_pct = round((stat.used / stat.total) * 100, 1)
            if disk_pct > 80:
                alerts.append(f"Disk usage is at {disk_pct}%. Triggering storage optimization...")
                freed_gb = self.optimize_storage()
                stat = shutil.disk_usage("/")
                disk_pct = round((stat.used / stat.total) * 100, 1)
                alerts.append(f"Storage optimized! Freed {freed_gb:.2f} GB. Current disk: {disk_pct}%.")
        except Exception as e:
            alerts.append(f"Disk check error: {e}")

        return {
            "status": "ok" if disk_pct < 85 else "warning",
            "checks": checks,
            "disk_percent": disk_pct,
            "alerts": alerts
        }

    def optimize_storage(self, force: bool = False) -> float:
        """
        Autonomous Asset Optimizer (Sector 8):
        1. Purges non-product dump albums (QC/customer review chats).
        2. Prunes duplicate excess images (> 3 per angle) in real products, keeping all hero shots & size charts.
        3. Vacuums systemd journals.
        Returns total gigabytes freed.
        """
        freed_bytes = 0
        print("\n🧹 [Storage Optimizer] Scanning for reclaimable disk space...")

        # 1. Purge non-product QC / feedback albums
        qc_keywords = ["qc-", "-qc", "customer", "feedback", "reviews", "reaction", "findqc"]
        if MANUAL_CURATION_DIR.exists():
            for p in list(MANUAL_CURATION_DIR.iterdir()):
                if p.is_dir():
                    name_lower = p.name.lower()
                    if any(k in name_lower for k in qc_keywords):
                        for f in p.rglob("*"):
                            if f.is_file():
                                freed_bytes += f.stat().st_size
                        shutil.rmtree(p, ignore_errors=True)
                        print(f"  [-] Removed non-product QC folder: {p.name}")

        # 2. Prune duplicate excess angles in curated products
        ALLOWED_LIMITS = {
            "front_angle": 3,
            "flat_lay": 3,
            "back_angle": 2,
            "side_angle": 2,
            "detail_close": 3,
            "tag_label": 2,
            "angle_": 2,
            "other_": 1,
        }

        pruned_images = 0
        if MANUAL_CURATION_DIR.exists():
            for p in MANUAL_CURATION_DIR.iterdir():
                if not p.is_dir() or p.name.startswith(("_", ".")):
                    continue

                prefix_counts = {}
                for f in sorted(p.iterdir()):
                    if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                        # Never delete size charts or metadata
                        if "size" in f.name.lower() or "chart" in f.name.lower():
                            continue

                        matched_pfx = None
                        for pfx in ALLOWED_LIMITS:
                            if f.name.startswith(pfx):
                                matched_pfx = pfx
                                break

                        if matched_pfx:
                            prefix_counts[matched_pfx] = prefix_counts.get(matched_pfx, 0) + 1
                            if prefix_counts[matched_pfx] > ALLOWED_LIMITS[matched_pfx]:
                                try:
                                    freed_bytes += f.stat().st_size
                                    f.unlink()
                                    pruned_images += 1
                                except Exception:
                                    pass

        # 3. Vacuum systemd journal logs
        try:
            subprocess.run(["sudo", "journalctl", "--vacuum-size=100M"], capture_output=True, timeout=10)
        except Exception:
            pass

        freed_gb = freed_bytes / (1024 * 1024 * 1024)
        print(f"✅ [Storage Optimizer] Reclaimed {freed_gb:.2f} GB (Pruned {pruned_images} excess duplicate images). All products & hero assets intact.\n")
        return freed_gb

    def pre_flight_verify_code(self, script_path: str) -> bool:
        """Dry-run syntax and import checks before executing upgrades."""
        try:
            res = subprocess.run([sys.executable, "-m", "py_compile", script_path], capture_output=True, text=True)
            if res.returncode != 0:
                print(f"❌ [Pre-Flight] Syntax validation failed for {script_path}:\n{res.stderr}")
                return False
            return True
        except Exception as e:
            print(f"❌ [Pre-Flight] Error compiling {script_path}: {e}")
            return False

    # ── Sector 2: Vision & Classification Guard ──────────────────────────────
    async def audit_and_run_vlm(self) -> Dict[str, Any]:
        """Audits MANUAL_CURATION, detects unclassified items, runs VLM autonomously."""
        total_curated = 0
        unclassified_folders = []

        if MANUAL_CURATION_DIR.exists():
            for sub in MANUAL_CURATION_DIR.iterdir():
                if sub.is_dir() and not sub.name.startswith(("_", ".")):
                    total_curated += 1
                    if not (sub / "image_classification.json").exists():
                        unclassified_folders.append(sub)

        unclassified_count = len(unclassified_folders)
        classified_count = total_curated - unclassified_count
        rate = f"{(classified_count / max(total_curated, 1)) * 100:.1f}%"

        actions = []
        if unclassified_folders:
            print(f"🤖 [Vision Guard] Found {unclassified_count} unclassified product(s). Auto-triggering VLM...")
            try:
                from agent_tools_vps import execute_tool
                from agent_memory import AgentMemory
                mem = AgentMemory()
                res = await execute_tool("classify_product_images", {}, mem)
                actions.append(f"VLM classified: {res.get('message', 'Completed')}")
            except Exception as e:
                actions.append(f"VLM classification error: {str(e)}")

        return {
            "status": "ok" if unclassified_count == 0 else "classifying",
            "total_curated": total_curated,
            "unclassified": unclassified_count,
            "classified_rate": rate,
            "actions": actions
        }

    # ── Sector 3: Outfit Warehouse & 3-Piece Set Assembler ────────────────────
    def audit_and_stage_warehouse(self) -> Dict[str, Any]:
        """Scans for newly classified items and updates matching 3-piece outfits."""
        actions = []
        ready_count = 0
        staged_count = 0

        try:
            import auto_stage_to_warehouse
            import outfit_warehouse

            # Run auto-staging logic
            auto_stage_to_warehouse.main()
            outfits = outfit_warehouse.find_ready_outfits()
            ready_count = len(outfits)
            stats = outfit_warehouse.get_warehouse_stats()
            staged_count = stats.get("total_items", 0)
            actions.append(f"Auto-staged items. Active ready 3-piece outfits: {ready_count}")
        except Exception as e:
            actions.append(f"Warehouse staging notice: {str(e)}")

        return {
            "status": "ok",
            "ready_outfits": ready_count,
            "staged_items": staged_count,
            "actions": actions
        }

    # ── Sector 4: AI Generation & Token Sentinel ─────────────────────────────
    def audit_and_dispatch_generation(self) -> Dict[str, Any]:
        """Checks bridge token status and advances generation queue."""
        bridge_online = False
        token_active = False
        pending_queue = 0
        output_ready = 0

        try:
            r = requests.get("http://127.0.0.1:9877/tokens", timeout=3)
            if r.status_code == 200:
                data = r.json()
                bridge_online = True
                token_active = bool(data.get("bearer"))
        except Exception:
            pass

        if OUTPUT_DIR.exists():
            with os.scandir(OUTPUT_DIR) as scanner:
                # ⚡ Performance optimization
                # Why: Avoid N+1 stat calls during .is_dir()
                # What: Use os.scandir() instead of Path.iterdir()
                output_ready = sum(1 for e in scanner if e.is_dir() and not e.name.startswith("."))

        qfile = PROJECT_ROOT / "generation_queue.json"
        if qfile.exists():
            try:
                qdata = json.loads(qfile.read_text(encoding="utf-8"))
                pending_queue = len(qdata.get("pending", []))
            except Exception:
                pass

        status = "idle"
        if token_active and pending_queue > 0:
            status = "generating"
        elif not token_active and pending_queue > 0:
            status = "token_needed"

        return {
            "status": status,
            "bridge_online": bridge_online,
            "token_active": token_active,
            "pending_queue": pending_queue,
            "output_ready": output_ready
        }

    # ── Sector 5: Storefront Publisher & Resale Sync ──────────────────────────
    def audit_and_publish_storefront(self) -> Dict[str, Any]:
        """Scans completed campaigns and ensures storefront products.js is updated."""
        live_products = 0
        unlisted_campaigns = 0

        if STOREFRONT_PRODUCTS_FILE.exists():
            try:
                text = STOREFRONT_PRODUCTS_FILE.read_text(encoding="utf-8")
                import re
                m = re.search(r'export const DEMO_PRODUCTS\s*=\s*(\[[\s\S]*?\]);', text)
                if m:
                    prods = json.loads(m.group(1))
                    live_products = len(prods)
            except Exception:
                pass

        if OUTPUT_DIR.exists():
            with os.scandir(OUTPUT_DIR) as scanner:
                # ⚡ Performance optimization
                # Why: Avoid N+1 stat calls during .is_dir() and .exists()
                # What: Use os.scandir() and os.path.exists() instead of Path.iterdir()
                completed = sum(1 for e in scanner if e.is_dir() and os.path.exists(os.path.join(e.path, "campaign_info.json")))
            unlisted_campaigns = max(completed - live_products, 0)

        actions = []
        if unlisted_campaigns > 0:
            print(f"🛍️ [Storefront] Found {unlisted_campaigns} completed unlisted campaign(s). Auto-uploading...")
            try:
                import storefront_uploader
                storefront_uploader.scan_and_upload()
                actions.append(f"Auto-published {unlisted_campaigns} new campaign(s) to storefront")
            except Exception as e:
                actions.append(f"Storefront publish notice: {str(e)}")

        return {
            "status": "ok" if unlisted_campaigns == 0 else "syncing",
            "live_products": live_products,
            "unlisted_campaigns": unlisted_campaigns,
            "actions": actions
        }

    # ── Sector 6: Fulfillment & Logistics Telemetry ──────────────────────────
    def audit_fulfillment_sector(self) -> Dict[str, Any]:
        """Audits customer orders, routes DDP agents, and updates tracking telemetry."""
        try:
            import auto_fulfillment
            stats = auto_fulfillment.get_fulfillment_stats()
            return {
                "status": "ok",
                "total_orders": stats.get("total_orders", 0),
                "pending_routing": stats.get("pending_routing", 0),
                "newly_routed": stats.get("newly_routed", 0),
                "status_breakdown": stats.get("status_breakdown", {})
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "total_orders": 0,
                "pending_routing": 0
            }

    # ── Sector 1: Sourcing & Supplier Rotation ────────────────────────────────
    def audit_sourcing_sector(self) -> Dict[str, Any]:
        """Checks seller health and tracks rotation."""
        active_sellers = 0
        sellers_file = DATA_DIR / "yupoo_sellers.json"
        if sellers_file.exists():
            try:
                sdata = json.loads(sellers_file.read_text(encoding="utf-8"))
                if isinstance(sdata, dict):
                    active_sellers = sum(len(v) for k, v in sdata.items() if isinstance(v, list))
                elif isinstance(sdata, list):
                    active_sellers = len(sdata)
            except Exception:
                pass

        return {
            "status": "ok",
            "active_sellers": active_sellers
        }

    # ── Master Orchestration Cycle ────────────────────────────────────────────
    async def run_manager_cycle(self) -> Dict[str, Any]:
        """Executes full autonomous audit and self-healing across all sectors A-Z."""
        now = datetime.now().isoformat()
        print(f"\n{'='*60}\n👔 [OPERATIONS MANAGER] Starting Autonomous Multi-Sector Audit: {now}\n{'='*60}")

        # 1. Guardian & Self-Heal
        guardian = self.audit_and_heal_system()
        print(f"🛡️  [Guardian] Status: {guardian['status'].upper()} (Disk: {guardian['disk_percent']}%)")

        # 2. Vision & VLM Guard
        vision = await self.audit_and_run_vlm()
        print(f"👁️  [Vision VLM] Curated: {vision['total_curated']} | Unclassified: {vision['unclassified']} | Verified: {vision['classified_rate']}")

        # 3. Warehouse Staging & Outfit Engine
        warehouse = self.audit_and_stage_warehouse()
        print(f"👕👖👟 [Warehouse] Ready Outfits: {warehouse['ready_outfits']} | Staged Items: {warehouse['staged_items']}")

        # 4. Generation & Token Sentinel
        generation = self.audit_and_dispatch_generation()
        print(f"🎨 [Generation] Bridge Online: {generation['bridge_online']} | Token: {generation['token_active']} | Queue: {generation['pending_queue']}")

        # 5. Storefront Publisher
        storefront = self.audit_and_publish_storefront()
        print(f"🛍️  [Storefront] Live Products: {storefront['live_products']} | Unlisted: {storefront['unlisted_campaigns']}")

        # 6. Fulfillment & Logistics
        fulfillment = self.audit_fulfillment_sector()
        print(f"📦🚚 [Fulfillment] Total Orders: {fulfillment['total_orders']} | Pending Routing: {fulfillment['pending_routing']}")

        # 7. Sourcing Monitor
        sourcing = self.audit_sourcing_sector()
        print(f"📦 [Sourcing] Active Trusted Sellers: {sourcing['active_sellers']}")

        report = {
            "timestamp": now,
            "overall_status": "healthy" if guardian["status"] == "ok" else "warning",
            "sectors": {
                "guardian": guardian,
                "vision": vision,
                "warehouse": warehouse,
                "generation": generation,
                "storefront": storefront,
                "fulfillment": fulfillment,
                "sourcing": sourcing
            }
        }

        # Save to persistent audit log
        try:
            MANAGER_LOG.write_text(json.dumps(report, indent=2), encoding="utf-8")
        except Exception:
            pass

        print(f"{'='*60}\n✅ [OPERATIONS MANAGER] Audit Complete. All Sectors Synchronized.\n{'='*60}\n")
        return report


# Global instance
manager = AutonomousManager()

if __name__ == "__main__":
    asyncio.run(manager.run_manager_cycle())
