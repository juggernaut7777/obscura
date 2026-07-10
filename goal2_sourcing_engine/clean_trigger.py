import requests
url = 'https://buffoon-correct-credible.ngrok-free.dev/generate'
payload = {'prompt': 'Global Production Master Test', 'market': 'london_uk'}
print(f'>>> TRIGGERING VIA PURE PYTHON...')
try:
    r = requests.post(url, json=payload, timeout=120)
    print(f'    Status: {r.status_code}')
    print(f'    Body: {r.text}')
except Exception as e:
    print(f'    FAILED: {str(e)}')
