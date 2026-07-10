@echo off
echo ============================================
echo  FLOW TOKEN BRIDGE - STARTUP
echo ============================================
echo.

REM Find which Chrome profile is logged into Flow
REM We will let the user just pick the right one.

REM Kill any existing Chrome debug instances on 9222
netstat -ano | findstr "9222" > nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Chrome debug port 9222 already active!
    echo      Connecting Python bridge...
    goto :run_bridge
)

echo Chrome is not running with debug port.
echo.
echo INSTRUCTIONS:
echo   1. Close this window
echo   2. Find your Chrome shortcut (on desktop or taskbar)
echo   3. Right-click it -> Properties
echo   4. In "Target" field, add at the end:  --remote-debugging-port=9222
echo   5. Click OK, then open Chrome normally - it will have the debug port
echo   6. Navigate to: labs.google/fx/tools/flow and log in
echo   7. Then run this batch file again.
echo.
echo OR - easier - just press a key and we will open Chrome with debug port
echo using your DEFAULT profile. You can then switch to the right Google account.
echo.
pause

REM Launch Chrome with remote debugging on the user's existing Default profile
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
    --remote-debugging-port=9222 ^
    --profile-directory=Default ^
    https://labs.google/fx/tools/flow/project/dbdc084a-72ca-48c4-b20e-bca88039ec84

echo.
echo Chrome opened! 
echo   - If you need to switch accounts: click profile icon top-right
echo   - Make sure you are on the FLOW PROJECT page (not the homepage)
echo   - You should see the image generation interface
echo.
echo Waiting 15 seconds for Chrome to load...
timeout /t 15 /nobreak > nul

:run_bridge
echo.
echo Connecting to Chrome and starting token bridge...
cd /d "%~dp0"
python token_bridge_cdp.py
pause
