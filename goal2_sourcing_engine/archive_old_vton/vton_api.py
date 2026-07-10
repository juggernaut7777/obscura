"""
VTON API — Clean, simple, no browser needed.
Uses fal.ai IDM-VTON model via API.

Setup:
  1. Go to https://fal.ai and sign up (free starter credits)
  2. Get your API key from the dashboard
  3. Set it: set FAL_KEY=your_key_here
  4. Run: python vton_api.py
"""
import os
import sys
import base64
import asyncio
import fal_client


def image_to_data_uri(path: str) -> str:
    """Convert a local image file to a data URI for the API."""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(path)[1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext.lstrip("."), "image/png")
    return f"data:{mime};base64,{data}"


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(f"   ... {log['message']}")


def run_vton(model_image: str, garment_image: str, description: str, output_path: str = None):
    """
    Run virtual try-on.
    
    Args:
        model_image: Path to the model/person image (body shot)
        garment_image: Path to the garment/product image (flat lay)
        description: Short description of the garment (e.g. "Red cropped hoodie")
        output_path: Where to save the result
    """
    print("\n" + "=" * 50)
    print("VTON API — Virtual Try-On")
    print("=" * 50)

    # Check API key
    if not os.environ.get("FAL_KEY"):
        print("\n❌ FAL_KEY not set!")
        print("   1. Go to https://fal.ai and sign up")
        print("   2. Get your API key")
        print("   3. Run: set FAL_KEY=your_key_here")
        return None

    # Check files
    if not os.path.exists(model_image):
        print(f"❌ Model image not found: {model_image}")
        return None
    if not os.path.exists(garment_image):
        print(f"❌ Garment image not found: {garment_image}")
        return None

    print(f"\n   Model:   {model_image}")
    print(f"   Garment: {garment_image}")
    print(f"   Desc:    {description}")

    # Convert images to data URIs
    print("\n   Encoding images...")
    model_uri = image_to_data_uri(model_image)
    garment_uri = image_to_data_uri(garment_image)

    # Call the API
    print("   Sending to fal.ai IDM-VTON...")
    print("   (This takes 30-60 seconds)\n")

    result = fal_client.subscribe(
        "fal-ai/idm-vton",
        arguments={
            "human_image_url": model_uri,
            "garment_image_url": garment_uri,
            "description": description,
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )

    # Save result
    if result and "image" in result:
        image_url = result["image"]["url"]
        print(f"\n   ✅ Generated! URL: {image_url[:80]}...")

        # Download the image
        if not output_path:
            os.makedirs("output/vton_api", exist_ok=True)
            output_path = f"output/vton_api/vton_{int(asyncio.get_event_loop().time())}.png"

        import urllib.request
        urllib.request.urlretrieve(image_url, output_path)
        print(f"   ✅ Saved to: {output_path}")
        return output_path
    else:
        print(f"\n   ❌ Unexpected result: {result}")
        return None


if __name__ == "__main__":
    # Default test: model body + red hoodie
    result = run_vton(
        model_image="models/character_sheets/f1_body.png",
        garment_image="test_products/red_hoodie.png",
        description="Red cropped hoodie, streetwear style",
    )

    if result:
        print(f"\n🎉 Done! Check: {result}")
    else:
        print("\n💀 Failed.")
