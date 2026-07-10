import asyncio
from playwright.async_api import async_playwright
import os

# Safe print
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

async def main():
    profile_dir = os.path.abspath("playwright_profile_meta")
    safe_print("=" * 60)
    safe_print("     OBSCURA META AI SESSION INITIALIZER")
    safe_print("=" * 60)
    safe_print(f"[*] Opening browser with persistent profile at:\n    {profile_dir}")
    safe_print("[*] Launching browser window on your desktop...")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=["--disable-blink-features=AutomationControlled"],
            channel="chrome"
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            safe_print("\n[*] Navigating to Meta AI...")
            await page.goto("https://www.meta.ai/", wait_until="domcontentloaded", timeout=60000)
            
            safe_print("\n" + "!" * 50)
            safe_print("[!] ACTION REQUIRED: Please log into your Meta/Facebook Account.")
            safe_print("[!]")
            safe_print("[!] Once you are fully logged in and can generate images/videos,")
            safe_print("[!] simply CLOSE the browser window to save your session.")
            safe_print("!" * 50 + "\n")
            
            # Wait for browser/page to close
            await page.wait_for_event("close", timeout=0)
        except Exception as e:
            safe_print(f"[!] Browser closed or encountered error: {e}")
            
        await context.close()
        safe_print("[OK] Session successfully saved! Meta AI can now run headlessly.")

if __name__ == "__main__":
    asyncio.run(main())
