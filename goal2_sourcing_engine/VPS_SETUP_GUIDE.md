# VPS Deployment Guide — The Brain (Autonomous AI Agent)

## Overview

This VPS runs an **autonomous AI agent** that:
- Researches trending products (TikTok, USFans, Yupoo)
- Generates AI model character sheets
- Creates photorealistic ad images via Google AI Studio
- Writes viral captions (TikTok-safe coded language)
- Auto-posts to TikTok, Instagram, Facebook
- Finds underperforming brands and DMs them with demo ads
- Learns and adapts based on what works

**Cost: $0-4/month** (free tier APIs + free/cheap VPS)

---

## 1. Get a VPS

**Cheapest options:**
- **Google Cloud e2-micro** — FREE (always-free tier, already created)
- **Hetzner CX22** — €3.99/mo (2 vCPU, 4GB RAM, 40GB)
- **Contabo VPS S** — €5.99/mo (4 vCPU, 8GB RAM, 200GB)

Select **Ubuntu 22.04 LTS** as the OS.

## 2. Initial Server Setup

```bash
# SSH into your VPS
ssh root@YOUR_IP

# Update system
apt update && apt upgrade -y

# Install Python 3.11+
apt install python3 python3-pip python3-venv -y

# Install Node.js (required for Playwright)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install nodejs -y

# Install Chromium dependencies
apt install -y libgbm-dev libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
  libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2

# Install VNC for manual login step
apt install xvfb x11vnc -y
```

## 3. Deploy the Code

```bash
# Create project directory
mkdir -p ~/ai-ugc
cd ~/ai-ugc

# Upload your code (from your local machine):
# scp -r "c:\Users\USER\ai ugc and sales\goal2_sourcing_engine\*" root@YOUR_IP:~/ai-ugc/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install playwright
playwright install chromium

# Create required directories
mkdir -p output/{generated,scraped_ads/screenshots,variations}
mkdir -p models/character_sheets
mkdir -p products
mkdir -p logs
```

## 4. Configure Environment

```bash
# Copy your .env file (has API keys for Groq, xAI, NVIDIA)
# scp .env root@YOUR_IP:~/ai-ugc/.env

# Verify keys are present
cat .env | grep -c "API_KEY"
# Should show at least 3 (GROQ, XAI, NVIDIA)
```

## 5. First-Time Login (Manual — One Time Only)

The brain needs cookies for Google AI Studio and social media accounts.

```bash
# Start virtual display for headless VPS
Xvfb :1 -screen 0 1920x1080x24 &
export DISPLAY=:1

# Login to Google AI Studio (for FlowBridge)
python flow_bridge.py login
# → Log into Google in the browser → Press ENTER
# → Cookies saved to ~/.flow_bridge_cookies.json

# Login to TikTok (for auto-posting)
python social_autoposter.py login tiktok
# → Log into TikTok → Press ENTER

# Login to Instagram (for auto-posting + DMs)
python social_autoposter.py login instagram
# → Log into Instagram → Press ENTER
```

## 6. Test The Brain

```bash
cd ~/ai-ugc
source venv/bin/activate

# Step 1: Check brain status
python agent_brain.py --status

# Step 2: Dry run (plans actions but doesn't execute)
python agent_brain.py --dry-run --run-hours 0.01

# Step 3: Create model sheets (first real task)
python agent_brain.py --task "create model sheets" --run-hours 0.5

# Step 4: Full autonomous run (1 hour)
python agent_brain.py --run-hours 1
```

## 7. Run The Brain Continuously

### Option A: Run as a service (recommended)

```bash
# Create systemd service
cat > /etc/systemd/system/ai-brain.service << 'EOF'
[Unit]
Description=AI UGC Brain — Autonomous Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-ugc
Environment=PATH=/root/ai-ugc/venv/bin:/usr/bin
Environment=DISPLAY=:1
ExecStartPre=/usr/bin/Xvfb :1 -screen 0 1920x1080x24
ExecStart=/root/ai-ugc/venv/bin/python agent_brain.py --run-hours 23
Restart=always
RestartSec=3600
StandardOutput=append:/root/ai-ugc/logs/brain.log
StandardError=append:/root/ai-ugc/logs/brain_error.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable ai-brain
systemctl start ai-brain

# Check status
systemctl status ai-brain
```

