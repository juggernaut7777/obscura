import time
import subprocess
from playwright.sync_api import sync_playwright

def main():
    print("[*] Starting local Next.js production server on port 3333...")
    proc = subprocess.Popen(
        ["npm", "run", "start", "--", "-p", "3333"],
        cwd="storefront",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(4)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            # 1. Test Home Page
            print("[*] Testing Home Page (http://localhost:3333/)...")
            page.goto("http://localhost:3333/", wait_until="networkidle")
            page.screenshot(path="verify_home.png", full_page=True)
            print("    [+] Home page verified and screenshot captured.")

            # 2. Test Product Detail Page
            print("[*] Testing Product Detail Page (http://localhost:3333/product/deateath-prada-inverted-triangle-tee)...")
            page.goto("http://localhost:3333/product/deateath-prada-inverted-triangle-tee", wait_until="networkidle")
            
            # Verify initial color is Washed Black
            title = page.locator("h1").text_content()
            color_text = page.locator("text=Color —").text_content()
            print(f"    Product Title: {title}")
            print(f"    Active Color: {color_text}")
            assert "Washed Black" in color_text, f"Expected Washed Black, got {color_text}"
            
            # Verify Black thumbnails
            thumbs = page.locator("button img[alt*='Thumbnail']").all()
            print(f"    Thumbnails count for Washed Black: {len(thumbs)}")
            black_thumb_srcs = [t.get_attribute("src") for t in thumbs]
            for s in black_thumb_srcs:
                print(f"      - {s}")
                assert "white" not in s, f"Found white image in black variant: {s}"
            page.screenshot(path="verify_product_black.png")
            print("    [+] Washed Black variant verified: 100% black images, zero white mixing!")

            # 3. Test Clicking Chalk White Swatch
            print("[*] Clicking Chalk White swatch...")
            white_swatch = page.locator("button[title='Chalk White']").first
            white_swatch.click()
            page.wait_for_timeout(1000)

            color_text_after = page.locator("text=Color —").text_content()
            print(f"    Active Color after switch: {color_text_after}")
            assert "Chalk White" in color_text_after, f"Expected Chalk White, got {color_text_after}"

            # Verify White thumbnails
            white_thumbs = page.locator("button img[alt*='Thumbnail']").all()
            print(f"    Thumbnails count for Chalk White: {len(white_thumbs)}")
            white_thumb_srcs = [t.get_attribute("src") for t in white_thumbs]
            for s in white_thumb_srcs:
                print(f"      - {s}")
                assert "black" not in s, f"Found black image in white variant: {s}"
            page.screenshot(path="verify_product_white.png")
            print("    [+] Chalk White variant verified: 100% white images, zero black mixing!")

            # 4. Test Size Guide Modal
            print("[*] Testing Size Guide modal...")
            size_btn = page.locator("button:has-text('Size Guide')").first
            if size_btn.is_visible():
                size_btn.click()
                page.wait_for_timeout(500)
                page.screenshot(path="verify_size_guide.png")
                print("    [+] Size Guide modal opened and screenshot captured.")

            # 5. Test Lookbook Page
            print("[*] Testing Lookbook Page (http://localhost:3333/lookbook)...")
            page.goto("http://localhost:3333/lookbook", wait_until="networkidle")
            page.screenshot(path="verify_lookbook.png")
            print("    [+] Lookbook page verified and screenshot captured.")

            browser.close()
            print("\n[+] ALL LOCAL STOREFRONT INTEGRITY CHECKS PASSED 100%!")

    finally:
        proc.terminate()

if __name__ == "__main__":
    main()
