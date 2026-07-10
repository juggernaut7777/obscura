"""
Watermark Utility
=================
Adds a subtle brand watermark to all generated images before posting.
Prevents competitors from stealing your AI-generated content.

Usage:
  from watermark import add_watermark
  add_watermark("output/outfit.png", "YOURBRAND")
"""
import os
from PIL import Image, ImageDraw, ImageFont


def add_watermark(image_path: str, brand_name: str = "STUDIO", opacity: int = 40, 
                  position: str = "bottom-right") -> str:
    """
    Adds a semi-transparent text watermark to an image.
    
    Args:
        image_path: Path to the image file
        brand_name: Your brand name text
        opacity: 0-255, lower = more transparent (40 is subtle)
        position: bottom-right, bottom-left, bottom-center
    
    Returns:
        Path to the watermarked image (overwrites original)
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        w, h = img.size
        
        # Create transparent overlay
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Calculate font size (2.5% of image width)
        font_size = max(int(w * 0.025), 14)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        
        # Get text dimensions
        text = f"© {brand_name}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        # Position
        margin = int(w * 0.03)
        if position == "bottom-right":
            x, y = w - text_w - margin, h - text_h - margin
        elif position == "bottom-left":
            x, y = margin, h - text_h - margin
        else:  # bottom-center
            x, y = (w - text_w) // 2, h - text_h - margin
        
        # Draw with opacity
        draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
        
        # Merge and save
        watermarked = Image.alpha_composite(img, overlay).convert("RGB")
        watermarked.save(image_path, quality=95)
        
        return image_path
    except Exception as e:
        print(f"⚠️  Watermark failed: {e}")
        return image_path


def watermark_batch(folder: str, brand_name: str = "STUDIO"):
    """Watermark all images in a folder."""
    count = 0
    for f in os.listdir(folder):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            add_watermark(os.path.join(folder, f), brand_name)
            count += 1
    print(f"✅ Watermarked {count} images in {folder}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        path = sys.argv[1]
        brand = sys.argv[2] if len(sys.argv) > 2 else "STUDIO"
        if os.path.isdir(path):
            watermark_batch(path, brand)
        else:
            add_watermark(path, brand)
            print(f"✅ Watermarked: {path}")
    else:
        print("Usage: python watermark.py <image_or_folder> [BRAND_NAME]")
