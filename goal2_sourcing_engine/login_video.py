import asyncio
from playwright.async_api import async_playwright
import os
import json

KLING_COOKIE_FILE = os.path.expanduser('~/.kling_cookies.json')

async def main():
    print('\n[+] Launching Browser...')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        try:
            await page.goto('https://klingai.com')
            await asyncio.sleep(5)
            if "kuaishou.com" in page.url:
                print('[!] Redirected to Chinese domain. Attempting migration to global site...')
                migration_btn = page.locator("text=Go to klingai.com").or_(page.locator("a:has-text('Go to klingai.com')")).first
                if await migration_btn.count() > 0:
                    await migration_btn.click()
                    await asyncio.sleep(2)
            print('[!] Please log in to Kling AI now.')
            print('[!] Keep this window open until you are fully logged in.')
            print('[!] Once you are on the main dashboard, simply CLOSE the Chrome window.')
            
            # Wait for the user to close the page manually
            await page.wait_for_event('close', timeout=0)
        except Exception:
            pass
            
        print('\n[+] Saving cookies...')
        state = await context.storage_state()
        with open(KLING_COOKIE_FILE, 'w') as f:
            json.dump(state, f)
            
        print(f'[+] Success! Cookies saved to {KLING_COOKIE_FILE}')
        print('[+] The AI engine can now generate videos autonomously.')
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