### Option B: Daily cron (simpler)

```bash
crontab -e

# Run brain for 2 hours at 6 AM, 2 PM, and 10 PM daily:
0 6 * * * cd ~/ai-ugc && source venv/bin/activate && python agent_brain.py --run-hours 2 >> logs/brain.log 2>&1
0 14 * * * cd ~/ai-ugc && source venv/bin/activate && python agent_brain.py --run-hours 2 >> logs/brain.log 2>&1
0 22 * * * cd ~/ai-ugc && source venv/bin/activate && python agent_brain.py --run-hours 2 >> logs/brain.log 2>&1

# Keep the old daily_runner as fallback (once a day):
0 5 * * * cd ~/ai-ugc && source venv/bin/activate && python daily_runner.py >> logs/daily.log 2>&1
```

## 8. Monitor

```bash
# Check brain status
python agent_brain.py --status

# View brain log
tail -100 logs/brain.log

# View brain memory
python -c "import json; print(json.dumps(json.load(open('brain_memory.json')), indent=2))"

# Check today's output
ls -la output/$(date +%Y-%m-%d)/

# Count total generated content
find output/ -name "*.png" | wc -l
```

---

## File Structure

```
~/ai-ugc/
├── agent_brain.py            # 🧠 THE BRAIN — autonomous agent loop
├── agent_memory.py           # 💾 Persistent memory system
├── agent_tools.py            # 🔧 14 tools the brain can call
├── fashion_brain.py          # 👗 Fashion understanding module
├── flow_bridge.py            # 🌐 Browser automation (Google AI Studio)
├── prompt_library.py         # 📝 All ad prompts (clothing, shoes, wigs, beauty)
├── luxury_caption_generator.py # ✍️ Viral caption writer
├── daily_runner.py           # 🔄 Legacy pipeline (fallback)
├── agent_product_scraper.py  # 🕷️ USFans/CNFans scraper
├── tiktok_trend_scraper.py   # 📈 TikTok trend discovery
├── social_autoposter.py      # 📱 Auto-poster (TT/IG/FB)
├── kofa_bridge.py            # 🔗 KOFA platform integration
├── fashion_sourcing.py       # 🏭 Supplier sourcing
├── meta_ad_scraper.py        # 📊 Meta Ad Library scraper
├── carousel_builder.py       # 🖼️ Multi-image carousel builder
├── video_variation_funnel.py # 🎬 Video variation generator
├── vton_pipeline.py          # 👕 Virtual try-on pipeline
├── sourcing_engine.py        # 🔍 Product sourcing engine
├── .env                      # 🔑 API keys (Groq, xAI, NVIDIA)
├── requirements.txt          # 📦 Python dependencies
├── brain_memory.json         # 🧠 Brain's persistent state (auto-created)
├── models/
│   └── character_sheets/     # AI model face references (auto-generated)
├── products/                 # Scraped product data
├── output/
│   ├── generated/            # Raw AI generations
│   ├── YYYY-MM-DD/           # Daily organized output
│   └── variations/           # Video variations
└── logs/
    ├── brain.log             # Brain activity log
    └── daily.log             # Legacy pipeline log
```

---

## API Keys Required (.env)

```
GROQ_API_KEY=gsk_xxxxx           # Free at console.groq.com
XAI_API_KEY=xai-xxxxx           # $25 free credit at x.ai
NVIDIA_NIM_API_KEY=nvapi-xxxxx  # Free tier at build.nvidia.com
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Brain can't think | Check Groq API key, check internet |
| No model sheets generated | Run with `--task "create model sheets"` |
| FlowBridge fails | Re-run `python flow_bridge.py login` |
| Social posting fails | Re-login: `python social_autoposter.py login` |
| Out of Groq free quota | Wait 24h (resets daily) or use xAI fallback |
| Brain stuck in loop | Check `brain_memory.json` for last_error |
