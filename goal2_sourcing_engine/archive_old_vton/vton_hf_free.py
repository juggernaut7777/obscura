import os
import time
from gradio_client import Client, handle_file

def run_free_vton(model_image_path, garment_image_path, description):
    print("==================================================")
    print(" FREE VTON GENERATOR (Hugging Face IDM-VTON)")
    print("==================================================")
    print(f"Model: {model_image_path}")
    print(f"Garment: {garment_image_path}")
    print("Connecting to free server...")
    
    try:
        client = Client("yisol/IDM-VTON")
        
        print("\nUploading images and generating... (This usually takes 30-60 seconds)")
        
        # Gradio ImageEditor expects a dict for the human image
        human_img_dict = {
            "background": handle_file(model_image_path),
            "layers": [],
            "composite": None
        }
        
        result = client.predict(
            dict=human_img_dict,
            garm_img=handle_file(garment_image_path),
            garment_des=description,
            is_checked=True,
            is_checked_crop=False,
            denoise_steps=30,
            seed=42,
            api_name="/tryon"
        )
        
        # Result is a tuple: (output_image_path, masked_image_path)
        output_img = result[0]
        
        os.makedirs("output/free_vton", exist_ok=True)
        final_path = f"output/free_vton/result_{int(time.time())}.webp"
        
        import shutil
        shutil.copy(output_img, final_path)
        
        print(f"\n✅ SUCCESS! Image saved to: {final_path}")
        return final_path
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return None

if __name__ == "__main__":
    run_free_vton(
        "models/character_sheets/f1_body.png",
        "test_products/red_hoodie.png",
        "Red cropped hoodie"
    )
