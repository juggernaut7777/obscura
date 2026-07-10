"""
Debug 3 — Use Playwright's shadow-piercing methods to find the hidden prompt box.
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def debug():
    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        user_data_dir=os.path.abspath("playwright_profile"),
        headless=False,
        viewport={"width": 900, "height": 600},
        args=["--disable-blink-features=AutomationControlled"],
        channel="chrome",
    )
    page = await ctx.new_page()
    await page.goto("https://labs.google/fx", wait_until="domcontentloaded")
    await page.wait_for_timeout(8000)

    print("=== SHADOW DOM PIERCING TEST ===\n")

    # Method 1: get_by_placeholder (auto-pierces shadow DOM)
    try:
        el = page.get_by_placeholder("What do you want to create")
        count = await el.count()
        print(f"get_by_placeholder('What do you want to create'): {count} found")
        if count > 0:
            visible = await el.first.is_visible()
            print(f"  visible={visible}")
    except Exception as e:
        print(f"get_by_placeholder: ERROR - {e}")

    # Method 2: get_by_role textbox
    try:
        el = page.get_by_role("textbox")
        count = await el.count()
        print(f"get_by_role('textbox'): {count} found")
        for i in range(min(count, 5)):
            try:
                visible = await el.nth(i).is_visible()
                text = await el.nth(i).input_value() if visible else ""
                print(f"  [{i}] visible={visible} value='{text[:30]}'")
            except:
                print(f"  [{i}] (could not inspect)")
    except Exception as e:
        print(f"get_by_role: ERROR - {e}")

    # Method 3: JavaScript to find ALL shadow roots
    try:
        result = await page.evaluate("""() => {
            function findAll(root, results) {
                const els = root.querySelectorAll('*');
                for (const el of els) {
                    if (el.shadowRoot) {
                        const inner = el.shadowRoot.querySelectorAll('textarea, input, [contenteditable]');
                        for (const inp of inner) {
                            results.push({
                                tag: inp.tagName,
                                type: inp.type || '',
                                placeholder: inp.placeholder || '',
                                contentEditable: inp.contentEditable,
                                visible: inp.offsetParent !== null
                            });
                        }
                        findAll(el.shadowRoot, results);
                    }
                }
                return results;
            }
            return findAll(document, []);
        }""")
        print(f"\nJS shadow root scan: {len(result)} elements inside shadow DOMs")
        for i, r in enumerate(result):
            print(f"  [{i}] <{r['tag']}> type='{r.get('type','')}' placeholder='{r.get('placeholder','')}' editable={r.get('contentEditable','')} visible={r.get('visible','')}")
    except Exception as e:
        print(f"JS shadow scan: ERROR - {e}")

    # Method 4: Check for iframes
    frames = page.frames
    print(f"\nFrames on page: {len(frames)}")
    for i, f in enumerate(frames):
        print(f"  [{i}] {f.url[:80]}")

    print("\nBrowser stays open 20 seconds...")
    await page.wait_for_timeout(20000)
    await ctx.close()
    await pw.stop()

asyncio.run(debug())
