import os
import re
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Auto-install reportlab if missing
try:
    import reportlab
except ImportError:
    print("[*] reportlab not found. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    import reportlab

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

# Safe print for Windows
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "brand_leads"
OUTPUT_DIR.mkdir(exist_ok=True)
READY_DIR = BASE_DIR / "OUTPUT_READY_FOR_SALE"

class LookbookPDFGenerator:
    def __init__(self, brand_name: str = "Demo Brand", width_inch: float = 8.5, height_inch: float = 11.0):
        self.brand_name = brand_name
        self.width_inch = width_inch
        self.height_inch = height_inch
        
        # KDP / Print Bleed Math:
        # Standard bleed is 0.125" on outer edges
        self.pdf_width = (self.width_inch + 0.25) * inch # bleed left + bleed right
        self.pdf_height = (self.height_inch + 0.25) * inch # bleed top + bleed bottom
        
        # Margins (inside bleed)
        self.safe_margin = 0.375 * inch # 0.25" safe zone + 0.125" bleed
        self.gutter = 0.5 * inch        # Gutter for binding
        
        # Color Palette
        self.color_charcoal = HexColor("#1A1A1A")
        self.color_gold = HexColor("#D4AF37")
        self.color_offwhite = HexColor("#F5F5F0")
        self.color_darkgrey = HexColor("#333333")
        self.color_lightgrey = HexColor("#E0E0D8")

    def _get_page_geometry(self, page_num: int):
        """Alternates margins based on page parity to handle binding gutters."""
        is_odd = page_num % 2 != 0
        content_left = self.gutter if is_odd else self.safe_margin
        content_right = self.pdf_width - (self.safe_margin if is_odd else self.gutter)
        content_width = content_right - content_left
        return content_left, content_right, content_width

    def compile_pdf(self, products: list, output_filename: str):
        pdf_path = OUTPUT_DIR / output_filename
        safe_print(f"[*] Starting PDF Lookbook Compilation: {pdf_path}")
        
        c = canvas.Canvas(str(pdf_path), pagesize=(self.pdf_width, self.pdf_height))
        
        # 1. PAGE 1: COVER PAGE (Luxury Dark Theme)
        self._draw_cover_page(c)
        
        # 2. PAGE 2: EXECUTIVE SUMMARY & PITCH PROPOSAL
        self._draw_summary_page(c)
        
        # 3. PAGES 3+: PRODUCTS BEFORE/AFTER
        # We display each product on a 2-page spread
        # Left page: Original asset (flatlay, basic shot)
        # Right page: AI editorial model shot
        page_idx = 3
        for p in products:
            # Draw Original Asset Page (Left Page - Even page number)
            self._draw_product_original_page(c, p, page_idx)
            page_idx += 1
            
            # Draw AI Lookbook Render Page (Right Page - Odd page number)
            self._draw_product_ai_page(c, p, page_idx)
            page_idx += 1
            
        # 4. LAST PAGE: PACKAGES & CTA
        self._draw_cta_page(c, page_idx)
        
        c.save()
        safe_print(f"[+] Lookbook pitch compiled successfully! Saved to: {pdf_path}")

    def _draw_cover_page(self, c):
        # Fill cover with dark charcoal background
        c.setFillColor(self.color_charcoal)
        c.rect(0, 0, self.pdf_width, self.pdf_height, fill=True, stroke=False)
        
        # Accent gold frame
        c.setStrokeColor(self.color_gold)
        c.setLineWidth(1.5)
        c.rect(self.safe_margin, self.safe_margin, self.pdf_width - 2 * self.safe_margin, self.pdf_height - 2 * self.safe_margin)
        
        # Brand Name / Obscura Header
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(self.pdf_width / 2.0, self.pdf_height - 3.5 * inch, self.brand_name.upper())
        
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica", 14)
        c.drawCentredString(self.pdf_width / 2.0, self.pdf_height - 4.2 * inch, "x")
        
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(self.pdf_width / 2.0, self.pdf_height - 4.8 * inch, "OBSCURA STUDIO")
        
        # Title
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(self.pdf_width / 2.0, self.pdf_height - 6.5 * inch, "EDITORIAL CONTENT UPGRADE PROPOSAL")
        
        c.setFillColor(self.color_lightgrey)
        c.setFont("Helvetica-Oblique", 11)
        c.drawCentredString(self.pdf_width / 2.0, self.pdf_height - 7.0 * inch, "Automated Fashion Curation & High-End AI Photoshoots")
        
        # Footer
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.pdf_width / 2.0, 1.5 * inch, "CONFIDENTIAL PROPOSAL FOR INTERNAL REVIEW")
        
        c.setFillColor(self.color_lightgrey)
        c.setFont("Helvetica", 9)
        c.drawCentredString(self.pdf_width / 2.0, 1.1 * inch, f"Generated: {datetime.now().strftime('%B %Y')} | Version 1.0")
        
        c.showPage()

    def _draw_summary_page(self, c):
        page_num = 2
        cl, cr, cw = self._get_page_geometry(page_num)
        
        # Page background
        c.setFillColor(self.color_offwhite)
        c.rect(0, 0, self.pdf_width, self.pdf_height, fill=True, stroke=False)
        
        # Draw header
        c.setFillColor(self.color_charcoal)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(cl, self.pdf_height - 1.2 * inch, "EXECUTIVE SUMMARY")
        
        c.setStrokeColor(self.color_gold)
        c.setLineWidth(1)
        c.line(cl, self.pdf_height - 1.3 * inch, cr, self.pdf_height - 1.3 * inch)
        
        # Draw value proposition text
        c.setFillColor(self.color_darkgrey)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(cl, self.pdf_height - 1.8 * inch, f"Elevating {self.brand_name}'s Visual Identity & E-Commerce Conversions")
        
        text_y = self.pdf_height - 2.2 * inch
        paragraphs = [
            "In modern digital retail, visual presentation represents the single most important factor governing e-commerce conversion rates. High-quality editorial and lifestyle photography can increase add-to-cart clicks by over 30% and boost brand value perception.",
            "Traditional photoshoots are expensive and slow. Hiring models, photographers, booking studios, and editing images cost thousands of dollars per collection. OBSCURA solves this using advanced AI fashion orchestration.",
            "We take your existing flat-lay, hanger, or mannequin product images and programmatically drape them onto hyperrealistic AI models situated in premium, stylized locations. The results are indistinguishable from high-end agency photoshoots.",
            f"This proposal presents a direct before-and-after comparison using actual items from {self.brand_name}'s current collection. We showcase how basic e-commerce flat layouts are instantly elevated into premium, Vogue-like editorial campaign material.",
            "Key ROI Benefits:",
            "  • 90% Cost Reduction compared to hiring human models and photographers.",
            "  • Instant Turnaround: Complete collections generated and ready in days instead of weeks.",
            "  • Platform Optimized: Formatted instantly for Shopify, Instagram carousels, and print catalogs."
        ]
        
        c.setFont("Helvetica", 11)
        for p in paragraphs:
            # Basic manual paragraph drawing/wrapping
            words = p.split()
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                if c.stringWidth(" ".join(current_line), "Helvetica", 11) > cw:
                    current_line.pop()
                    lines.append(" ".join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(" ".join(current_line))
                
            for line in lines:
                c.drawString(cl, text_y, line)
                text_y -= 18
            text_y -= 10
            
        self._draw_page_footer(c, page_num, cl, cw)
        c.showPage()

    def _draw_product_original_page(self, c, product: dict, page_num: int):
        cl, cr, cw = self._get_page_geometry(page_num)
        
        # Clean white background for original
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, self.pdf_width, self.pdf_height, fill=True, stroke=False)
        
        # Title
        c.setFillColor(self.color_charcoal)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(cl, self.pdf_height - 1.0 * inch, f"ORIGINAL VISUAL: {product['name'].upper()}")
        
        # Subtitle
        c.setFont("Helvetica", 10)
        c.setFillColor(self.color_darkgrey)
        c.drawString(cl, self.pdf_height - 1.2 * inch, f"Flat Lay / Current Store Listing Asset")
        
        c.setStrokeColor(self.color_lightgrey)
        c.setLineWidth(1)
        c.line(cl, self.pdf_height - 1.3 * inch, cr, self.pdf_height - 1.3 * inch)
        
        # Drawing original image box
        img_y = self.safe_margin + 2.5 * inch
        img_h = self.pdf_height - img_y - 1.6 * inch
        
        original_img = product.get("original_image")
        if original_img and os.path.exists(original_img):
            try:
                c.drawImage(original_img, cl, img_y, width=cw, height=img_h, preserveAspectRatio=True)
            except Exception as e:
                safe_print(f"  [!] Error drawing original image: {e}")
                self._draw_placeholder_box(c, cl, img_y, cw, img_h, "Original Product Flat Lay")
        else:
            self._draw_placeholder_box_vector(c, cl, img_y, cw, img_h, "Original Product Flat Lay")
            
        # Metadata / Spec Box at bottom
        spec_y = self.safe_margin + 0.3 * inch
        spec_h = 2.0 * inch
        c.setFillColor(self.color_offwhite)
        c.rect(cl, spec_y, cw, spec_h, fill=True, stroke=False)
        c.setStrokeColor(self.color_lightgrey)
        c.rect(cl, spec_y, cw, spec_h, fill=False, stroke=True)
        
        # Write specs
        c.setFillColor(self.color_charcoal)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(cl + 15, spec_y + spec_h - 25, "E-COMMERCE LISTING METADATA")
        
        c.setFont("Helvetica", 9)
        c.setFillColor(self.color_darkgrey)
        c.drawString(cl + 15, spec_y + spec_h - 45, f"Product Name: {product.get('name', 'N/A')}")
        c.drawString(cl + 15, spec_y + spec_h - 60, f"Listed Price: {product.get('price', 'N/A')}")
        
        desc = product.get("description", "No description provided.")
        c.drawString(cl + 15, spec_y + spec_h - 80, "Product Description:")
        
        # Wrap description
        desc_words = desc.split()
        desc_lines = []
        curr_line = []
        for w in desc_words:
            curr_line.append(w)
            if c.stringWidth(" ".join(curr_line), "Helvetica", 9) > cw - 30:
                curr_line.pop()
                desc_lines.append(" ".join(curr_line))
                curr_line = [w]
        if curr_line:
            desc_lines.append(" ".join(curr_line))
            
        d_y = spec_y + spec_h - 95
        for line in desc_lines[:4]: # Max 4 lines
            c.drawString(cl + 15, d_y, line)
            d_y -= 12
            
        self._draw_page_footer(c, page_num, cl, cw)
        c.showPage()

    def _draw_product_ai_page(self, c, product: dict, page_num: int):
        cl, cr, cw = self._get_page_geometry(page_num)
        
        # Luxury dark grey background for editorial reveal
        c.setFillColor(self.color_charcoal)
        c.rect(0, 0, self.pdf_width, self.pdf_height, fill=True, stroke=False)
        
        # Accent gold frame
        c.setStrokeColor(self.color_gold)
        c.setLineWidth(1)
        c.rect(cl, self.safe_margin, cw, self.pdf_height - 2 * self.safe_margin)
        
        # Title
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(cl + 15, self.pdf_height - 1.0 * inch, f"AI EDITORIAL REVEAL: {product['name'].upper()}")
        
        # Subtitle
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor("#FFFFFF"))
        c.drawString(cl + 15, self.pdf_height - 1.2 * inch, "Lookbook Campaign Model Curation")
        
        c.setStrokeColor(self.color_gold)
        c.line(cl + 15, self.pdf_height - 1.3 * inch, cr - 15, self.pdf_height - 1.3 * inch)
        
        # Draw AI lookbook image
        img_y = self.safe_margin + 2.5 * inch
        img_h = self.pdf_height - img_y - 1.6 * inch
        
        ai_img = product.get("ai_image")
        if ai_img and os.path.exists(ai_img):
            try:
                c.drawImage(ai_img, cl + 15, img_y, width=cw - 30, height=img_h, preserveAspectRatio=True)
            except Exception as e:
                safe_print(f"  [!] Error drawing AI image: {e}")
                self._draw_placeholder_box(c, cl + 15, img_y, cw - 30, img_h, "AI Editorial Model Render", is_dark=True)
        else:
            self._draw_placeholder_box_vector(c, cl + 15, img_y, cw - 30, img_h, "AI Editorial Model Render", is_dark=True)
            
        # Analysis / Contrast box at bottom
        box_y = self.safe_margin + 0.3 * inch
        box_h = 2.0 * inch
        c.setFillColor(self.color_darkgrey)
        c.rect(cl + 15, box_y, cw - 30, box_h, fill=True, stroke=False)
        c.setStrokeColor(self.color_gold)
        c.rect(cl + 15, box_y, cw - 30, box_h, fill=False, stroke=True)
        
        # Narrative
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(cl + 30, box_y + box_h - 25, "VISUAL RE-STYLING NOTES & ROI")
        
        c.setFont("Helvetica", 9)
        c.setFillColor(HexColor("#FFFFFF"))
        notes = [
            f"• Model Styling: Garment mapped to professional model matching {self.brand_name}'s style.",
            "• Setting: Dressed in a minimalist Paris street scene with cinematic soft lighting.",
            "• Texture Retention: Fabric details and stitching patterns are realistically preserved.",
            "• Marketing Value: Perfect for Instagram carousels, home banner, or high-end catalog print."
        ]
        n_y = box_y + box_h - 45
        for note in notes:
            c.drawString(cl + 30, n_y, note)
            n_y -= 15
            
        self._draw_page_footer(c, page_num, cl, cw, is_dark=True)
        c.showPage()

    def _draw_cta_page(self, c, page_num: int):
        cl, cr, cw = self._get_page_geometry(page_num)
        
        # Cover with dark background
        c.setFillColor(self.color_charcoal)
        c.rect(0, 0, self.pdf_width, self.pdf_height, fill=True, stroke=False)
        
        # Gold frame
        c.setStrokeColor(self.color_gold)
        c.setLineWidth(1.5)
        c.rect(self.safe_margin, self.safe_margin, self.pdf_width - 2 * self.safe_margin, self.pdf_height - 2 * self.safe_margin)
        
        # Header
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(self.pdf_width / 2.0, self.pdf_height - 2.0 * inch, "LOOKBOOK AGENCY SERVICES")
        
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica", 12)
        c.drawCentredString(self.pdf_width / 2.0, self.pdf_height - 2.4 * inch, "Select the plan that matches your launch velocity")
        
        # Pricing Cards
        card_w = 2.2 * inch
        card_h = 3.5 * inch
        card_y = self.pdf_height - 6.5 * inch
        
        # Card 1: Starter
        c.setFillColor(self.color_darkgrey)
        c.rect(cl + 0.1 * inch, card_y, card_w, card_h, fill=True, stroke=False)
        c.setStrokeColor(self.color_gold)
        c.rect(cl + 0.1 * inch, card_y, card_w, card_h, fill=False, stroke=True)
        
        # Card 2: Growth
        c.setFillColor(self.color_darkgrey)
        c.rect(cl + 2.5 * inch, card_y, card_w, card_h, fill=True, stroke=False)
        c.setStrokeColor(self.color_gold)
        c.setLineWidth(2)
        c.rect(cl + 2.5 * inch, card_y, card_w, card_h, fill=False, stroke=True)
        
        # Card 3: Custom
        c.setLineWidth(1)
        c.setFillColor(self.color_darkgrey)
        c.rect(cl + 4.9 * inch, card_y, card_w, card_h, fill=True, stroke=False)
        c.setStrokeColor(self.color_gold)
        c.rect(cl + 4.9 * inch, card_y, card_w, card_h, fill=False, stroke=True)
        
        # Card 1 Text
        cx1 = cl + 1.2 * inch
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(cx1, card_y + card_h - 30, "STARTER PACK")
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(cx1, card_y + card_h - 70, "$299")
        c.setFont("Helvetica", 9)
        c.setFillColor(self.color_lightgrey)
        c.drawCentredString(cx1, card_y + card_h - 90, "Single Collection Curation")
        c.drawString(cx1 - 65, card_y + card_h - 130, "• 5 High-End AI Renders")
        c.drawString(cx1 - 65, card_y + card_h - 150, "• 2 Custom Model Faces")
        c.drawString(cx1 - 65, card_y + card_h - 170, "• 3 Scene Backgrounds")
        c.drawString(cx1 - 65, card_y + card_h - 190, "• 72-Hour Delivery")
        
        # Card 2 Text
        cx2 = cl + 3.6 * inch
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(cx2, card_y + card_h - 30, "GROWTH PACK")
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(cx2, card_y + card_h - 70, "$599")
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(self.color_gold)
        c.drawCentredString(cx2, card_y + card_h - 90, "★ MOST POPULAR ★")
        c.setFont("Helvetica", 9)
        c.setFillColor(self.color_lightgrey)
        c.drawString(cx2 - 65, card_y + card_h - 130, "• 15 High-End AI Renders")
        c.drawString(cx2 - 65, card_y + card_h - 150, "• 4 Custom Model Faces")
        c.drawString(cx2 - 65, card_y + card_h - 170, "• 6 Scene Backgrounds")
        c.drawString(cx2 - 65, card_y + card_h - 190, "• Instagram Carousel Files")
        c.drawString(cx2 - 65, card_y + card_h - 210, "• Free Re-renders (Max 3)")
        
        # Card 3 Text
        cx3 = cl + 6.0 * inch
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(cx3, card_y + card_h - 30, "RETAINER")
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(cx3, card_y + card_h - 70, "$1,200/mo")
        c.setFont("Helvetica", 9)
        c.setFillColor(self.color_lightgrey)
        c.drawCentredString(cx3, card_y + card_h - 90, "Continuous Content Factory")
        c.drawString(cx3 - 65, card_y + card_h - 130, "• 40+ Renders / Month")
        c.drawString(cx3 - 65, card_y + card_h - 150, "• Dedicated Virtual Model")
        c.drawString(cx3 - 65, card_y + card_h - 170, "• Multi-Angle Outfit Merges")
        c.drawString(cx3 - 65, card_y + card_h - 190, "• Priority Support")
        c.drawString(cx3 - 65, card_y + card_h - 210, "• UGC Faceless Video Ads")

        # CTA Pitch Box at bottom
        c.setFillColor(self.color_darkgrey)
        c.rect(cl + 0.1 * inch, 1.2 * inch, cw - 0.2 * inch, 1.6 * inch, fill=True, stroke=False)
        c.setStrokeColor(self.color_gold)
        c.rect(cl + 0.1 * inch, 1.2 * inch, cw - 0.2 * inch, 1.6 * inch, fill=False, stroke=True)
        
        c.setFillColor(self.color_gold)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(self.pdf_width / 2.0, 2.4 * inch, "GET STARTED TODAY")
        
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica", 10)
        c.drawCentredString(self.pdf_width / 2.0, 2.1 * inch, "Interested in upgrading your catalog? We will build you 3 sample model photos for free.")
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(self.color_gold)
        c.drawCentredString(self.pdf_width / 2.0, 1.6 * inch, "Contact: studio@obscura-agency.com | discord: obscura_fashion")

        self._draw_page_footer(c, page_num, cl, cw, is_dark=True)
        c.showPage()

    def _draw_page_footer(self, c, page_num: int, cl: float, cw: float, is_dark: bool = False):
        c.setFont("Helvetica", 8)
        c.setFillColor(self.color_gold if is_dark else self.color_darkgrey)
        
        # Center page number
        c.drawCentredString(self.pdf_width / 2.0, 0.25 * inch, str(page_num))
        
        # Left/Right running text
        c.drawString(cl, 0.25 * inch, f"{self.brand_name.upper()} x OBSCURA STUDIO")
        
        r_text = "CONFIDENTIAL LOOKBOOK PROPOSAL"
        tw = c.stringWidth(r_text, "Helvetica", 8)
        c.drawString(cl + cw - tw, 0.25 * inch, r_text)

    def _draw_placeholder_box(self, c, x, y, w, h, title, is_dark=False):
        c.setFillColorRGB(0.15, 0.15, 0.15) if is_dark else c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x, y, w, h, fill=True, stroke=False)
        
        c.setStrokeColor(self.color_gold if is_dark else self.color_darkgrey)
        c.setLineWidth(1)
        c.setDash(4, 4)
        c.rect(x, y, w, h, fill=False, stroke=True)
        c.setDash() # Restore solid
        
        c.setFillColor(self.color_gold if is_dark else self.color_charcoal)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + w/2.0, y + h/2.0 + 10, title)
        
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(HexColor("#FFFFFF") if is_dark else self.color_darkgrey)
        c.drawCentredString(x + w/2.0, y + h/2.0 - 15, "[Image File Missing or Offline]")

    def _draw_placeholder_box_vector(self, c, x, y, w, h, title, is_dark=False):
        """Draws a nice vector outline for lookbook elements in demo mode."""
        self._draw_placeholder_box(c, x, y, w, h, title, is_dark)
        
        # Draw nice aesthetic cross lines inside box to look like design blueprint
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        if is_dark:
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.setLineWidth(0.5)
        c.line(x, y, x + w, y + h)
        c.line(x, y + h, x + w, y)

