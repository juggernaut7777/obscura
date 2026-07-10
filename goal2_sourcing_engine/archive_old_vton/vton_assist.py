"""
VTON Assist — Final Resilient Version
=======================================
1. Auto-uploads 3 images.
2. YOU paste the prompt and click generate.
3. DO NOT CLOSE BROWSER until you hit Enter in terminal.
"""
import os
import asyncio
from playwright.async_api import async_playwright

async def run_assist():
    print("\n" + "="*50)
    print("🚀 VTON ASSISTANT (FINAL RESILIENT MODE)")
    print("="*50)
    
    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        user_data_dir=os.path.abspath("playwright_profile"),
        headless=False,
        viewport={"width": 800, "height": 500},
        args=["--disable-blink-features=AutomationControlled"],
        channel="chrome",
    )
    
    page = await ctx.new_page()
    print("\n[1/4] Opening Flow...")
    await page.goto("https://labs.google/fx", wait_until="domcontentloaded")
    
    input("\n>>> STEP 1: Navigate to your project. Press ENTER when prompt box is visible...")
    
    # [2/4] Upload images
    print("\n[2/4] Uploading reference images...")
    images = [
        "models/character_sheets/f1_face.png",
        "models/character_sheets/f1_body.png",
        "test_products/black_hoodie.jpg"
    ]
    
    active_page = ctx.pages[-1]
    try:
        file_input = active_page.locator("input[type='file']").first
        await file_input.set_input_files([os.path.abspath(i) for i in images if os.path.exists(i)])
        print("✅ Images uploaded!")
    except Exception as e:
        print(f"⚠️ Upload check: {e}. If images didn't appear, please upload manually.")

    # [3/4] User turn
    print("\n" + "*"*50)
    print("👉 YOUR TURN:")
    print("1. Paste the prompt I gave you.")
    print("2. Click Generate.")
    print("3. WAIT for the image to appear.")
    print("4. DO NOT CLOSE THE BROWSER!")
    print("*"*50)
    
    input("\n>>> Press ENTER here only when you see the final image in the browser...")

    # [4/4] Save
    print("\n[4/4] Saving results...")
    os.makedirs("output/vton_final", exist_ok=True)
    
    # Try all pages to find the one with the result
    target = None
    for p in ctx.pages:
        try:
            if "labs.google" in p.url:
                target = p
                break
        except:
            continue
    
    if not target:
        print("❌ Could not find the Flow page. Did you close the browser?")
        return

    path = f"output/vton_final/vton_{int(asyncio.get_event_loop().time())}.png"
    try:
        await target.screenshot(path=path, full_page=True)
        print(f"✅ SUCCESS! Saved to: {path}")
    except Exception as e:
        print(f"❌ Save failed: {e}")
    
    print("\nClosing in 5 seconds...")
    await asyncio.sleep(5)
    await ctx.close()
    await pw.stop()

if __name__ == "__main__":
    asyncio.run(run_assist())
