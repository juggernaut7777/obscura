"""
BROWSER SESSION HELPER — Unified Playwright Browser Context Manager
===================================================================
A unified utility that manages browser context creation using a fallback chain:
1. Connect via CDP to http://localhost:9222 (allows using active logged-in Chrome tabs)
2. Launch local Chrome pointing to %LOCALAPPDATA%/Google/Chrome/User Data
3. Launch local headless context using the fallback playwright_profile directory
"""

import os
import socket
import asyncio
from pathlib import Path
from typing import Tuple, Optional, Any, Dict
from patchright.async_api import Playwright, BrowserContext, Browser

# Paths
LOCAL_APPDATA = os.getenv("LOCALAPPDATA", "")
DEFAULT_CHROME_USER_DATA = Path(LOCAL_APPDATA) / "Google" / "Chrome" / "User Data" if LOCAL_APPDATA else None
FALLBACK_PROFILE_DIR = Path(__file__).parent / "playwright_profile"

def is_cdp_port_active(host: str = "127.0.0.1", port: int = 9222) -> bool:
    """Helper to check if a TCP port is open/listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect((host, port))
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

class BrowserSession:
    def __init__(self, context: BrowserContext, browser: Optional[Browser], is_cdp: bool, mode: str):
        self.context = context
        self.browser = browser  # None if launch_persistent_context was used
        self.is_cdp = is_cdp
        self.mode = mode

    async def close(self):
        """Safely close browser context, avoiding closing user's personal browser in CDP mode."""
        if self.is_cdp:
            print(f"[*] CDP session ({self.mode}): Keeping active user browser open. Closing pages only.")
            for page in self.context.pages:
                try:
                    await page.close()
                except Exception:
                    pass
        else:
            print(f"[*] Closing local browser context ({self.mode})...")
            try:
                await self.context.close()
            except Exception:
                pass
            if self.browser:
                try:
                    await self.browser.close()
                except Exception:
                    pass

async def get_browser_context(
    playwright: Playwright,
    headless: bool = True,
    profile_dir: Optional[str] = None
) -> BrowserSession:
    """
    Acquires a unified browser context.
    Attempts: CDP -> Personal Chrome Profile -> Custom Profile Dir -> Fallback Playwright Profile.
    """
    # 1. Try CDP Remote Debugging (Port 9222)
    if is_cdp_port_active("127.0.0.1", 9222):
        try:
            print("[*] CDP: Detected active remote debugging port 9222. Connecting...")
            browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
            if browser.contexts:
                context = browser.contexts[0]
                print("[+] CDP: Connected to existing browser context.")
                return BrowserSession(context, browser, is_cdp=True, mode="CDP")
            else:
                context = await browser.new_context()
                print("[+] CDP: Connected and created new context.")
                return BrowserSession(context, browser, is_cdp=True, mode="CDP")
        except Exception as e:
            print(f"[-] CDP connection failed: {e}. Falling back...")

    # 2. Try launching with user's actual Chrome User Data (Bypassed due to Google Chrome's non-default data directory security restriction)
    # if DEFAULT_CHROME_USER_DATA and DEFAULT_CHROME_USER_DATA.exists():
    #     try:
    #         print(f"[*] Launching local Chrome with personal user profile: {DEFAULT_CHROME_USER_DATA}")
    #         # Windows Chrome usually locks the user data directory if Chrome is already open.
    #         context = await playwright.chromium.launch_persistent_context(
    #             user_data_dir=str(DEFAULT_CHROME_USER_DATA),
    #             channel="chrome",
    #             headless=headless,
    #             args=[
    #                 "--no-sandbox",
    #                 "--disable-dev-shm-usage",
    #                 "--disable-blink-features=AutomationControlled"
    #             ]
    #         )
    #         try:
    #             from playwright_stealth import Stealth
    #             await Stealth().apply_stealth_async(context)
    #             print("[*] Stealth shields active.")
    #         except Exception as e:
    #             print(f"[-] Stealth warning: {e}")
    #         print("[+] Personal Chrome profile launched successfully.")
    #         return BrowserSession(context, None, is_cdp=False, mode="PersonalChromeProfile")
    #     except Exception as e:
    #         print(f"[-] Personal Chrome profile launch failed (likely locked by active Chrome instance): {e}")

    # 3. Try launching with the specific profile_dir requested
    if profile_dir:
        user_data_path = Path(profile_dir)
        try:
            print(f"[*] Launching local Chrome with custom profile: {user_data_path}")
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_path),
                channel="chrome",
                headless=headless,
                viewport={"width": 1280, "height": 720},
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            try:
                from playwright_stealth import Stealth
                await Stealth().apply_stealth_async(context)
                print("[*] Stealth shields active.")
            except Exception as e:
                print(f"[-] Stealth warning: {e}")
            print("[+] Custom profile launched successfully.")
            return BrowserSession(context, None, is_cdp=False, mode="CustomProfile")
        except Exception as e:
            print(f"[-] Custom profile launch failed: {e}")

    # 4. Fall back to persistent default playwright profile
    fallback_path = FALLBACK_PROFILE_DIR
    fallback_path.mkdir(exist_ok=True)
    print(f"[*] Launching fallback Playwright profile at: {fallback_path}")
    
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=str(fallback_path),
        headless=headless,
        viewport={"width": 1280, "height": 720},
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled"
        ]
    )
    try:
        from playwright_stealth import Stealth
        await Stealth().apply_stealth_async(context)
        print("[*] Stealth shields active.")
    except Exception as e:
        print(f"[-] Stealth warning: {e}")
    print("[+] Fallback profile launched successfully.")
    return BrowserSession(context, None, is_cdp=False, mode="Fallback")
