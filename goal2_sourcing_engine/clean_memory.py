import json

fpath = '/home/user/ai-ugc/brain_memory.json'
try:
    with open(fpath, 'r') as f:
        data = json.load(f)
    if 'models' in data:
        data['models'] = {}
    with open(fpath, 'w') as f:
        json.dump(data, f, indent=2)
    print("Memory cleaned successfully.")
except Exception as e:
    print(f"Error: {e}")
