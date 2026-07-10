"""
Social Profile Setup — Automated Bio/Picture Editor
====================================================
Sets up brand new Instagram, TikTok, and Facebook accounts with
the OBSCURA GARMENTS brand identity automatically.
"""
import asyncio
import os
import json
from playwright.async_api import async_playwright

IG_COOKIE_FILE = os.path.expanduser("~/.ig_cookies.json")
TIKTOK_COOKIE_FILE = os.path.expanduser("~/.tiktok_cookies.json")
FB_COOKIE_FILE = os.path.expanduser("~/.fb_cookies.json")

# Brand identity
BRAND = {
    "name": "OBSCURA",
    "full_name": "OBSCURA GARMENTS",
    "bio_ig": "Curated fashion for the aesthetically inclined ✦\nNew drops weekly\n⬇️ Shop the collection",
    "bio_tiktok": "Curated fashion ✦ New drops weekly\nShop link below ⬇️",
    "bio_fb": "Premium aesthetically curated fashion. Every piece is designed with intention.",
    "website": "",  # Will be filled once Vercel is deployed
    "category": "Clothing (Brand)",
}


class ProfileSetup:
    def __init__(self, headless=False):
        self.headless = headless

    async def _load_context(self, pw, cookie_file):
        browser = await pw.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        if os.path.exists(cookie_file):
            ctx = await browser.new_context(
                storage_state=cookie_file,
                viewport={"width": 1280, "height": 720}
            )
        else:
            ctx = await browser.new_context(viewport={"width": 1280, "height": 720})
        return browser, ctx

    async def setup_instagram(self, pw, profile_pic_path=None):
        """Edit Instagram profile: bio, name, and optionally profile picture."""
        print("\n[IG] Setting up Instagram profile...")
        browser, ctx = await self._load_context(pw, IG_COOKIE_FILE)
        page = await ctx.new_page()

        try:
            await page.goto("https://www.instagram.com/accounts/edit/", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            if "login" in page.url.lower():
                print("   ⚠️ Not logged into Instagram. Run login_socials.bat first.")
                return False

            # Update Name
            name_field = page.locator('input[name="fullName"]').or_(page.locator('input[name="name"]'))
            if await name_field.count() > 0:
                await name_field.clear()
                await name_field.fill(BRAND["full_name"])
                print("   ✅ Name set to: {}".format(BRAND["full_name"]))

            # Update Bio
            bio_field = page.locator('textarea[name="biography"]').or_(page.locator('textarea').first)
            if await bio_field.count() > 0:
                await bio_field.clear()
                await bio_field.fill(BRAND["bio_ig"])
                print("   ✅ Bio updated")

            # Update Website (if we have one)
            if BRAND["website"]:
                website_field = page.locator('input[name="website"]').or_(page.locator('input[name="external_url"]'))
                if await website_field.count() > 0:
                    await website_field.clear()
                    await website_field.fill(BRAND["website"])
                    print("   ✅ Website set to: {}".format(BRAND["website"]))

            # Upload profile picture
            if profile_pic_path and os.path.exists(profile_pic_path):
                # Click the profile picture change button
                change_pic = page.locator('text="Change profile photo"').or_(
                    page.locator('[aria-label*="profile photo"]')
                )
                if await change_pic.count() > 0:
                    await change_pic.click()
                    await asyncio.sleep(2)
                    upload_btn = page.locator('text="Upload Photo"')
                    if await upload_btn.count() > 0:
                        async with page.expect_file_chooser() as fc_info:
                            await upload_btn.click()
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(profile_pic_path)
                        await asyncio.sleep(3)
                        print("   ✅ Profile picture uploaded")

            # Submit
            submit_btn = page.locator('button[type="submit"]').or_(page.locator('text="Submit"'))
            if await submit_btn.count() > 0:
                await submit_btn.click()
                await asyncio.sleep(3)
                print("   ✅ Instagram profile saved!")
            
            # Save updated cookies
            state = await ctx.storage_state()
            with open(IG_COOKIE_FILE, "w") as f:
                json.dump(state, f)

            return True

        except Exception as e:
            print("   ❌ Instagram setup error: {}".format(e))
            return False
        finally:
            await browser.close()

    async def setup_tiktok(self, pw, profile_pic_path=None):
        """Edit TikTok profile: bio and name."""
        print("\n[🎵] Setting up TikTok profile...")
        browser, ctx = await self._load_context(pw, TIKTOK_COOKIE_FILE)
        page = await ctx.new_page()

        try:
            await page.goto("https://www.tiktok.com/setting", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            if "login" in page.url.lower():
                print("   ⚠️ Not logged into TikTok. Run login_socials.bat first.")
                return False

            # Navigate to edit profile
            edit_btn = page.locator('text="Edit profile"').or_(page.locator('[data-e2e="edit-profile"]'))
            if await edit_btn.count() > 0:
                await edit_btn.click()
                await asyncio.sleep(2)

            # Update Name
            name_field = page.locator('input[placeholder*="Name"]').or_(page.locator('input[name="nickname"]'))
            if await name_field.count() > 0:
                await name_field.clear()
                await name_field.fill(BRAND["full_name"])
                print("   ✅ Name set to: {}".format(BRAND["full_name"]))

            # Update Bio
            bio_field = page.locator('textarea[placeholder*="Bio"]').or_(page.locator('textarea').first)
            if await bio_field.count() > 0:
                await bio_field.clear()
                await bio_field.fill(BRAND["bio_tiktok"])
                print("   ✅ Bio updated")

            # Save
            save_btn = page.locator('button:has-text("Save")')
            if await save_btn.count() > 0:
                await save_btn.click()
                await asyncio.sleep(3)
                print("   ✅ TikTok profile saved!")

            # Save cookies
            state = await ctx.storage_state()
            with open(TIKTOK_COOKIE_FILE, "w") as f:
                json.dump(state, f)

            return True

        except Exception as e:
            print("   ❌ TikTok setup error: {}".format(e))
            return False
        finally:
            await browser.close()

    async def setup_facebook(self, pw):
        """Edit Facebook page info."""
        print("\n[📘] Setting up Facebook profile...")
        browser, ctx = await self._load_context(pw, FB_COOKIE_FILE)
        page = await ctx.new_page()

        try:
            await page.goto("https://www.facebook.com/settings", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            if "login" in page.url.lower():
                print("   ⚠️ Not logged into Facebook. Run login_socials.bat first.")
                return False

            print("   ✅ Facebook logged in. Manual page setup recommended for best results.")
            print("   💡 Tip: Create a Facebook Page named '{}' and set the bio to:".format(BRAND["full_name"]))
            print("      '{}'".format(BRAND["bio_fb"]))

            # Save cookies
            state = await ctx.storage_state()
            with open(FB_COOKIE_FILE, "w") as f:
                json.dump(state, f)

            return True

        except Exception as e:
            print("   ❌ Facebook setup error: {}".format(e))
            return False
        finally:
            await browser.close()

    async def run_all(self, profile_pic_path=None):
        """Set up all social profiles."""
        async with async_playwright() as pw:
            await self.setup_instagram(pw, profile_pic_path)
            await self.setup_tiktok(pw, profile_pic_path)
            await self.setup_facebook(pw)
            print("\n[✅] All social profiles configured for OBSCURA GARMENTS!")


if __name__ == "__main__":
    import sys
    pic = sys.argv[1] if len(sys.argv) > 1 else None
    setup = ProfileSetup(headless=False)
    asyncio.run(setup.run_all(profile_pic_path=pic))
