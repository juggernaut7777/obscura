import os
import subprocess

# Azure VPS Configuration (Active Production Server)
VPS_IP = "20.215.232.214"
VPS_USER = "azureuser"
KEY_PATH = "C:/Users/USER/.ssh/azure_obscura_key.pem"
ROUTER_PATH = "/home/azureuser/ai-ugc/generation_router.py"
PUBLIC_URL = "http://127.0.0.1:9877"

sed_cmd = f"sed -i 's|BRIDGE_URL = .*|BRIDGE_URL = \"{PUBLIC_URL}\"|' {ROUTER_PATH}"

ssh_cmd = [
    'ssh', '-i', KEY_PATH,
    '-o', 'ConnectTimeout=15',
    '-o', 'StrictHostKeyChecking=no',
    f'{VPS_USER}@{VPS_IP}',
    sed_cmd
]

print(f"Syncing router on Azure VPS ({VPS_IP})...")
result = subprocess.run(ssh_cmd, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("[stderr]:", result.stderr)
