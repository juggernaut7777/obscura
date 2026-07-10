"""
Carousel Builder Module
Takes raw VTON-generated images (and product images) and builds
ready-to-post 5-image carousels with native-looking social media text overlays.
"""
import os
import requests
from io import BytesIO
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    # We will need to pip install Pillow
    print("WARNING: Pillow library not found. Text overlays will be disabled unless installed.")
    Image, ImageDraw, ImageFont, ImageFilter = None, None, None, None

def download_image(url: str) -> Image.Image:
    """Helper to download an image from a URL into a Pillow Image object."""
    if not Image:
        return None
    try:
        response = requests.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        # Return a blank gray image as fallback for testing
        return Image.new("RGBA", (1080, 1350), (128, 128, 128, 255))

def add_instagram_text_sticker(img: Image.Image, text: str, y_position: int = 700) -> Image.Image:
    """
    Simulates the native Instagram/TikTok text overlay.
    White text with a subtle black background box.
    """
    if not Image:
        return img
    
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Try to load a bold font, fallback to default
    try:
        # Standard paths for Windows fonts
        font = ImageFont.truetype("arialbd.ttf", 60)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text bounding box (centering)
    # PIL 9.5+ uses textbbox, older versions use textsize
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        text_width, text_height = draw.textsize(text, font=font)
    
    x_position = (width - text_width) // 2

    # Draw semi-transparent black background box for the text
    padding = 20
    box_coords = [
        x_position - padding, 
        y_position - padding, 
        x_position + text_width + padding, 
        y_position + text_height + padding
    ]
    draw.rectangle(box_coords, fill=(0, 0, 0, 160), outline=(255, 255, 255, 50), width=2)
    
    # Draw the white text
    draw.text((x_position, y_position), text, font=font, fill=(255, 255, 255, 255))
    
    return img

def create_split_screen_cta(model_img_url: str, product_img_url: str) -> Image.Image:
    """
    Creates Slide 5: The Call To Action.
    Splits the screen 50/50: Top is the model, Bottom is the flat-lay product.
    """
    if not Image:
        return None
        
    model_img = download_image(model_img_url)
    product_img = download_image(product_img_url)
    
    # Standard Instagram Portrait Size
    final_size = (1080, 1350)
    final_img = Image.new("RGBA", final_size, (255, 255, 255, 255))
    
    # Resize and crop model to top half
    top_half = final_size[1] // 2
    model_img = model_img.resize((final_size[0], int(final_size[0] * (model_img.height / model_img.width))))
    model_cropped = model_img.crop((0, 0, final_size[0], top_half))
    final_img.paste(model_cropped, (0, 0))
    
    # Resize and paste product to bottom half with padding
    product_img.thumbnail((800, 600))  # keep aspect ratio
    p_w, p_h = product_img.size
    p_x = (final_size[0] - p_w) // 2
    p_y = top_half + (top_half - p_h) // 2
    final_img.paste(product_img, (p_x, p_y), product_img if product_img.mode == 'RGBA' else None)
    
    # Add the CTA Text
    final_img = add_instagram_text_sticker(final_img, "LINKED IN MY BIO! 🏃‍♀️💨", y_position=final_size[1] - 200)
    
    return final_img

def build_carousel(
    vton_image_urls: list[str], 
    product_image_url: str, 
    hook_text: str, 
    output_dir: str = "output/carousels"
) -> list[str]:
    """
    Takes 3 VTON images and builds a full 5-image carousel sequence.
    Returns local file paths to the generated carousel images.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    print(f"🖼️ Building 5-Image Carousel for Hook: '{hook_text}'...")
    
    # Ensure we have at least 3 VTON images (fallback if not)
    while len(vton_image_urls) < 3:
        vton_image_urls.append(vton_image_urls[0] if vton_image_urls else "https://via.placeholder.com/1080x1350")

    # Slide 1: The Hook (Image 0 + big text)
    img_hook = download_image(vton_image_urls[0])
    img_hook = add_instagram_text_sticker(img_hook, hook_text, y_position=600)
    path = f"{output_dir}/slide_1_hook.png"
    img_hook.save(path)
    generated_files.append(path)
    
    # Slide 2: The Proof 1 (Image 1 + subtle text)
    img_proof1 = download_image(vton_image_urls[1])
    img_proof1 = add_instagram_text_sticker(img_proof1, "The material is insanely soft", y_position=1100)
    path = f"{output_dir}/slide_2_proof.png"
    img_proof1.save(path)
    generated_files.append(path)
    
    # Slide 3: The Proof 2 (Image 2 + subtle text)
    img_proof2 = download_image(vton_image_urls[2])
    img_proof2 = add_instagram_text_sticker(img_proof2, "Literally my new obsession", y_position=1100)
    path = f"{output_dir}/slide_3_proof.png"
    img_proof2.save(path)
    generated_files.append(path)
    
    # Slide 4: The Detail (Cropped/zoomed version of Image 0)
    img_detail = download_image(vton_image_urls[0])
    if Image:
        # Crop to the center to show detail
        w, h = img_detail.size
        crop_box = (w//4, h//4, w - w//4, h - h//4)
        img_detail = img_detail.crop(crop_box).resize((1080, 1350))
    path = f"{output_dir}/slide_4_detail.png"
    img_detail.save(path)
    generated_files.append(path)
    
    # Slide 5: The CTA (Split screen Model + Product)
    img_cta = create_split_screen_cta(vton_image_urls[0], product_image_url)
    path = f"{output_dir}/slide_5_cta.png"
    img_cta.save(path)
    generated_files.append(path)
    
    print(f"✅ Carousel built! 5 images saved to {output_dir}/")
    return generated_files

if __name__ == "__main__":
    # Test execution
    mock_vton_urls = [
        "https://via.placeholder.com/1080x1350.png?text=VTON+Pose+1",
        "https://via.placeholder.com/1080x1350.png?text=VTON+Pose+2",
        "https://via.placeholder.com/1080x1350.png?text=VTON+Pose+3"
    ]
    mock_product_url = "https://via.placeholder.com/800x800.png?text=Flatlay+Sneaker"
    
    files = build_carousel(
        vton_image_urls=mock_vton_urls,
        product_image_url=mock_product_url,
        hook_text="Things TikTok made me buy 👉"
    )
