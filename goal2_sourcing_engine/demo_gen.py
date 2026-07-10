import requests
import time

BRIDGE_URL = "http://127.0.0.1:9877"

def run_demo():
    print("Requesting new high-end 2K photo from the bridge...")
    prompt = "Hyperrealistic high fashion editorial photo of a trendy washed black distressed denim jacket on a premium concrete surface. Cinematic studio lighting. Shot on 100mm macro lens, ultra premium aesthetic, 8K detail."
    
    try:
        resp = requests.post(f"{BRIDGE_URL}/generate", json={"prompt": prompt}, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            print("SUCCESS! Generated images:")
            for img in data.get("images", []):
                print(img)
        else:
            print(f"FAILED: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_demo()
