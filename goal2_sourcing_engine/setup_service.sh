#!/bin/bash
# ============================================
# AI Brain — 24/7 Setup Script for Google Cloud VM
# ============================================
# Run this script ONCE on the VM to set up:
#   1. Systemd service for auto-restart
#   2. Log rotation
#   3. Memory cleanup cron job
#
# Usage: sudo bash setup_service.sh
# ============================================

set -e

# Config
BRAIN_DIR="/home/user/ai-ugc"
BRAIN_USER="user"
VENV_PATH="$BRAIN_DIR/venv"
SERVICE_NAME="ai-brain"
LOG_DIR="$BRAIN_DIR/logs"

# Validate inputs to prevent path traversal and command injection
if [[ ! "$BRAIN_DIR" =~ ^/[a-zA-Z0-9_/-]+$ ]] || [[ "$BRAIN_DIR" == *..* ]]; then
    echo "Error: Invalid BRAIN_DIR path" >&2
    exit 1
fi

if [[ ! "$BRAIN_USER" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    echo "Error: Invalid BRAIN_USER" >&2
    exit 1
fi


echo "🧠 Setting up AI Brain 24/7 service..."

# Create log directory
mkdir -p "$LOG_DIR"
chown "$BRAIN_USER:$BRAIN_USER" "$LOG_DIR"

# ── 1. Create the systemd service ──
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=AI Fashion Ad Brain — Autonomous Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${BRAIN_USER}
Group=${BRAIN_USER}
WorkingDirectory=${BRAIN_DIR}
Environment="PATH=${BRAIN_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HOME=/home/${BRAIN_USER}"
Environment="DISPLAY=:99"
ExecStartPre=/bin/bash -c 'source ${BRAIN_DIR}/venv/bin/activate'
ExecStart=${BRAIN_DIR}/venv/bin/python3 ${BRAIN_DIR}/agent_brain.py --run-hours 6
Restart=always
RestartSec=60
StartLimitInterval=3600
StartLimitBurst=20

# Logging
StandardOutput=append:${BRAIN_DIR}/logs/brain.log
StandardError=append:${BRAIN_DIR}/logs/brain_error.log

# Memory limits (prevent runaway)
MemoryMax=1.5G
MemoryHigh=1G

# Auto-restart timeout
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd service created"

# ── 2. Create a wrapper script that resets daily counters ──
cat > "$BRAIN_DIR/run_brain.sh" << RUNEOF
#!/bin/bash
# Wrapper script — called by systemd
cd ${BRAIN_DIR}
source venv/bin/activate

# Load .env
set -a
source .env 2>/dev/null || true
set +a

echo ""
echo "============================================================"
echo "  🧠 AI BRAIN SESSION START: \$(date)"
echo "============================================================"

# Run the brain for 6 hours, then systemd restarts it
python3 agent_brain.py --run-hours 6

echo ""
echo "============================================================"
echo "  🛑 SESSION END: \$(date) — Systemd will restart in 60s"
echo "============================================================"
RUNEOF
chmod +x "$BRAIN_DIR/run_brain.sh"
chown "$BRAIN_USER:$BRAIN_USER" "$BRAIN_DIR/run_brain.sh"

# Update service to use wrapper
sed -i "s|ExecStart=.*|ExecStart=/bin/bash ${BRAIN_DIR}/run_brain.sh|" /etc/systemd/system/${SERVICE_NAME}.service

echo "✅ Wrapper script created"

# ── 3. Set up log rotation ──
cat > /etc/logrotate.d/ai-brain << EOF
${BRAIN_DIR}/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    maxsize 10M
}
EOF

echo "✅ Log rotation configured (keep 7 days)"

# ── 4. Create memory cleanup cron (runs daily at 3am) ──
cat > "$BRAIN_DIR/clean_memory.py" << 'PYEOF'
#!/usr/bin/env python3
"""Clean duplicate learnings from brain_memory.json"""
import json, os

mem_path = os.path.join(os.path.dirname(__file__), "brain_memory.json")
if not os.path.exists(mem_path):
    print("No memory file found")
    exit(0)

with open(mem_path, "r") as f:
    data = json.load(f)

# Deduplicate learnings
seen = set()
unique = []
for l in data.get("learnings", []):
    key = l["text"][:100]  # First 100 chars as dedup key
    if key not in seen:
        seen.add(key)
        unique.append(l)

removed = len(data.get("learnings", [])) - len(unique)
data["learnings"] = unique

# Reset daily counters
data["actions_today"] = 0

with open(mem_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"Cleaned memory: removed {removed} duplicate learnings, {len(unique)} remaining")
PYEOF
chmod +x "$BRAIN_DIR/clean_memory.py"
chown "$BRAIN_USER:$BRAIN_USER" "$BRAIN_DIR/clean_memory.py"

# Add cron job for memory cleanup (3am daily)
(crontab -u "$BRAIN_USER" -l 2>/dev/null | grep -v clean_memory; \
 echo "0 3 * * * cd ${BRAIN_DIR} && ${BRAIN_DIR}/venv/bin/python3 clean_memory.py >> logs/cleanup.log 2>&1") \
 | crontab -u "$BRAIN_USER" -

echo "✅ Daily memory cleanup cron set (3am UTC)"

# ── 5. Set up Xvfb for headless browser ──
apt-get install -y xvfb > /dev/null 2>&1 || true
cat > /etc/systemd/system/xvfb.service << 'XEOF'
[Unit]
Description=Virtual Framebuffer for Playwright
Before=ai-brain.service

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
XEOF

echo "✅ Xvfb virtual display configured"

# ── 6. Enable and start everything ──
systemctl daemon-reload
systemctl enable xvfb.service
systemctl start xvfb.service
systemctl enable ${SERVICE_NAME}.service

echo ""
echo "============================================================"
echo "  ✅ SETUP COMPLETE"
echo "============================================================"
echo ""
echo "  Commands:"
echo "    Start:   sudo systemctl start ai-brain"
echo "    Stop:    sudo systemctl stop ai-brain"
echo "    Status:  sudo systemctl status ai-brain"
echo "    Logs:    tail -f ${BRAIN_DIR}/logs/brain.log"
echo "    Errors:  tail -f ${BRAIN_DIR}/logs/brain_error.log"
echo ""
echo "  The brain will:"
echo "    - Run 6-hour sessions, auto-restart between sessions"
echo "    - Survive VM reboots"
echo "    - Clean duplicate learnings daily at 3am"
echo "    - Rotate logs (keep 7 days)"
echo ""
echo "  ⚠️  Before starting, make sure FlowBridge cookies are valid:"
echo "    sudo -u ${BRAIN_USER} bash -c 'cd ${BRAIN_DIR} && source venv/bin/activate && python3 flow_bridge.py login'"
echo ""