def run_scan() -> list:
    """Scans the local OUTPUT_READY_FOR_SALE/ directory for matched generated products."""
    products = []
    if not READY_DIR.exists():
        safe_print(f"[!] Scan path not found: {READY_DIR}")
        return products
        
    safe_print(f"[*] Scanning {READY_DIR} for completed items...")
    
    for subdir in READY_DIR.iterdir():
        if subdir.is_dir():
            # Look for generated editorial images
            editorial_images = []
            for ext in ["*editorial*.png", "*editorial*.jpg", "*_0.png", "*_1.png"]:
                editorial_images.extend(list(subdir.glob(ext)))
                
            # Look for original source product shots
            source_images = []
            for ext in ["IMG_*.jpg", "IMG_*.jpeg", "IMG_*.png", "angle_*.jpg", "angle_*.png"]:
                source_images.extend(list(subdir.glob(ext)))
                
            # Fallback for source images if none match naming pattern
            if not source_images:
                for img in subdir.glob("*"):
                    if img.is_file() and img.suffix.lower() in [".png", ".jpg", ".jpeg"] and "editorial" not in img.name:
                        source_images.append(img)
            
            if editorial_images and source_images:
                # We have a match!
                ai_img = str(editorial_images[0])
                orig_img = str(source_images[0])
                
                # Deduce name from folder name
                folder_name = subdir.name
                # Strip dates/hashes
                name_clean = folder_name
                # Match pattern: 20260505_110952_m2_product_drop_20260505_110452_947b
                match = re.search(r'product_drop_.*', folder_name)
                if match:
                    name_clean = match.group(0).replace("product_drop_", "")
                    # Strip trailing hash
                    name_clean = re.sub(r'_[a-f0-9]+$', '', name_clean)
                else:
                    # e.g. 20260505_123912_m1_product_drop...
                    name_clean = folder_name.split("_")[-1]
                
                # Check for metadata
                meta = {}
                meta_file = subdir / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, encoding="utf-8") as mf:
                            meta = json.load(mf)
                    except:
                        pass
                
                products.append({
                    "name": meta.get("product_name") or name_clean.replace("-", " ").title(),
                    "price": meta.get("price_string") or "$49.00",
                    "description": meta.get("description") or f"High-quality garment from {name_clean.replace('-', ' ').title()} collection.",
                    "original_image": orig_img,
                    "ai_image": ai_img
                })
                safe_print(f"   [FOUND] Match in {subdir.name} -> {products[-1]['name']}")
                
    safe_print(f"[+] Scan complete. Found {len(products)} completed products.")
    return products

