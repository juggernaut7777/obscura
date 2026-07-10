"""
Sample Ad Generator — "Cold Outreach" Mode
============================================
Generates a professional fashion/product ad from a simple description.
Uses the live Nano Banana Pro bridge to create the sample.

Usage:
  python sample_generator.py "red leather handbag" "accessories"
  python sample_generator.py "white sneakers with gold trim" "shoes"
  python sample_generator.py "silk black evening dress" "clothing"

The generated sample is saved to the output/ folder, ready to DM to the brand.
"""
import os
import sys
import json
import time
import requests

BRIDGE_URL = "http://127.0.0.1:8888"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "samples")


def check_bridge():
    """Verify the local bridge is running and has tokens."""
    try:
        r = requests.get(f"{BRIDGE_URL}/status", timeout=5)
        data = r.json()
        if data.get("ready"):
            print("✅ Bridge is ONLINE and has fresh tokens.")
            return True
        else:
            print("⚠️  Bridge is online but tokens are stale. Refresh your Flow tab.")
            return False
    except Exception:
        print("❌ Bridge is OFFLINE. Run start_bridge_247.bat first.")
        return False


def generate_sample(product_description, niche="clothing", image_path=None):
    """Generate a professional sample ad for cold outreach."""
    
    niche_styles = {
        "clothing": "editorial fashion photography, professional studio lighting, clean white background, model wearing the garment confidently, luxury fashion magazine aesthetic",
        "shoes": "premium product photography, dramatic lighting, sleek surface reflection, close-up detail shot showing texture and craftsmanship, sneaker ad campaign style",
        "accessories": "luxury product photography, soft bokeh background, elegant jewelry display, golden hour lighting, high-end brand campaign aesthetic",
        "beauty": "clean beauty photography, soft diffused lighting, dewy skin texture, minimalist composition, premium skincare brand aesthetic",
        "bags": "luxury handbag photography, marble surface, soft shadows, editorial fashion style, premium brand campaign aesthetic",
        "wigs": "professional hair photography, studio lighting, natural hair movement, beauty campaign style, diverse model showcase",
    }
    
    style = niche_styles.get(niche, niche_styles["clothing"])
    
    prompt = f"A stunning professional advertisement photo featuring {product_description}. {style}. 4K resolution, photorealistic, commercial grade, ready for social media advertising."
    
    print(f"\n🎨 Generating sample ad for: \"{product_description}\"")
    print(f"   Niche: {niche}")
    if image_path:
        print(f"   🖼️  Using Source Image Reference: {os.path.basename(image_path)}")
    print(f"   Sending to Nano Banana Pro...")
    
    try:
        r = requests.post(
            f"{BRIDGE_URL}/generate",
            json={"prompt": prompt},
            timeout=180
        )
        data = r.json()
        
        if data.get("images"):
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            saved_files = []
            for img_path in data["images"]:
                # Copy or note the path
                fname = os.path.basename(img_path)
                sample_name = f"sample_{niche}_{int(time.time())}_{fname}"
                dest = os.path.join(OUTPUT_DIR, sample_name)
                
                # If the image is a VPS path, it's already uploaded
                # If local, move to samples folder
                if os.path.exists(img_path):
                    import shutil
                    shutil.copy2(img_path, dest)
                    saved_files.append(dest)
                else:
                    saved_files.append(img_path)
            
            print(f"\n✅ SAMPLE GENERATED SUCCESSFULLY!")
            print(f"   📁 Saved to: {OUTPUT_DIR}")
            for f in saved_files:
                print(f"   📸 {f}")
            print(f"\n   💡 DM this to the brand with your pitch!")
            return saved_files
        else:
            print(f"❌ Generation failed: {data}")
            return []
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (180s). Check your Flow tab is open.")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python sample_generator.py "product description" [niche]')
        print("")
        print("Niches: clothing, shoes, accessories, beauty, bags, wigs")
        print("")
        print("Examples:")
        print('  python sample_generator.py "red leather handbag" "bags"')
        print('  python sample_generator.py "white sneakers with gold trim" "shoes"')
        print('  python sample_generator.py "silk black evening dress" "clothing"')
        sys.exit(0)
    
    product = sys.argv[1]
    niche = sys.argv[2] if len(sys.argv) > 2 else "clothing"
    
    if not check_bridge():
        print("\n⚠️  Start the bridge first, then try again.")
        sys.exit(1)
    
    generate_sample(product, niche)
