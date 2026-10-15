"""
Resilient Sourcing Engine Deployment Tool
===========================================
Synchronises all upgraded modules to the 24/7 Azure VPS (20.215.232.214),
runs dependency installation inside the remote virtualenv,
and restarts both central services.
"""
import os
import sys
import subprocess

KEY_PATH = "C:/Users/USER/.ssh/azure_obscura_key.pem"
VPS_USER = "azureuser"
VPS_IP = "20.215.232.214"
REMOTE_DIR = "/home/azureuser/ai-ugc"

FILES_TO_SYNC = [
    "requirements.txt",
    "litellm_router.py",
    "agent_brain_vps.py",
    "agent_tools_vps.py",
    "agent_tools.py",
    "agent_memory.py",
    "discord_listener.py",
    "chinese_sourcing_agent.py",
    "sourcing_utils.py",
    "pricing_engine.py",
    "order_fulfillment.py",
    "supplier_mappings.json",
    "auto_stock_sync.py",
    "yupoo_scraper.py",
    "color_matcher.py",
    "product_onboarder.py",
    "image_classifier_v2.py",
    "storefront_image_selector.py",
    "seller_profiler.py",
    "background_enhancer.py",
    "pipeline_orchestrator.py",
    "storefront_curator_guard.py",
    "style_tagger.py",
    "outfit_warehouse.py",
    "auto_matcher.py",
    "local_generation_worker.py",
    "generation_router.py",
    "all_in_one_bridge.py",
    "composite_builder.py",
    "storefront_uploader.py",
    "reverse_search.py",
    "meta_ai_video_worker.py",
    "prompt_library.py",
    "utils.py",
    "start_engine.py",
    "data/yupoo_sellers.json",
]


def run_command(cmd_list, description):
    print(f"\n[DEPLOY] {description}...")
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        if res.stdout:
            print(res.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error during {description}:")
        print(e.stderr)
        return False

def sync_files():
    """Copy upgraded python files and requirements.txt to the remote directory."""
    success = True
    for f in FILES_TO_SYNC:
        if not os.path.exists(f):
            print(f"[WARNING] Local file {f} not found, skipping sync.")
            continue
            
        scp_cmd = [
            "scp", "-i", KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            f, f"{VPS_USER}@{VPS_IP}:{REMOTE_DIR}/{f}"
        ]
        if not run_command(scp_cmd, f"Syncing {f} to VPS"):
            success = False
            
    return success

def remote_execute():
    """Execute requirements installation, file cleanup, cron adjustment, and service restarts via remote SSH."""
    # Build list of remote operations
    remote_commands = [
        f"echo '📂 Directory listing remote ai-ugc:' && ls -la {REMOTE_DIR}",
        # (Yupoo scrapers are now active — no longer archived)
        # Activate virtualenv and upgrade remote packages
        f"echo '📦 Installing remote pip packages...' && {REMOTE_DIR}/venv/bin/pip install -r {REMOTE_DIR}/requirements.txt",
        # Restart central services with systemd reset-failed
        "echo '🔄 Resetting failed systemd state for ai-brain...' && sudo systemctl reset-failed ai-brain",
        "echo '🔄 Restarting ai-brain systemd service...' && sudo systemctl restart ai-brain",
        "echo '🔄 Restarting discord-listener systemd service...' && sudo systemctl restart discord-listener",
        "echo '✅ VPS successfully updated!'"
    ]
    
    ssh_cmd = [
        "ssh", "-i", KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        f"{VPS_USER}@{VPS_IP}",
        " && ".join(remote_commands)
    ]
    
    return run_command(ssh_cmd, "Executing remote package installations and service restarts")

def main():
    print("=" * 60)
    print("STARTING DEPLOYMENT SYSTEM FOR AGENTIC UPGRADES")
    print(f"   Target VPS: {VPS_USER}@{VPS_IP}")
    print("=" * 60)
    
    if not os.path.exists(KEY_PATH):
        print(f"[CRITICAL ERROR] SSH key not found at {KEY_PATH}")
        sys.exit(1)
        
    if not sync_files():
        print("[ERROR] Sync failed. Aborting VPS execution.")
        sys.exit(1)
        
    if not remote_execute():
        print("[ERROR] Remote execution failed.")
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("DEPLOYMENT AND SERVER UPGRADES COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
