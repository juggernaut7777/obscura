#!/bin/bash
# Login helper v3 — navigates to Flow AFTER login to capture session cookies
# Run: sudo -u user bash /home/user/ai-ugc/full_login.sh

# Ensure Xvfb is running
if ! pgrep -x Xvfb > /dev/null; then
    Xvfb :99 -screen 0 1280x900x24 &
    sleep 2
fi

# Ensure x11vnc is running
if ! pgrep -x x11vnc > /dev/null; then
    x11vnc -display :99 -nopw -forever -shared -rfbport 5900 &
    sleep 2
fi

export DISPLAY=:99
IP=$(curl -s ifconfig.me)

echo ""
echo "============================================"
echo "  OPEN IN YOUR BROWSER:"
echo "  http://${IP}:6080/vnc.html"
echo ""
echo "  You have 5 MINUTES to log in."
echo "============================================"
echo ""

cd /home/user/ai-ugc
source venv/bin/activate

python3 << 'PYEOF'
import asyncio
from playwright.async_api import async_playwright

async def login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Go directly to sign-in page
        print("Opening sign-in page...")
        await page.goto("https://labs.google/fx/api/auth/signin", wait_until="domcontentloaded", timeout=60000)
        
        print("Waiting for you to log in via noVNC...")
        print("After clicking 'Sign in with Google' and logging in,")
        print("the script will detect it automatically.")
        print("")
        
        # Wait for login to complete — check every 10 seconds
        logged_in = False
        for i in range(30):  # 5 minutes max
            await asyncio.sleep(10)
            elapsed = (i + 1) * 10
            remaining = 300 - elapsed
            
            url = page.url
            print(f"  {elapsed}s... URL: {url[:60]}")
            
            # If we got redirected away from signin page, login worked
            if "signin" not in url and "accounts.google" not in url:
                print("Login detected! Navigating to Flow tool...")
                logged_in = True
                break
        
        if not logged_in:
            # Navigate to flow tool anyway to try
            print("Timer done. Navigating to Flow tool to capture cookies...")
        
        # Go to the actual Flow tool to trigger session cookie creation
        await page.goto("https://labs.google/fx/tools/flow", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        # Check if we see the tool page or sign-in
        body = await page.text_content("body") or ""
        if "Sign in" in body[:500]:
            print("WARNING: Still not logged in. Cookies may not work.")
        else:
            print("Flow tool loaded successfully!")
        
        # Save ALL cookies
        state = await context.storage_state(path="/home/user/.flow_bridge_cookies.json")
        cookie_count = len(state.get("cookies", []))
        has_session = any("session" in c["name"].lower() for c in state.get("cookies", []))
        
        print(f"")
        print(f"Saved {cookie_count} cookies (session token: {'YES' if has_session else 'NO'})")
        
        # Also save to project dir
        import json
        with open("/home/user/ai-ugc/google_cookies.json", "w") as f:
            json.dump(state, f, indent=2)
        
        await browser.close()

asyncio.run(login())
PYEOF

echo ""
echo "Done! Now restart brain: sudo systemctl restart ai-brain"
