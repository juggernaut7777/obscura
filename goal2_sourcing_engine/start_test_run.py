import time
import requests
import glob
import os
import random

BRIDGE_URL = "http://localhost:9877/generate"

def run():
    print("========================================")
    print(" Starting 4-Shot Campaign Test via Bridge ")
    print("========================================")
    
    male_face = os.path.abspath("models/character_sheets/m1_face.png")
    male_body = os.path.abspath("models/character_sheets/m1_body.png")
    
    products = glob.glob("input_sourcing/*.png")
    if not products:
        print("No products found in input_sourcing/")
        return
    
    product = products[0]
    print(f"[*] Using Product: {os.path.basename(product)}")
    product_abs = os.path.abspath(product)
    
    prompts = [
        "Photo 1 and 2 are the model (face and body). Use image 3 as the product. Put the clothing from the product image on the model. Generate a hyperrealistic full body photo of the model posing in a photo shoot at a professional studio.",
        "Photo 1 and 2 are the model (face and body). Use image 3 as the product. Put the clothing from the product image on the model. Generate a hyperrealistic photo of the model posing with another friend in a photo shoot at a studio.",
        "Ignore image 1 and 2. Use image 3 as the product. Generate a professional flat lay photograph of this EXACT garment. The garment is neatly laid out on a clean surface like an outfit check. No human in the photo.",
        "Ignore image 1 and 2. Use image 3 as the product. Professional product-only photograph of this EXACT garment. The garment hangs hollow on an invisible mannequin against a clean studio wall. No human in the photo."
    ]
    
    for i, p in enumerate(prompts):
        print(f"\n[>>] Requesting Shot {i+1}/4...")
        payload = {
            "prompt": p,
            "ref_image_paths": [male_face, male_body, product_abs]
        }
        
        try:
            resp = requests.post(BRIDGE_URL, json=payload, timeout=240)
            if resp.status_code == 200:
                print(f"  [OK] Successfully generated and saved to bridge output directory!")
            else:
                print(f"  [FAIL] Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            
        if i < len(prompts) - 1:
            print("  [WAIT] Delaying 10s before next shot...")
            time.sleep(10)

if __name__ == '__main__':
    run()
