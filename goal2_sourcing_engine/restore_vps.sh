#!/bin/bash
# ====================================================
# OBSCURA VPS Restore & Setup Script (Debian 12)
# ====================================================
set -e

echo "=========================================="
echo "          RESTORING VPS BACKUP"
echo "=========================================="

# 1. Create Swap File (Crucial for 1GB RAM VM)
if [ ! -f /swapfile ]; then
    echo "[1] Creating 2GB swapfile..."
    sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "    ✅ Swapfile created & enabled!"
else
    echo "[1] Swapfile already exists, skipping."
fi

# 2. Extract Backup (If present)
if [ -f /home/USER/vps_backup.tar.gz ]; then
    echo "[2] Extracting backup..."
    mkdir -p /home/USER/ai-ugc
    tar -xzf /home/USER/vps_backup.tar.gz -C /home/USER/
    rm -f /home/USER/vps_backup.tar.gz
    echo "    ✅ Backup extracted successfully!"
else
    echo "[2] Backup tarball not found or already extracted, skipping."
fi

# 3. System Packages Installation
echo "[3] Updating apt and installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv xvfb x11vnc \
    libgbm-dev libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 curl

# 4. Node.js Installation (Required for Playwright)
if ! command -v node &> /dev/null; then
    echo "[4] Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo "    ✅ Node.js installed!"
else
    echo "[4] Node.js already installed."
fi

# 5. Virtual Environment & Python Requirements
echo "[5] Setting up Python virtual environment..."
cd /home/USER/ai-ugc
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install playwright
playwright install chromium
echo "    ✅ Python environment ready!"

# 6. Run service setup script
echo "[6] Running AI Brain service configuration..."
sudo bash setup_service_vps.sh

# 7. Setup Discord Listener Service
echo "[7] Configuring Discord listener bot service..."
sudo cp discord-listener.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable discord-listener
sudo systemctl restart discord-listener

echo "=========================================="
echo "          🎉 RESTORE COMPLETE! 🎉"
echo "=========================================="
echo "To monitor the brain:"
echo "    tail -f /home/USER/ai-ugc/logs/brain.log"
echo "To monitor the Discord bot:"
echo "    tail -f /home/USER/ai-ugc/logs/discord_vps.log"
echo "=========================================="
