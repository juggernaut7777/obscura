import os
import subprocess

public_url = 'https://buffoon-correct-credible.ngrok-free.dev'
router_path = '/home/USER/ai-ugc/generation_router.py'
key_path = 'C:/Users/USER/.ssh/google_compute_engine'

# Build the sed command carefully
sed_cmd = f\"sed -i 's|BRIDGE_URL = .*|BRIDGE_URL = \\\"{public_url}\\\"|' {router_path}\"

# Run the SSH command
ssh_cmd = [
    'ssh', '-i', key_path, 
    '-o', 'StrictHostKeyChecking=no',
    'USER@34.75.179.135', 
    sed_cmd
]

print(f'Syncing URL: {public_url}')
result = subprocess.run(ssh_cmd, capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
