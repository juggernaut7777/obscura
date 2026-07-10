import os
import sys
from gradio_client import Client, handle_file

# Force UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("📸 RUNNING OOTDIFFUSION QUALITY TEST...")

try:
    client = Client("levihsu/OOTDiffusion")
    
    # Paths to our test assets
    person_path = os.path.abspath("models/character_sheets/f1_body.png")
    garment_path = os.path.abspath("test_products/black_hoodie.jpg")
    
    print(f"   Person: {os.path.basename(person_path)}")
    print(f"   Garment: {os.path.basename(garment_path)}")
    print("   Sending to HuggingFace (HD Mode)...")

    # Call the /process_hd endpoint
    # Parameters: vton_img, garm_img, n_samples, n_steps, image_scale, seed
    result = client.predict(
        vton_img=handle_file(person_path),
        garm_img=handle_file(garment_path),
        n_samples=1,
        n_steps=20,
        image_scale=2.0,
        seed=-1,
        api_name="/process_hd"
    )

    # OOTDiffusion returns a Gallery (list of dicts)
    if result and len(result) > 0:
        img_info = result[0]
        temp_path = img_info['image']
        
        # Save it to our test folder
        output_path = os.path.abspath("output/ootd_quality_test.png")
        os.makedirs("output", exist_ok=True)
        
        import shutil
        shutil.copy(temp_path, output_path)
        
        print(f"\n✅ QUALITY TEST COMPLETE!")
        print(f"   Result saved to: {output_path}")
    else:
        print("\n❌ API returned no images.")

except Exception as e:
    print(f"\n❌ Error during quality test: {e}")
