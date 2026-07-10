#!/bin/bash
# VPS Setup Script for Golden API Pipeline

echo "=========================================="
echo " Setting up VPS for Golden API Pipeline"
echo "=========================================="

# 1. Update and install Python tools
sudo apt update
sudo apt install -y python3-pip python3-venv curl

# 2. Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install requirements
pip install httpx python-dotenv playwright

# 4. Install Playwright browsers (needed for the token extractor)
playwright install chromium
playwright install-deps

echo ""
echo "=========================================="
echo " Setup Complete!"
echo " "
echo " Next Steps:"
echo " 1. Make sure Tailscale is running: sudo tailscale up --exit-node=<HOME_IP>"
echo " 2. Run the pipeline: python fast_api_pipeline.py"
echo "=========================================="
