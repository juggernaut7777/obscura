import asyncio
from playwright.async_api import async_playwright
import os
import json

async def login_platform(p, platform_name, url, cookie_file):
    print(f'\n[+] Launching Browser for {platform_name}...')
    browser = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    context = await browser.new_context(viewport={'width': 1280, 'height': 720})
    page = await context.new_page()
    
    try:
        await page.goto(url)
        print(f'[!] Please log in to {platform_name}.')
        print(f'[!] Once you are fully logged in and see your feed/dashboard, CLOSE the browser window.')
        
        # Wait for user to close the browser manually
        await page.wait_for_event('close', timeout=0)
    except Exception as e:
        # Ignore target closed errors when they manually close it
        pass
        
    print(f'\n[+] Saving {platform_name} cookies...')
    state = await context.storage_state()
    with open(cookie_file, 'w') as f:
        json.dump(state, f)
        
    print(f'[+] Success! {platform_name} cookies saved to {cookie_file}')
    await browser.close()

async def main():
    async with async_playwright() as p:
        # Instagram
        await login_platform(p, 'Instagram', 'https://www.instagram.com', os.path.expanduser('~/.ig_cookies.json'))
        
        # TikTok
        await login_platform(p, 'TikTok', 'https://www.tiktok.com/login', os.path.expanduser('~/.tiktok_cookies.json'))
        
        # Facebook
        await login_platform(p, 'Facebook', 'https://www.facebook.com', os.path.expanduser('~/.fb_cookies.json'))
        
        print('\n[✅] All social media accounts logged in and cookies saved!')
        
if __name__ == "__main__":
    asyncio.run(main())
