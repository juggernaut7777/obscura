import asyncio
import os
import sys
import json
from pathlib import Path
from playwright.async_api import async_playwright

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding, errors='replace'))
        except Exception:
            print('[Print Error] Unable to encode output print message.')

print = safe_print

async def main():
    print("=" * 60)
    print("      🎨 DREAMINA (SEEDANCE 2.0) COOKIE HARVESTER")
    print("============================================================\n")
    print("This script will help you capture cookies for your 7 Google Accounts")
    print("so the pipeline can automatically rotate them for unlimited free videos.\n")
    
    # Prompt user for account number (1-7)
    while True:
        try:
            account_num = input("Enter Google Account slot to log in (1-7): ").strip()
            if account_num in [str(i) for i in range(1, 8)]:
                break
            print("❌ Invalid selection. Please enter a number between 1 and 7.")
        except KeyboardInterrupt:
            print("\nAborted.")
            return

    cookie_file = os.path.expanduser(f"~/.dreamina_cookies_{account_num}.json")
    print(f"\n[+] Preparing browser for Google Account #{account_num}...")
    print(f"[+] Cookies will be saved to: {cookie_file}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("[🌐] Opening Dreamina...")
            await page.goto("https://dreamina.com/create/image-to-video", wait_until="domcontentloaded", timeout=60000)
            
            print("\n" + "!" * 50)
            print(f"[!] PLEASE SIGN IN WITH GOOGLE ACCOUNT #{account_num} NOW.")
            print("[!] Keep this window open until you see the Dreamina canvas/interface.")
            print("[!] Once you are fully logged in and ready, simply CLOSE the browser window.")
            print("!" * 50 + "\n")
            
            # Wait for user to close browser manually
            await page.wait_for_event("close", timeout=0)
        except Exception as e:
            print(f"[!] Browser closed or error: {e}")
            
        print("\n[+] Capturing storage state...")
        state = await context.storage_state()
        
        # Verify if we captured cookies
        cookie_count = len(state.get("cookies", []))
        has_session = any("session" in c["name"].lower() or "token" in c["name"].lower() or "auth" in c["name"].lower() for c in state.get("cookies", []))
        
        if cookie_count > 0:
            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            print(f"✅ Success! Saved {cookie_count} cookies to {cookie_file} (Authentication elements: {'YES' if has_session else 'NO'})")
        else:
            print("❌ Error: No cookies found. Did you close the window before loading was complete?")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
