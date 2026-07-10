import os
import sys
import asyncio
from playwright.async_api import async_playwright

# Force UTF-8 on Windows
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    print("=" * 60)
    print("TAOBAO/TMALL INTERACTIVE LOGIN HELPER")
    print("=" * 60)
    print("This script will open a visible browser window.")
    print("Please log in to your Taobao account in this window.")
    print("You can log in via QR code scan, SMS code, or password.")
    print("Once you are fully logged in and see the homepage, CLOSE the browser window.")
    print("=" * 60)
    
    async with async_playwright() as p:
        profile_dir = os.path.abspath("playwright_profile_sourcing")
        print(f"[*] Opening browser with persistent profile at:\n    {profile_dir}")
        
        # Launch headful browser
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            # Go to Taobao login
            await page.goto("https://login.taobao.com", wait_until="domcontentloaded", timeout=45000)
            print("[*] Browser window is open. Waiting for you to login and close the browser...")
            
            # Wait until user manually closes the browser
            await page.wait_for_event("close", timeout=0)
            print("[+] Browser closed by user.")
        except Exception as e:
            print(f"[-] Interaction completed: {e}")
        finally:
            await context.close()
            print("[+] Session saved successfully to persistent profile.")

if __name__ == "__main__":
    asyncio.run(main())