def get_demo_products() -> list:
    """Returns a list of dummy products for the demo lookbook."""
    return [
        {
            "name": "Luxury Essential Hoodie",
            "price": "$129.00",
            "description": "Heavyweight French terry organic cotton hoodie. Features double-lined hood, dropped shoulders, and relaxed streetwear fit. Preshrunk and garment-dyed in charcoal grey.",
            "original_image": "",
            "ai_image": ""
        },
        {
            "name": "Streetwear Oversized Sweatpants",
            "price": "$95.00",
            "description": "Premium matching sweatpants in heavyweight cotton. Thick elastic waistband with internal drawstrings, side welt pockets, and elastic cuffs. Styled for casual luxury.",
            "original_image": "",
            "ai_image": ""
        },
        {
            "name": "Boxy Cropped Tee",
            "price": "$45.00",
            "description": "Combed ring-spun cotton heavyweight jersey tee. Classic boxy silhouette, cropped length, and tight crewneck collar. Available in off-white.",
            "original_image": "",
            "ai_image": ""
        }
    ]

def main():
    parser = argparse.ArgumentParser(description="Compile print-ready B2B Lookbook Pitch PDFs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true", help="Generate a demo PDF using dummy mockups.")
    group.add_argument("--scan", action="store_true", help="Generate a PDF by scanning OUTPUT_READY_FOR_SALE/ directory.")
    
    parser.add_argument("--brand", type=str, default="Aventis Streetwear", help="Name of the brand to generate lookbook for.")
    parser.add_argument("--output", type=str, help="Output filename (saved in brand_leads/).")
    
    args = parser.parse_args()
    
    brand = args.brand
    output_file = args.output
    
    if args.demo:
        safe_print(f"[*] Running in DEMO mode for brand: {brand}")
        products = get_demo_products()
        if not output_file:
            output_file = "demo_lookbook_pitch.pdf"
    else:
        safe_print(f"[*] Running in SCAN mode for folder: {READY_DIR}")
        products = run_scan()
        if not products:
            safe_print("[!] No completed products found in SCAN mode. Cannot compile PDF. Try --demo first.")
            sys.exit(1)
        if not output_file:
            clean_brand = re.sub(r'[^\w\s-]', '', brand.lower().strip())
            clean_brand = re.sub(r'[\s_]+', '_', clean_brand)
            output_file = f"lookbook_pitch_{clean_brand}.pdf"
            
    generator = LookbookPDFGenerator(brand_name=brand)
    generator.compile_pdf(products, output_file)

if __name__ == "__main__":
    main()
