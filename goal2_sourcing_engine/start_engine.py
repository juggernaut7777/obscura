import os
import sys
import time
import subprocess
import shlex

def print_banner():
    print("=" * 60)
    print("   OBSCURA GARMENTS — AUTONOMOUS ENGINE CONTROL CENTER")
    print("=" * 60)

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_banner()
        print("\nSYSTEM STATUS:")
        print("[OK] Trend Scrapers (Meta Ad Library + TikTok)")
        print("[OK] Competitor Spy (Ad Intel + Supplier Reverse Search)")
        print("[OK] Image Generation Pipeline (Google Flow Bridge)")
        print("[OK] Video Generation Pipeline (Kling AI Bridge)")
        print("[OK] Fashion Brain (Style Matching + Outfit Combos)")
        print("[OK] Pricing Engine (Stripe-only, no marketplace fees)")
        print("[OK] Social Auto-Poster (Anti-Shadowban Protected)")
        print("[OK] Auto-Fulfillment (Order -> CJ/Apliiq -> Ship)")

        print("\nSALES FLOW:")
        print("  IG/TikTok (organic traffic) -> OBSCURA Website (Stripe checkout)")

        print("\nCHOOSE AN ACTION:")
        print("1. Login to Social Media (IG, TikTok, Facebook)")
        print("2. Login to Kling AI (Video Generation)")
        print("3. Setup Social Profiles (OBSCURA branding)")
        print("4. Run Competitor Spy (Find winning products)")
        print("5. Run Factory Hunter (Find direct suppliers)")
        print("6. START 24/7 AUTONOMOUS LOOP")
        print("7. Push Code to VPS")
        print("8. Run End-to-End Pipeline Test")
        print("9. Run Stock Sync (Updates live stock/prices)")
        print("10. Compile captioned UGC Video Ad")
        print("11. Exit")

        try:
            choice = input("\nEnter choice (1-11): ").strip()

            if choice == '1':
                print("\n[*] Launching Social Media Login...")
                os.system("python login_socials.py")
            elif choice == '2':
                print("\n[*] Launching Kling AI Login...")
                os.system("python login_video.py")
            elif choice == '3':
                print("\n[*] Setting up OBSCURA branding on all platforms...")
                os.system("python profile_setup.py")
            elif choice == '4':
                print("\n[*] Running Competitor Spy...")
                os.system("python competitor_spy.py")
            elif choice == '5':
                print("\n[*] Running Factory Hunter...")
                os.system("python factory_hunter.py")
            elif choice == '6':
                print("\n[!!!] INITIATING 24/7 OBSCURA AUTONOMOUS ENGINE [!!!]")
                time.sleep(2)
                os.system("python agent_brain_local.py")
            elif choice == '7':
                print("\n[*] Pushing to VPS...")
                os.system("push_to_vps.bat")
            elif choice == '8':
                print("\n[*] Running End-to-End Pipeline Test...")
                os.system("python pipeline_test_runner.py --self-heal")
                input("\nPress Enter to return to main menu...")
            elif choice == '9':
                print("\n[*] Running Stock Sync...")
                os.system("python auto_stock_sync.py")
                input("\nPress Enter to return to main menu...")
            elif choice == '10':
                print("\n[*] UNIFIED UGC AD CREATOR [*]")
                prompt = input("Enter video prompt (e.g. Model wearing black hoodie walking down NYC street): ").strip()
                script = input("Enter narration script (e.g. Get the new Obscura heavy weight basic hoodie now): ").strip()
                refs = input("Enter reference image paths (optional, space separated): ").strip()
                cmd_list = ["python", "compile_ugc_ad.py", "--prompt", prompt, "--script", script]
                if refs:
                    cmd_list.extend(["--refs"] + refs.split())
                print(f"\n[*] Executing: {shlex.join(cmd_list)}")
                subprocess.run(cmd_list)
                input("\nPress Enter to return to main menu...")
            elif choice == '11':
                print("Exiting...")
                sys.exit(0)
            else:
                print("Invalid choice.")
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == "__main__":
    main()
