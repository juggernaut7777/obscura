import requests
import json
url = 'https://buffoon-correct-credible.ngrok-free.dev/generate'
payload = {'prompt': 'MASTER PRODUCTION COLLECTION TEST', 'market': 'london_uk'}
print(f'>>> TRIGGERING SILENTLY...')
try:
    # Using json= automatically handles the headers and encoding
    r = requests.post(url, json=payload, timeout=120)
    print(f'    Status: {r.status_code}')
    print(f'    Body: {r.text}')
except Exception as e:
    print(f'    Error: {str(e)}')
