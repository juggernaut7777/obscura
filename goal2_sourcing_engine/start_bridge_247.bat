@echo off
title 24/7 Flow Engine - Token Bridge + SSH Tunnel
color 0A
echo.
echo ============================================================
echo   24/7 FLOW ENGINE - AUTONOMOUS BRIDGE
echo   Token Bridge (port 9876) + SSH Reverse Tunnel to VPS
echo ============================================================
echo.
echo [INFO] This window must stay open for the VPS to generate images.
echo [INFO] It will auto-restart if anything crashes.
echo.

:: Kill any existing processes on port 9877
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9877 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

:: Start the Token Bridge server in the background
echo [%time%] Starting Token Bridge on port 9876...
start /B cmd /c "cd /d "%~dp0" && set PYTHONUNBUFFERED=1 && python all_in_one_bridge.py"
timeout /t 3 /nobreak >nul
echo [%time%] Token Bridge started.
echo.

:: Now run the SSH tunnel in a persistent loop
:tunnel_loop
echo [%time%] Connecting SSH Tunnel to Azure VPS (20.215.232.214)...
echo [%time%] Your VPS can now reach localhost:9877 through this tunnel.
echo.

ssh -N -i "%USERPROFILE%\.ssh\azure_obscura_key.pem" -o StrictHostKeyChecking=no -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -R 9877:127.0.0.1:9877 azureuser@20.215.232.214

echo.
echo [%time%] !! SSH Tunnel dropped. Reconnecting in 5 seconds...
timeout /t 5 /nobreak >nul
goto tunnel_loop
