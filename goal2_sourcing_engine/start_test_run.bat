@echo off
echo ============================================
echo   LOCAL FASHION ENGINE - TEST RUN
echo ============================================
echo.
cd /d "%~dp0"
python local_generation_worker.py
echo.
echo Press any key to close...
pause >nul
