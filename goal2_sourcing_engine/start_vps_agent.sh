#!/bin/bash

# Load Environment Variables (Ensure NVAPI_KEY is in here)
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

echo "=================================================="
echo "      AUTONOMOUS VPS AGENT (NVIDIA EDITION)      "
echo "=================================================="

# 1. Start the Claude-to-NVIDIA Proxy in the background
echo "🚀 Starting NVIDIA Proxy..."
python3 claude_nvidia_proxy.py &
PROXY_PID=$!

# Wait for proxy to initialize
sleep 3

# 2. Configure Claude Code to use our Local Proxy
export ANTHROPIC_BASE_URL="http://localhost:8083"
export ANTHROPIC_API_KEY="nv-agent-session" # Placeholder

# 3. Launch the Claude Agent
# We use --non-interactive if we want to run in a pure loop, 
# but for the VPS we usually run in a 'screen' or 'tmux' session.
echo "🧠 Launching Claude Agent..."
claude

# Cleanup proxy on exit
kill $PROXY_PID
echo "👋 Shutdown complete."
