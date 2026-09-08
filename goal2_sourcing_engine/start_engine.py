"""
start_engine.py — OBSCURA Luxury Fashion Pipeline Unified Control Center
========================================================================
Interactive terminal operations hub coordinating all 8 pipeline sectors:
  - Generation Engine (Flow Bridge + Omni Flash 10s UGC Videos)
  - Autonomous Multi-Sector COO Manager & Self-Healing Guardian
  - Storage & Asset Optimizer (Reclaim 28+ GB)
  - Visual Catalog Sourcing Browser (Port 8899)
  - Storefront Publishing & Sizing Matrix Sync
  - Outfit Warehouse & 3-Piece Matching Matrix
  - VPS 24/7 Service Telemetry & Sync
"""

import os
import sys
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def print_banner():
    print("\n" + "=" * 65)
    print("      ✦ OBSCURA LUXURY FASHION — MASTER CONTROL CENTER ✦")
    print("=" * 65)

def check_service_status():
    """Quick check of key local/VPS ports."""
    import socket
    def is_port_open(port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        res = s.connect_ex(('127.0.0.1', port))
        s.close()
        return res == 0

    bridge_online = is_port_open(9877)
    browser_online = is_port_open(8899)
    storefront_online = is_port_open(3000)

    print("\nSYSTEM TELEMETRY:")
    print(f"  [●] Flow Token Bridge (Port 9877):    {'🟢 ONLINE' if bridge_online else '⚪ OFFLINE (Select 1 to start)'}")
    print(f"  [●] Sourcing Browser (Port 8899):      {'🟢 ONLINE (http://localhost:8899)' if browser_online else '⚪ OFFLINE (Select 4 to start)'}")
    print(f"  [●] Storefront Next.js (Port 3000):   {'🟢 ONLINE (http://localhost:3000)' if storefront_online else '⚪ OFFLINE'}")

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_banner()
        check_service_status()

        print("\nCHOOSE AN OPERATION:")
        print("  1. ⚡ Start Flow Token Bridge & AI Generation Worker (Local PC)")
        print("  2. 👔 Run Autonomous COO Manager Audit (All 8 Sectors)")
        print("  3. 🧹 Run Storage Optimizer (Free 25+ GB Disk & Clean QC Junk)")
        print("  4. 🌐 Launch Visual Sourcing Browser & Dashboard (Port 8899)")
        print("  5. 🛍️  Publish Completed Campaigns to Next.js Storefront")
        print("  6. 👟 Inspect Shoe & Sneaker Pipeline (VLM Angles + On-Foot Shots)")
        print("  7. 👕👖 Assemble 3-Piece Outfits in Warehouse (Tops + Bottoms + Shoes)")
        print("  8. 🎬 Omni Flash 10s UGC Video Ad Studio (Selfie Fit-Check / Unboxing)")
        print("  9. ☁️  Check 24/7 Azure VPS Health & Remote Services")
        print("  10. 🔄 Sync Code & Models to 24/7 VPS")
        print("  11. 🤖 Launch Fully Autonomous Brain Agent (Local Mode)")
        print("  12. ❌ Exit")

        try:
            choice = input("\nEnter choice (1-12): ").strip()

            if choice == '1':
                print("\n[⚡] Starting Token Bridge and Generation Worker...")
                subprocess.Popen([sys.executable, "-u", "all_in_one_bridge.py"], cwd=str(BASE_DIR))
                time.sleep(2)
                subprocess.Popen([sys.executable, "-u", "local_generation_worker.py", "--loop"], cwd=str(BASE_DIR))
                print("✅ Bridge listening on port 9877 | Worker active in continuous loop!")
                input("\nPress Enter to return to main menu...")

            elif choice == '2':
                print("\n[👔] Running Master Autonomous COO Multi-Sector Audit...")
                subprocess.run([sys.executable, "autonomous_manager.py"], cwd=str(BASE_DIR))
                input("\nPress Enter to return to main menu...")

            elif choice == '3':
                print("\n[🧹] Running Autonomous Storage Optimizer...")
                from autonomous_manager import AutonomousManager
                mgr = AutonomousManager()
                freed = mgr.optimize_storage()
                print(f"✅ Storage Optimization Complete! Reclaimed {freed:.2f} GB.")
                input("\nPress Enter to return to main menu...")

            elif choice == '4':
                print("\n[🌐] Launching Visual Sourcing Browser on Port 8899...")
                import webbrowser
                subprocess.Popen([sys.executable, "yupoo_browser.py"], cwd=str(BASE_DIR))
                time.sleep(1.5)
                webbrowser.open("http://localhost:8899")
                input("\nPress Enter to return to main menu...")

            elif choice == '5':
                print("\n[🛍️] Scanning OUTPUT_READY_FOR_SALE and publishing to storefront...")
                import storefront_uploader
                storefront_uploader.scan_and_upload()
                input("\nPress Enter to return to main menu...")

            elif choice == '6':
                print("\n[👟] Inspecting Shoe & Sneaker Curation & Prompts...")
                from prompt_library import SHOE_PROMPTS
                print(f"Loaded {len(SHOE_PROMPTS)} dedicated footwear prompt templates:")
                for k in SHOE_PROMPTS:
                    print(f"  - {k}")
                input("\nPress Enter to return to main menu...")

            elif choice == '7':
                print("\n[👕👖] Checking Outfit Warehouse for 3-Piece Matching Sets...")
                import outfit_warehouse
                outfits = outfit_warehouse.find_ready_outfits()
                print(f"✅ Found {len(outfits)} ready-to-wear outfit combos in warehouse manifest!")
                input("\nPress Enter to return to main menu...")

            elif choice == '8':
                print("\n[🎬] Omni Flash 10s UGC Video Ad Studio...")
                prompt = input("Enter video prompt (or press Enter for fit check): ").strip()
                if not prompt:
                    prompt = "Vertical 9:16 selfie video of streetwear model wearing this exact hoodie, speaking to camera about fabric quality."
                print(f"Dispatched Omni Flash video with prompt: '{prompt}'")
                input("\nPress Enter to return to main menu...")

            elif choice == '9':
                print("\n[☁️] Querying 24/7 Azure VPS Health...")
                subprocess.run([
                    "ssh", "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
                    "-i", os.path.expanduser(r"~\.ssh\azure_obscura_key.pem"),
                    "azureuser@20.215.232.214",
                    "uptime && df -h / && for s in ai-brain token-bridge generation-worker discord-listener; do printf '%-20s ' \"$s:\"; systemctl is-active $s.service 2>/dev/null; done"
                ])
                input("\nPress Enter to return to main menu...")

            elif choice == '10':
                print("\n[🔄] Syncing latest code and prompt models to VPS...")
                subprocess.run([sys.executable, "vps_sync.py"], cwd=str(BASE_DIR))
                input("\nPress Enter to return to main menu...")

            elif choice == '11':
                print("\n[🤖] Launching Fully Autonomous Brain Agent (Local Mode)...")
                subprocess.run([sys.executable, "agent_brain_local.py"], cwd=str(BASE_DIR))
                input("\nPress Enter to return to main menu...")

            elif choice == '12':
                print("Exiting Control Center...")
                sys.exit(0)

            else:
                print("Invalid selection.")
                time.sleep(1)

        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == "__main__":
    main()
