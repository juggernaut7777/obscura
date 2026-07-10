#!/bin/bash
echo "Installing dependencies..."
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
sudo apt install nodejs -y
sudo apt install -y libgbm-dev libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2

cd /home/USER/ai-ugc/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install playwright
playwright install chromium

echo "Starting background intelligence tasks..."
nohup python competitor_spy.py > spy.log 2>&1 &
nohup python factory_hunter.py > hunter.log 2>&1 &
nohup python agent_brain_local.py --scrape-only > scrape.log 2>&1 &

echo "Everything is running in the background! You can close SSH now."
