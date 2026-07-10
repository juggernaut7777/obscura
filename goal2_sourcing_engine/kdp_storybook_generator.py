import os
import re
import sys
import json
import asyncio
import subprocess

# Auto-install reportlab if missing
try:
    import reportlab
except ImportError:
    print("[*] reportlab not found. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    import reportlab

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Safe print for Windows
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_DIR = os.path.join(BASE_DIR, "output_storybook")
os.makedirs(BOOKS_DIR, exist_ok=True)

class KDPStorybookGenerator:
    def __init__(self, trim_size_inch: float = 8.5, pages: int = 10):
        self.trim_size = trim_size_inch
        self.total_pages = pages
        
        # KDP Bleed Math:
        # Width: Trim + 0.125" bleed on outer edge
        self.pdf_width = (self.trim_size + 0.125) * inch
        # Height: Trim + 0.25" total bleed (0.125" top + 0.125" bottom)
        self.pdf_height = (self.trim_size + 0.25) * inch
        
        # Margins (inside bleed)
        self.safe_margin = 0.375 * inch # 0.25" KDP minimum + 0.125" bleed
        self.gutter = 0.5 * inch        # Gutter for binding

    def slugify(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        return re.sub(r'[\s_]+', '-', text)

    async def generate_storybook_content(self, theme: str) -> list:
        """Call Gemini to generate page-by-page story sentences and image prompts."""
        safe_print(f"[*] Planning KDP children's book for theme: '{theme}'...")
        
        prompt = (
            f"Write a {self.total_pages}-page children's storybook based on the theme: '{theme}'.\n"
            f"For each page, write:\n"
            f"1. Story Text: 1-2 simple, engaging sentences suitable for a 3-6 year old child.\n"
            f"2. Illustration Prompt: A highly detailed, visually descriptive image prompt for an AI generator (Flux/Midjourney).\n"
            f"   It must specify a consistent art style (e.g., 'Children's book illustration, watercolor and soft pastel, cute, clean, highly detailed, 300 DPI') "
            f"   and clearly describe the character, action, and setting to maintain character consistency across pages.\n\n"
            f"Return ONLY a JSON object containing a 'pages' key with a JSON array of objects:\n"
            f"{{\n"
            f"  \"pages\": [\n"
            f"    {{\"page\": 1, \"text\": \"story text here\", \"prompt\": \"image prompt here\"}}, ...\n"
            f"  ]\n"
            f"}}"
        )

        try:
            from litellm_router import shared_router
            messages = [{"role": "user", "content": prompt}]
            resp = await shared_router.get_chat_completion(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.7,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            content = resp["choices"][0]["message"]["content"].strip()
            # Parse JSON
            data = json.loads(content)
            if "pages" in data:
                return data["pages"]
            return data
        except Exception as e:
            safe_print(f"[!] LiteLLM content generation failed: {e}")
            # Fallback story
            fallback = []
            for i in range(1, self.total_pages + 1):
                fallback.append({
                    "page": i,
                    "text": f"This is page {i} of the story about {theme}. The little character went on a grand adventure.",
                    "prompt": f"Children's book illustration, watercolor style, cute character exploring, page {i} setting, detailed."
                })
            return fallback

    def compile_pdf(self, book_dir: str, story_data: list, compile_final: bool = False):
        """Assembles the PDF book layout with margins, headers, gutters, and bleed."""
        pdf_path = os.path.join(book_dir, "storybook_final.pdf" if compile_final else "storybook_draft.pdf")
        safe_print(f"[*] Compiling PDF book: {pdf_path}")
        
        c = canvas.Canvas(pdf_path, pagesize=(self.pdf_width, self.pdf_height))
        
        for idx, page_data in enumerate(story_data):
            page_num = page_data["page"]
            text = page_data["text"]
            img_prompt = page_data["prompt"]
            
            # Determine gutter edge based on odd/even page numbers (Alternating sides)
            # Odd pages (right side): Gutter is on the left
            # Even pages (left side): Gutter is on the right
            is_odd = page_num % 2 != 0
            
            # Calculate content boxes inside margins
            content_left = self.gutter if is_odd else self.safe_margin
            content_right = self.pdf_width - (self.safe_margin if is_odd else self.gutter)
            content_width = content_right - content_left
            
            # Illustration Box (top portion of the page)
            img_box_y = self.safe_margin + (1.8 * inch) # Raise it to leave room for text below
            img_box_h = self.pdf_height - img_box_y - self.safe_margin
            
            # Draw illustration (final image or draft placeholder)
            image_filename = f"page_{page_num:02d}.png"
            image_path = os.path.join(book_dir, image_filename)
            
            if compile_final and os.path.exists(image_path):
                # Draw high-res illustration
                try:
                    c.drawImage(image_path, content_left, img_box_y, width=content_width, height=img_box_h, preserveAspectRatio=True)
                except Exception as e:
                    safe_print(f"  [!] Error drawing image for page {page_num}: {e}")
                    self._draw_placeholder(c, content_left, img_box_y, content_width, img_box_h, page_num, img_prompt)
            else:
                # Draw placeholder box
                self._draw_placeholder(c, content_left, img_box_y, content_width, img_box_h, page_num, img_prompt)
                
            # Text layout (centered bottom portion)
            text_y = self.safe_margin + (0.5 * inch)
            
            c.setFont("Helvetica-Bold", 18)
            # Draw text cleanly wrapped (crude word wrapper for simple kids books)
            words = text.split()
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                line_str = " ".join(current_line)
                if c.stringWidth(line_str, "Helvetica-Bold", 18) > content_width:
                    current_line.pop()
                    lines.append(" ".join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(" ".join(current_line))
                
            # Draw each line centered
            line_offset = 0
            c.setFont("Helvetica", 16)
            for line in lines[:2]: # Max 2 lines to fit neatly
                tw = c.stringWidth(line, "Helvetica", 16)
                tx = content_left + (content_width - tw) / 2
                c.drawString(tx, text_y - line_offset, line)
                line_offset += 24
                
            # Page Number (Centered outer bottom edge)
            c.setFont("Helvetica", 9)
            num_str = str(page_num)
            num_w = c.stringWidth(num_str, "Helvetica", 9)
            num_x = content_left + (content_width - num_w) / 2
            c.drawString(num_x, 0.25 * inch, num_str)
            
            c.showPage()
            
        c.save()
        safe_print(f"[+] Book compiled successfully! PDF saved at {pdf_path}")

    def _draw_placeholder(self, c, x, y, w, h, page_num, prompt):
        # Draw dotted border
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(1)
        c.setDash(4, 4)
        c.rect(x, y, w, h)
        
        # Light grey background
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(x, y, w, h, fill=True, stroke=False)
        
        # Text instructions inside box
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x + 15, y + h - 30, f"Page {page_num} Illustration Placeholder (Flux/Flow)")
        
        c.setFont("Helvetica-Oblique", 9)
        # Wrap prompt text inside placeholder
        words = prompt.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if c.stringWidth(" ".join(current_line), "Helvetica-Oblique", 9) > w - 30:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        py_offset = 50
        for line in lines[:6]: # limit lines
            c.drawString(x + 15, y + h - py_offset, line)
            py_offset += 15

async def main():
    if len(sys.argv) < 2:
        safe_print("==================================================")
        safe_print("AMAZON KDP STORYBOOK GENERATOR")
        safe_print("==================================================")
        safe_print("Usage: python kdp_storybook_generator.py \"[Book Theme/Title]\" [--compile]")
        safe_print("Example: python kdp_storybook_generator.py \"A brave puppy saves the day\"")
        return

    theme = sys.argv[1]
    compile_final = "--compile" in sys.argv
    
    generator = KDPStorybookGenerator(trim_size_inch=8.5, pages=10)
    
    # Create target book dir
    slug = generator.slugify(theme)
    book_dir = os.path.join(BOOKS_DIR, slug)
    os.makedirs(book_dir, exist_ok=True)
    
    json_path = os.path.join(book_dir, "story_content.json")
    
    # Check if story text was already generated before to save API credits
    if os.path.exists(json_path):
        safe_print(f"[*] Loading existing story data from: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            story_data = json.load(f)
    else:
        story_data = await generator.generate_storybook_content(theme)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(story_data, f, indent=2, ensure_ascii=False)
        safe_print(f"[+] Saved story outlines and prompts to: {json_path}")
        
    generator.compile_pdf(book_dir, story_data, compile_final=compile_final)
    safe_print(f"\n📂 Storybook folder located at: {book_dir}")
    safe_print(f"Use Flux/Flow to generate the images matching the prompts in story_content.json, ")
    safe_print(f"save them as page_01.png, page_02.png etc. in that folder, and re-run with --compile to make final KDP PDF!")

if __name__ == "__main__":
    asyncio.run(main())
    # Force exit to prevent LiteLLM background thread hangs
    os._exit(0)
