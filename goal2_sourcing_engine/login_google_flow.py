import asyncio
import os
import json
from playwright.async_api import async_playwright

COOKIE_FILE = "google_cookies.json"

async def main():
    print("\n[+] Launching Browser...")
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
            print("Opening sign-in page...")
            await page.goto("https://labs.google/fx/api/auth/signin", wait_until="domcontentloaded", timeout=60000)
            
            print("\n[!] Please log in to Google Labs Flow.")
            print("[!] Keep this window open until you are fully logged in and see the Flow project canvas.")
            print("[!] Once you are logged in and ready, simply CLOSE the Chrome window.")
            
            # Wait for user to close browser manually
            await page.wait_for_event("close", timeout=0)
        except Exception as e:
            print(f"[!] Error or browser closed: {e}")
            
        print("\n[+] Saving cookies...")
        state = await context.storage_state()
        cookie_count = len(state.get("cookies", []))
        has_session = any("session" in c["name"].lower() for c in state.get("cookies", []))
        
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
            
        print(f"[+] Success! Saved {cookie_count} cookies to {COOKIE_FILE} (session token: {'YES' if has_session else 'NO'})")
        print("[+] The AI engine can now generate images autonomously.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
