#!/bin/bash
# =============================================================
# 24/7 AUTONOMOUS AI BRAIN - VPS Runner
# =============================================================
# This script runs the AI agent in a persistent loop.
# If it crashes or finishes, it waits 30 seconds and restarts.
# Deploy on VPS: chmod +x start_autonomous.sh && ./start_autonomous.sh
# =============================================================

cd ~/ai-ugc
source venv/bin/activate

echo "============================================================"
echo "  🧠 AUTONOMOUS AI BRAIN - 24/7 MODE"
echo "  $(date)"
echo "============================================================"

# Ensure log directory exists
mkdir -p logs

LOOP_COUNT=0

echo "[*] Starting Discord Listener (24/7 Mode)..."
nohup python discord_listener.py > logs/discord_vps.log 2>&1 &

while true; do
    LOOP_COUNT=$((LOOP_COUNT + 1))
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🔄 Run #$LOOP_COUNT | $(date)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if the SSH tunnel (port 9877) is available
    if curl -s --max-time 3 http://localhost:9877/health > /dev/null 2>&1; then
        echo "✅ Bridge tunnel is CONNECTED. Using Google Flow (GEM_PIX_2)."
    else
        echo "⚠️  Bridge tunnel not available. Will use Pollinations fallback."
    fi
    
    # Run the brain for 2 hours, then loop
    python agent_brain_vps.py --run-hours 2 2>&1 | tee -a logs/brain_$(date +%Y%m%d).log
    
    EXIT_CODE=$?
    echo ""
    echo "[$(date)] Brain exited with code $EXIT_CODE"
    
    if [ $EXIT_CODE -ne 0 ]; then
        echo "⚠️  Brain crashed. Waiting 30 seconds before restart..."
        sleep 30
    else
        echo "✅ Brain completed run. Starting next cycle in 10 seconds..."
        sleep 10
    fi
done
