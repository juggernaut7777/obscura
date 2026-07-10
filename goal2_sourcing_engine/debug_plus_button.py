"""
Debug script: Opens Flow, clicks '+', takes a screenshot so we can SEE what's there.
Also dumps every single element near the picker area.
"""
import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.async_api import async_playwright

PROFILE = os.path.join(os.path.dirname(__file__), "playwright_debug_profile")

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            PROFILE,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("Navigating to Flow...")
        try:
            await page.goto("https://labs.google/fx/tools/flow", timeout=120000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"Nav error (may be OK): {e}")

        await asyncio.sleep(8)
        
        # Take screenshot of current state
        await page.screenshot(path="debug_step0_loaded.png", full_page=False)
        print("Saved: debug_step0_loaded.png")

        # Find the prompt box
        FIND_PROMPT_JS = """() => {
            function findInShadow(root, depth) {
                if (depth > 10) return null;
                const all = root.querySelectorAll('*');
                for (const el of all) {
                    const ph = el.getAttribute('placeholder') || '';
                    const al = el.getAttribute('aria-label') || '';
                    const ce = el.getAttribute('contenteditable');
                    if ((ph.toLowerCase().includes('create') || al.toLowerCase().includes('create') ||
                         ph.toLowerCase().includes('prompt') || al.toLowerCase().includes('prompt'))
                        && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || ce === 'true' || el.tagName === 'DIV')) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 100 && rect.height > 10) {
                            return {found: true, rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height}};
                        }
                    }
                    if (el.shadowRoot) {
                        const found = findInShadow(el.shadowRoot, depth + 1);
                        if (found) return found;
                    }
                }
                return null;
            }
            return findInShadow(document, 0) || {found: false};
        }"""

        result = await page.evaluate(FIND_PROMPT_JS)
        print(f"Prompt box: {result}")

        if result.get('found') and result.get('rect'):
            r = result['rect']
            plus_x = r['x'] - 30
            plus_y = r['y'] + r['height'] / 2
            print(f"Clicking '+' at ({int(plus_x)}, {int(plus_y)})")
            await page.mouse.click(plus_x, plus_y)
            await asyncio.sleep(3)

            # Take screenshot AFTER clicking +
            await page.screenshot(path="debug_step1_plus_clicked.png", full_page=False)
            print("Saved: debug_step1_plus_clicked.png")

            # Dump EVERY visible element in the picker area
            elements = await page.evaluate("""() => {
                function findInShadow(root, depth) {
                    if (depth > 10) return [];
                    const results = [];
                    const all = root.querySelectorAll('*');
                    for (const el of all) {
                        if (el.offsetParent !== null || el.offsetWidth > 0) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 10 && rect.height > 10 && rect.top > 200) {
                                const text = (el.textContent || '').trim().substring(0, 50);
                                const tag = el.tagName;
                                const cls = (el.className || '').toString().substring(0, 40);
                                const aria = el.getAttribute('aria-label') || '';
                                const role = el.getAttribute('role') || '';
                                const src = el.src || '';
                                const bgImg = el.style ? el.style.backgroundImage || '' : '';
                                
                                if (tag === 'IMG' || tag === 'BUTTON' || tag === 'A' || 
                                    role || aria || text.length < 30 || src || bgImg) {
                                    results.push({
                                        tag, cls: cls.substring(0, 30), text: text.substring(0, 30),
                                        aria, role, src: src.substring(0, 50), bgImg: bgImg.substring(0, 50),
                                        x: Math.round(rect.x), y: Math.round(rect.y),
                                        w: Math.round(rect.width), h: Math.round(rect.height)
                                    });
                                }
                            }
                        }
                        if (el.shadowRoot) {
                            results.push(...findInShadow(el.shadowRoot, depth + 1));
                        }
                    }
                    return results;
                }
                return findInShadow(document, 0);
            }""")

            print(f"\n=== {len(elements)} VISIBLE ELEMENTS AFTER CLICKING + ===")
            for el in elements:
                if el['tag'] == 'IMG':
                    print(f"  [IMG] pos=({el['x']},{el['y']}) size={el['w']}x{el['h']} src={el['src']}")
                elif el['role'] or el['aria']:
                    print(f"  [{el['tag']}] pos=({el['x']},{el['y']}) size={el['w']}x{el['h']} role={el['role']} aria={el['aria']} text={el['text']}")
                elif el['tag'] == 'BUTTON' or el['tag'] == 'A':
                    print(f"  [{el['tag']}] pos=({el['x']},{el['y']}) size={el['w']}x{el['h']} text={el['text']}")
        else:
            print("Could not find prompt box!")

        await asyncio.sleep(2)
        await browser.close()
        print("\nDone! Check the debug_*.png files.")

asyncio.run(debug())
