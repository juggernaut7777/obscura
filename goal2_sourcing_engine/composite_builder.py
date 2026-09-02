"""
COMPOSITE FLAT LAY BUILDER
==========================
Creates editorial-quality composite flat lay images by vertically stacking
top + bottom (+ optional shoe) product flat lays into a single 9:16 image.

Used by the outfit generation pipeline to create combined product shots
for the storefront gallery.
"""

import os
import glob
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw
from typing import Optional
from utils import safe_print


def _add_drop_shadow(
    image: Image.Image,
    offset: int = 8,
    blur: int = 15,
    color: tuple = (0, 0, 0, 40)
) -> Image.Image:
    """Adds a drop shadow to an RGBA image."""
    shadow = Image.new("RGBA", image.size, color)
    
    # Extract alpha channel to mask shadow if it exists, otherwise assume full opacity
    if "A" in image.getbands():
        alpha = image.getchannel("A")
        shadow.putalpha(alpha)
    
    # Expand canvas to fit shadow and blur without clipping
    padding = max(abs(offset), blur) * 2
    canvas = Image.new("RGBA", (image.width + padding, image.height + padding), (0, 0, 0, 0))
    
    # Paste shadow offset
    shadow_x = padding // 2 + offset
    shadow_y = padding // 2 + offset
    canvas.paste(shadow, (shadow_x, shadow_y), mask=shadow)
    
    # Blur the shadow
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    
    # Paste original image on top
    canvas.paste(image, (padding // 2, padding // 2), mask=image if "A" in image.getbands() else None)
    return canvas


def create_composite_flat_lay(
    top_front_path: str,
    bottom_front_path: str,
    shoe_front_path: Optional[str] = None,
    output_path: Optional[str] = None,
    canvas_width: int = 1080,
    canvas_height: int = 1920,
    bg_color: tuple = (245, 245, 245),  # Light gray background
    padding: int = 40,
    shadow_offset: int = 8,
    shadow_blur: int = 15,
    shadow_color: tuple = (0, 0, 0, 40)
) -> Optional[str]:
    """
    Merge top + bottom (+ shoe) flat lays into one vertical composite.
    
    Layout WITHOUT shoe (9:16):
    ┌─────────────────┐
    │    [padding]     │
    │   TOP FRONT      │  55% of usable height
    │                  │
    │    [gap]         │
    │  BOTTOM FRONT    │  45% of usable height
    │                  │
    │    [padding]     │
    └─────────────────┘
    
    Layout WITH shoe (9:16):
    ┌─────────────────┐
    │    [padding]     │
    │   TOP FRONT      │  45% of usable height
    │    [gap]         │
    │  BOTTOM FRONT    │  35% of usable height  
    │    [gap]         │
    │   SHOE FRONT     │  20% of usable height
    │    [padding]     │
    └─────────────────┘
    
    Each piece is:
    - Scaled to fit its allocated zone (maintaining aspect ratio)
    - Centered horizontally
    - Given a subtle drop shadow
    
    Args:
        top_front_path: Path to the top garment front flat lay image
        bottom_front_path: Path to the bottom garment front flat lay image  
        shoe_front_path: Optional path to shoe front image
        output_path: Where to save the composite. If None, saves next to top image.
        canvas_width: Output width (default 1080px)
        canvas_height: Output height (default 1920px for 9:16)
        bg_color: Background RGB color tuple
        padding: Outer padding in pixels
        shadow_offset: Drop shadow offset pixels
        shadow_blur: Drop shadow blur radius
        shadow_color: Drop shadow RGBA color
    
    Returns:
        Path to saved composite image, or None on failure.
    """
    try:
        if not output_path:
            output_dir = os.path.dirname(top_front_path)
            output_path = os.path.join(output_dir, "composite_flat_lay.png")
            
        # Create base canvas (RGB)
        canvas = Image.new("RGB", (canvas_width, canvas_height), bg_color)
        
        # Load images
        try:
            top_img = Image.open(top_front_path).convert("RGBA")
            bottom_img = Image.open(bottom_front_path).convert("RGBA")
            shoe_img = Image.open(shoe_front_path).convert("RGBA") if shoe_front_path else None
        except Exception as e:
            safe_print(f"[Error] Failed to load input images: {e}")
            return None
            
        max_w = canvas_width - 2 * padding
        gap = 20
        
        # Calculate zones
        usable_h = canvas_height - (2 * padding) - (gap if not shoe_img else 2 * gap)
        
        if shoe_img:
            top_h = int(usable_h * 0.45)
            bottom_h = int(usable_h * 0.35)
            shoe_h = usable_h - top_h - bottom_h
        else:
            top_h = int(usable_h * 0.55)
            bottom_h = usable_h - top_h
            shoe_h = 0
            
        def process_piece(img, max_width, max_height):
            """Scales image to fit within zone and adds drop shadow"""
            scale = min(max_width / img.width, max_height / img.height)
            new_w = int(img.width * scale)
            new_h = int(img.height * scale)
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            return _add_drop_shadow(
                resized, 
                offset=shadow_offset, 
                blur=shadow_blur, 
                color=shadow_color
            )
            
        y_offset = padding
        
        # Process and paste TOP
        processed_top = process_piece(top_img, max_w, top_h)
        x_top = (canvas_width - processed_top.width) // 2
        # Center vertically within its allocated zone
        y_top = y_offset + (top_h - processed_top.height) // 2
        canvas.paste(processed_top, (x_top, y_top), mask=processed_top)
        
        y_offset += top_h + gap
        
        # Process and paste BOTTOM
        processed_bottom = process_piece(bottom_img, max_w, bottom_h)
        x_bottom = (canvas_width - processed_bottom.width) // 2
        y_bottom = y_offset + (bottom_h - processed_bottom.height) // 2
        canvas.paste(processed_bottom, (x_bottom, y_bottom), mask=processed_bottom)
        
        y_offset += bottom_h + gap
        
        # Process and paste SHOE
        if shoe_img:
            processed_shoe = process_piece(shoe_img, max_w, shoe_h)
            x_shoe = (canvas_width - processed_shoe.width) // 2
            y_shoe = y_offset + (shoe_h - processed_shoe.height) // 2
            canvas.paste(processed_shoe, (x_shoe, y_shoe), mask=processed_shoe)
            
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save output
        canvas.save(output_path, "PNG")
        safe_print(f"[Success] Composite saved to: {output_path}")
        return output_path
        
    except Exception as e:
        safe_print(f"[Error] Failed to create composite flat lay: {e}")
        return None


def create_outfit_composite(
    outfit_dir: str,
    top_dir: Optional[str] = None,
    bottom_dir: Optional[str] = None,
    shoe_dir: Optional[str] = None
) -> Optional[str]:
    """
    Higher-level function that finds front images in product directories
    and calls create_composite_flat_lay.
    
    Looks for front_angle_1.* in each directory.
    Saves composite to outfit_dir/composite_flat_lay.png
    """
    try:
        def find_front_image(d):
            if not d or not os.path.isdir(d):
                return None
            for ext in ['png', 'jpg', 'jpeg', 'webp']:
                pattern = os.path.join(d, f"front_angle_1.{ext}")
                matches = glob.glob(pattern)
                if matches:
                    return matches[0]
            return None
            
        top_img = find_front_image(top_dir)
        bottom_img = find_front_image(bottom_dir)
        shoe_img = find_front_image(shoe_dir)
        
        if not top_img or not bottom_img:
            safe_print("[Error] Need at least top and bottom front images for composite.")
            return None
            
        out_path = os.path.join(outfit_dir, "composite_flat_lay.png")
        return create_composite_flat_lay(
            top_front_path=top_img, 
            bottom_front_path=bottom_img, 
            shoe_front_path=shoe_img, 
            output_path=out_path
        )
    except Exception as e:
        safe_print(f"[Error] Failed to create outfit composite: {e}")
        return None
