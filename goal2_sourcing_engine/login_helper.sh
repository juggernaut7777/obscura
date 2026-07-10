#!/bin/bash
# ============================================
# Login Helper — Opens browser with VNC for Google login
# ============================================
# Run this on the VM, then connect with a VNC viewer
# to see the browser and log in to Google.
#
# Usage: sudo -u user bash login_helper.sh
# ============================================

set -e

echo "============================================"
echo "  Google Login Helper (VNC)"
echo "============================================"
echo ""

# Start virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!
sleep 2

# Start VNC server on port 5900 (no password for simplicity)
x11vnc -display :99 -nopw -forever -shared -rfbport 5900 &
VNC_PID=$!
sleep 2

echo "✅ VNC server running on port 5900"
echo ""
echo "Connect with a VNC viewer to: $(curl -s ifconfig.me):5900"
echo ""
echo "Starting Chromium..."

# Launch Chromium (non-headless) pointed at labs.google
cd /home/user/ai-ugc
source venv/bin/activate

python3 -c "
import asyncio
from playwright.async_api import async_playwright

async def login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox', '--start-maximized']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        print('Opening labs.google...')
        await page.goto('https://labs.google', wait_until='domcontentloaded', timeout=60000)
        
        print('')
        print('=== BROWSER IS OPEN ===')
        print('Connect via VNC and log into Google.')
        print('After logging in and seeing the labs.google dashboard,')
        print('press ENTER here to save cookies.')
        print('')
        
        input('>>> Press ENTER after logging in... ')
        
        # Save cookies
        await context.storage_state(path='/home/user/.flow_bridge_cookies.json')
        print('✅ Cookies saved!')
        
        await browser.close()

asyncio.run(login())
"

# Cleanup
kill $VNC_PID 2>/dev/null
kill $XVFB_PID 2>/dev/null

echo ""
echo "✅ Done! Restart the brain with: sudo systemctl restart ai-brain"
