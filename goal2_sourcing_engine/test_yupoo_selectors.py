import asyncio
import os
import sys
from playwright.async_api import async_playwright

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8"))
        except Exception:
            print(text.encode("utf-8", errors="ignore").decode("ascii", errors="ignore"))

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://goat-official.x.yupoo.com/albums"
        safe_print(f"Navigating to {url} with wait_until='commit'...")
        try:
            await page.goto(url, wait_until="commit", timeout=20000)
            safe_print("Navigation commit done. Waiting for content...")
            await asyncio.sleep(5)
        except Exception as e:
            safe_print(f"Navigation or wait error: {e}")
            
        # Print page title
        title = await page.title()
        safe_print(f"Page Title: {title}")
        
        # Test selectors
        album_main = await page.query_selector_all(".album__main")
        album_href = await page.query_selector_all("a[href*='/albums/']")
        all_links = await page.query_selector_all("a")
        
        safe_print(f"Found with .album__main: {len(album_main)}")
        safe_print(f"Found with a[href*='/albums/']: {len(album_href)}")
        safe_print(f"Total links on page: {len(all_links)}")
        
        # Take a screenshot to inspect
        screenshot_path = "test_screenshot.png"
        await page.screenshot(path=screenshot_path)
        safe_print(f"Screenshot saved to {screenshot_path}")
        
        # Print all links that look like album or category links
        safe_print("\n--- ANALYZING LINKS ---")
        matched_links = []
        for i, a in enumerate(all_links):
            href = await a.get_attribute("href")
            text = (await a.inner_text() or "").strip()
            if href:
                href_lower = href.lower()
                if "/albums" in href_lower or "/categories" in href_lower or href.startswith("/"):
                    matched_links.append((href, text, a))
        
        safe_print(f"Found {len(matched_links)} matching links:")
        for idx, (href, text, a) in enumerate(matched_links[:40]):
            html = await page.evaluate("el => el.outerHTML", a)
            safe_print(f"Match {idx+1}: href={href} | text={text[:30]} | html={html[:120]}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
