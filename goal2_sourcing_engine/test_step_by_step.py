"""
Step-by-step Flow test — pauses after each action so you can see what's happening.
Press Enter in the terminal to move to the next step.
"""
import asyncio
import os
from playwright.async_api import async_playwright


async def run():
    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        user_data_dir=os.path.abspath("playwright_profile"),
        headless=False,
        viewport={"width": 900, "height": 600},
        args=["--disable-blink-features=AutomationControlled"],
        channel="chrome",
    )

    page = await ctx.new_page()

    # ========== STEP 1: Open Flow ==========
    print("\n=== STEP 1: Opening Flow homepage ===")
    await page.goto("https://labs.google/fx", wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)
    await page.screenshot(path="step1_homepage.png")
    print("Screenshot saved: step1_homepage.png")
    input("\n>>> Look at the browser. Press ENTER when you're on the Flow page with the prompt box visible...")

    # ========== STEP 2: Take screenshot of current state ==========
    print("\n=== STEP 2: Taking screenshot of current state ===")
    await page.screenshot(path="step2_current.png")
    print("Screenshot saved: step2_current.png")
    print(f"Page URL: {page.url}")
    print(f"Viewport: {page.viewport_size}")
    input("\n>>> Press ENTER to try clicking the prompt box...")

    # ========== STEP 3: Try clicking prompt box ==========
    print("\n=== STEP 3: Clicking where the prompt box should be ===")
    vp = page.viewport_size
    w, h = vp["width"], vp["height"]
    
    # Try clicking at the very bottom center
    click_x = w // 2
    click_y = h - 50
    print(f"Clicking at ({click_x}, {click_y}) — center bottom")
    await page.mouse.click(click_x, click_y)
    await page.wait_for_timeout(1000)
    await page.screenshot(path="step3_after_click.png")
    print("Screenshot saved: step3_after_click.png")
    input("\n>>> Did it click the prompt box? Or somewhere else? Press ENTER to try typing...")

    # ========== STEP 4: Type a short test ==========
    print("\n=== STEP 4: Typing 'hello test' ===")
    await page.keyboard.type("hello test", delay=50)
    await page.wait_for_timeout(1000)
    await page.screenshot(path="step4_after_type.png")
    print("Screenshot saved: step4_after_type.png")
    input("\n>>> Where did 'hello test' appear? In the prompt box or search bar? Press ENTER to continue...")

    # ========== STEP 5: Upload ONE image ==========
    print("\n=== STEP 5: Uploading one test image ===")
    test_img = "test_products/black_hoodie.jpg"
    if os.path.exists(test_img):
        try:
            file_input = page.locator("input[type='file']").first
            await file_input.set_input_files(os.path.abspath(test_img))
            print("Image uploaded via file input!")
        except Exception as e:
            print(f"Upload failed: {e}")
    else:
        print(f"Test image not found: {test_img}")
    
    await page.wait_for_timeout(5000)
    await page.screenshot(path="step5_after_upload.png")
    print("Screenshot saved: step5_after_upload.png")
    input("\n>>> What happened after the upload? Press ENTER to finish...")

    # ========== DONE ==========
    print("\n=== DONE! Browser stays open for 30 more seconds ===")
    await page.wait_for_timeout(30000)
    await ctx.close()
    await pw.stop()


asyncio.run(run())
