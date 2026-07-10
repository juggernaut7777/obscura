@echo off
TITLE FASHION AUTOMATION -- 24/7 AUTO RESTART WORKER
cd /d "%~dp0"

:loop
echo ==================================================
echo [%date% %time%] Starting AI Generation Worker...
echo ==================================================
python local_generation_worker.py --loop
echo.
echo ==================================================
echo [%date% %time%] Worker exited with code %errorlevel%. 
echo Restarting in 10 seconds... press Ctrl+C to abort.
echo ==================================================
timeout /t 10
goto loop
