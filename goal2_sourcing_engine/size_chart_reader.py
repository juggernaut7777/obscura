"""
SIZE CHART READER — Gemini Vision Logic
=======================================
Analyzes photos of size charts sent via Discord and extracts
the measurements/available sizes into the product metadata.
"""

import os
import json
import google.generativeai as genai
from PIL import Image

def extract_size_info(image_path):
    """
    Uses Gemini Vision to read a size chart image.
    Returns a string summary: "Available: S, M, L, XL | Fits oversized"
    """
    if not os.path.exists(image_path):
        return "No chart found"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "API Key Missing"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash') # Fast vision
        
        with Image.open(image_path) as img:
            prompt = """
            Analyze this image of a clothing size chart. 
            1. List the available sizes (e.g. S, M, L, XL, 40, 42, etc.).
            2. Give a brief recommendation on fit (e.g. 'True to size', 'Oversized', 'Runs small').
            
            Return ONLY a short string in this format:
            Sizes: [Size List] | Fit: [Recommendation]
            """
            
            response = model.generate_content([prompt, img])
            return response.text.strip()
    except Exception as e:
        print(f"[!] Size Chart Error: {e}")
        return "Could not read chart"

if __name__ == "__main__":
    # Test if run directly
    import sys
    if len(sys.argv) > 1:
        print(extract_size_info(sys.argv[1]))
