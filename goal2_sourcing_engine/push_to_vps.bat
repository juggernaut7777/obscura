@echo off
echo ========================================================
echo        PUSHING LATEST BRAIN CODE TO VPS
echo ========================================================
echo.
echo Syncing new scripts (DeepSeek, Video Bridge, Factory Hunter, etc.) to the 24/7 VM...

set KEY_PATH=C:\Users\USER\.ssh\google_compute_engine
set VPS_USER=USER
set VPS_IP=34.75.179.135
set REMOTE_DIR=/home/USER/ai-ugc/

echo [1] Copying python files...
scp -i %KEY_PATH% -o StrictHostKeyChecking=no *.py %VPS_USER%@%VPS_IP%:%REMOTE_DIR%

echo [2] Copying bash, config, and service files...
scp -i %KEY_PATH% -o StrictHostKeyChecking=no *.sh *.bat *.json *.txt *.service %VPS_USER%@%VPS_IP%:%REMOTE_DIR%

echo [3] Copying Social Media & Browser Cookies...
scp -i %KEY_PATH% -o StrictHostKeyChecking=no %USERPROFILE%\.ig_cookies.json %VPS_USER%@%VPS_IP%:~/.ig_cookies.json
scp -i %KEY_PATH% -o StrictHostKeyChecking=no %USERPROFILE%\.tiktok_cookies.json %VPS_USER%@%VPS_IP%:~/.tiktok_cookies.json
scp -i %KEY_PATH% -o StrictHostKeyChecking=no %USERPROFILE%\.fb_cookies.json %VPS_USER%@%VPS_IP%:~/.fb_cookies.json
scp -i %KEY_PATH% -o StrictHostKeyChecking=no %USERPROFILE%\.kling_cookies.json %VPS_USER%@%VPS_IP%:~/.kling_cookies.json

echo.
echo [✅] Push complete!
echo.
echo The 24/7 VPS Brain now has all the latest code.
echo Please run 'start_bridge_247.bat' on your local PC to open the image generation tunnel,
echo and then start the brain on the VPS!
echo.
pause
