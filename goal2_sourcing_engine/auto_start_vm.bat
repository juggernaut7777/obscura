@echo off
title Autonomous Fashion Engine 24/7
echo ====================================================
echo   STARTING 24/7 AUTONOMOUS FASHION BRAIN
echo ====================================================
echo.
echo Waiting 15 seconds for network and system services to initialize...
timeout /t 15 /nobreak

:: Change to the project directory
cd /d "c:\Users\USER\ai ugc and sales\goal2_sourcing_engine"

:: Run the engine in an infinite loop so if it crashes, it automatically restarts
:loop
echo [%date% %time%] Starting agent_brain_local.py...
python agent_brain_local.py
echo.
echo [!] Engine stopped or crashed. Restarting in 10 seconds...
timeout /t 10 /nobreak
goto loop
