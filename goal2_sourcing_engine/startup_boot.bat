@echo off
TITLE FASHION AUTOMATION -- STARTUP BOOT
cd /d "c:\Users\USER\ai ugc and sales\goal2_sourcing_engine"

echo ==================================================
echo [BOOT] Starting Fashion Automation Suite...
echo ==================================================

echo [*] Starting Discord Listener (24/7 Mode)...
start /B python discord_listener.py > discord_boot.log 2>&1

echo [*] Starting AI Generation Worker (Loop Mode)...
start /B python manual_worker.py --loop > worker_boot.log 2>&1

echo ==================================================
echo [OK] Everything is running in the background.
echo [!] To stop everything, close this window or run:
echo     taskkill /F /IM python.exe
echo ==================================================
pause
