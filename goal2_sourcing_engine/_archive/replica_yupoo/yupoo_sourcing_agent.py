import os
import json
import asyncio
import re
import base64
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
import aiohttp
from PIL import Image

# Directories
INPUT_SOURCING_DIR = os.path.join(os.getcwd(), "input_sourcing")
os.makedirs(INPUT_SOURCING_DIR, exist_ok=True)

# Trusted Sellers
SELLERS = {
    "cloyad": {
        "name": "Cloyad (Tophot)",
        "base_url": "https://tophotfashion.x.yupoo.com",
        "categories": {
            "bal": "https://tophotfashion.x.yupoo.com/categories/4644452",
            "prd": "https://tophotfashion.x.yupoo.com/categories/4642354",
            "hoodies": "https://tophotfashion.x.yupoo.com/categories/4642350",
            "shoes": "https://tophotfashion.x.yupoo.com/categories/4645167",
        }
    }
}

class YupooSourcingAgent:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.pw = None
        self.session = None
        self.validator = None
        self.gemini_keys = []
        self._current_key_idx = 0

    async def start(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.session = aiohttp.ClientSession()
        
        # Init Gemini Validator (using the dual keys from .env)
        from dotenv import load_dotenv
        import google.generativeai as genai
        load_dotenv(override=True)
        # GATHER ALL GEMINI KEYS DYNAMICALLY
        self.gemini_keys = [
            val for key, val in os.environ.items() 
            if key.startswith("GEMINI_API_KEY") and val.strip()
        ]
        # Filter out duplicates and keep order
        seen = set()
        self.gemini_keys = [k for k in self.gemini_keys if not (k in seen or seen.add(k))]
        
        # KEY AUDIT
        print(f"--- KEY AUDIT ---")
        print(f"Gemini Keys: {len(self.gemini_keys)}")
        print(f"NVIDIA Key: {'OK' if os.environ.get('NVIDIA_API_KEY') else 'MISSING'}")
        print(f"Groq Key: {'OK' if os.environ.get('GROQ_API_KEY') else 'MISSING'}")
        print(f"-----------------")
        
        # MODEL HIERARCHY (Optimized for verified account IDs)
        self.models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
        self._current_model_idx = 0
        self._current_key_idx = 0
        
        if self.gemini_keys:
            genai.configure(api_key=self.gemini_keys[self._current_key_idx])
            self.validator = genai.GenerativeModel(self.models[self._current_model_idx])
            print(f"[+] Quad-Key Engine Active | Primary: {self.models[self._current_model_idx]}", flush=True)

    def _rotate_key(self):
        import google.generativeai as genai
        # Try next key
        self._current_key_idx = (self._current_key_idx + 1) % len(self.gemini_keys)
        # If we cycled back to first key, try next model
        if self._current_key_idx == 0:
            self._current_model_idx = (self._current_model_idx + 1) % len(self.models)
            
        genai.configure(api_key=self.gemini_keys[self._current_key_idx])
        self.validator = genai.GenerativeModel(self.models[self._current_model_idx])
        print(f"      [OVERDRIVE] Swapping to Model: {self.models[self._current_model_idx]} | Key #{self._current_key_idx + 1}", flush=True)

    async def validate_image(self, image_path: str, title: str) -> tuple[bool, int]:
        # RESIZE FOR VISION PAYLOADS (Keep under 1MB)
        from io import BytesIO
        try:
            with Image.open(image_path) as img:
                img.thumbnail((1024, 1024))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                b64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"      [!] Resize Error: {e}")
            return False, 0

        print(f"      [DEBUG] Entering Universal Vision Chain...", flush=True)
        # PRIMARY: NVIDIA NIM (High Quota)
        nvidia_key = os.environ.get("NVIDIA_API_KEY")
        if nvidia_key:
            try:
                payload = {
                    "model": "meta/llama-3.2-11b-vision-instruct",
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": f"Strict Fashion QC: Rate '{title}' for 'Full Garment Visibility'. Rules: 1. Reject Humans (valid=false). 2. Reject Macro/Crops (valid=false). 3. Full Garment Flat Lay/Hanger (valid=true). Return JSON: {{\"valid\": bool, \"fullness_score\": 0-10, \"is_macro\": bool, \"reason\": str}}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                    ]}],
                    "response_format": {"type": "json_object"}
                }
                async with self.session.post("https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {nvidia_key}"}, json=payload) as resp:
                    raw_text = await resp.text()
                    if resp.status == 200:
                        data = json.loads(raw_text)
                        content = data["choices"][0]["message"]["content"]
                        # Surgical non-greedy JSON extraction
                        import re
                        matches = re.findall(r"\{.*?\}", content, re.DOTALL)
                        for m in matches:
                            try:
                                result = json.loads(m)
                                if "valid" in result and "fullness_score" in result:
                                    score = result.get("fullness_score", 0)
                                    is_valid = result.get("valid", False) and not result.get("is_macro", True)
                                    print(f"      [NVIDIA] Valid: {is_valid} | Score: {score}/10 | Reason: {result.get('reason')}", flush=True)
                                    return is_valid, score
                            except: continue
                    else:
                        print(f"      [!] NVIDIA Error {resp.status}: {raw_text}", flush=True)
            except Exception as e: print(f"      [!] NVIDIA Exception: {e} | Raw: {locals().get('raw_text', 'No Raw')}", flush=True)

        # SECONDARY: GROQ (Ultra Fast)
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            try:
                payload = {
                    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": f"Strict Fashion QC for '{title}'. RULES: 1. If human parts (hands/hair/skin) are visible -> score 0, valid false. 2. If macro/crop -> score 0, valid false. 3. If full garment flat lay/hanger -> score 10, valid true. JSON ONLY: {{\"valid\": bool, \"fullness_score\": int}}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                    ]}]
                }
                async with self.session.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}"}, json=payload) as resp:
                    raw_text = await resp.text()
                    if resp.status == 200:
                        data = json.loads(raw_text)
                        content = data["choices"][0]["message"]["content"]
                        import re
                        matches = re.findall(r"\{.*?\}", content, re.DOTALL)
                        for m in matches:
                            try:
                                result = json.loads(m)
                                if "valid" in result:
                                    print(f"      [GROQ] Valid: {result.get('valid')} | Score: {result.get('fullness_score')}/10", flush=True)
                                    return result.get("valid", False), result.get("fullness_score", 0)
                            except: continue
                    else:
                        print(f"      [!] Groq Error {resp.status}: {raw_text}", flush=True)
            except Exception as e: print(f"      [!] Groq Exception: {e} | Raw: {locals().get('raw_text', 'No Raw')}", flush=True)

        # BACKUP: Gemini (Quota Limited)
        if not self.validator: return True, 10
        try:
            with Image.open(image_path) as img:
                img.load()
            
            prompt = f"""You are a strict fashion quality control AI. 
Product: {title}

TASK: Rate this image for 'Full Garment Visibility'.

RULES:
1. HUMAN CHECK: Is there ANY part of a human visible? (hands, legs, neck, hair, fingers, skin)? 
   -> IF YES (even a tiny bit): valid=false. NO EXCEPTIONS.
2. CROP CHECK: Is this a 'Macro' or 'Detail' shot (e.g. just a zipper, a label, or a pocket)? 
   -> IF YES: valid=false.
3. FULLNESS: Does this show the ENTIRE garment from top to bottom? (Flat Lay or Hanger ONLY)
   -> IF YES (and no human): valid=true.

Return JSON ONLY: 
{{
    "valid": true/false, 
    "fullness_score": 0-10, 
    "is_macro": true/false,
    "reason": "..."
}}
"""
            
            response = None
            for _ in range(len(self.gemini_keys)):
                try:
                    with Image.open(image_path) as img:
                        response = self.validator.generate_content([prompt, img])
                    break
                except Exception as e:
                    print(f"      [!] Gemini Error: {e}")
                    if "429" in str(e): self._rotate_key()
                    else: return False, 0 # Skip if non-retryable
            
            if response:
                match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                    is_valid = result.get("valid", False) and not result.get("is_macro", True)
                    score = result.get("fullness_score", 0)
                    print(f"      [GEMINI] Valid: {is_valid} | Fullness: {score}/10 | Reason: {result.get('reason')}", flush=True)
                    return is_valid, score
            
            return False, 0
        except Exception as e:
            print(f"      [!] Validation Error: {e}", flush=True)
            return False, 0

    async def scrape_category(self, seller_id: str, category_id: str, limit: int = 1):
        seller = SELLERS.get(seller_id)
        url = seller["categories"].get(category_id)
        
        self.page = await self.context.new_page()
        print(f"   [*] Processing: {url.split('/')[-1]}...")
        # Use domcontentloaded for faster entry, with a longer timeout
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        album_els = await self.page.query_selector_all(".album__main")
        processed_count = 0
        
        for album_el in album_els[:limit]:
            title_el = await album_el.query_selector(".album__name")
            title = await title_el.inner_text() if title_el else "Unknown"
            href = await album_el.get_attribute("href")
            
            data = {"title": title, "url": seller["base_url"] + href}
            
            # Go into album
            album_page = await self.context.new_page()
            await album_page.goto(data['url'], wait_until="domcontentloaded", timeout=60000)
            
            # Scroll a bit to trigger lazy loads
            await album_page.evaluate("window.scrollTo(0, 500)")
            await asyncio.sleep(1)

            img_els = await album_page.query_selector_all(".showalbum__children img")
            print(f"      [Found {len(img_els)} images in album. Searching for Hero Shot...]")
            
            best_img = None
            best_score = -1
            best_path = None
            
            # Scan top 15 images to find the best Hero Shot
            for i, img_el in enumerate(img_els[:15]):
                try:
                    await img_el.scroll_into_view_if_needed()
                    
                    # Wait for image to actually load its pixels
                    await album_page.wait_for_function(
                        "(img) => img.complete && img.naturalWidth > 0",
                        arg=img_el,
                        timeout=10000
                    )
                    
                    ts = int(datetime.now().timestamp() * 100)
                    temp_filename = f"temp_{category_id}_{ts}_{i}.png"
                    temp_path = os.path.join(INPUT_SOURCING_DIR, temp_filename)
                    
                    await img_el.screenshot(path=temp_path)
                    
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 10000:
                        # Heartbeat to avoid RPM limits
                        await asyncio.sleep(2)
                        is_valid, score = await self.validate_image(temp_path, title)
                        if is_valid and score > best_score:
                            # New best Hero Shot
                            if best_path: os.remove(best_path)
                            best_score = score
                            best_path = temp_path
                            print(f"      [NEW BEST] Fullness Score: {score}/10")
                            # If we found a perfect 10, we can stop early
                            if score >= 10: break
                        else:
                            os.remove(temp_path)
                except Exception as e:
                    print(f"      [!] Capture Error: {e}")

            if best_path:
                final_filename = f"male_{category_id}_{int(datetime.now().timestamp())}.png"
                final_path = os.path.join(INPUT_SOURCING_DIR, final_filename)
                os.rename(best_path, final_path)
                print(f"   [OK] SAVED HERO SHOT: {final_filename} (Score: {best_score}/10)")
                processed_count += 1
            
            await album_page.close()
            if processed_count >= limit: break

        await self.page.close()

    async def close(self):
        if self.session:
            await self.session.close()
        await self.browser.close()
        await self.pw.stop()

async def main():
    agent = YupooSourcingAgent(headless=True)
    await agent.start()
    
    # Scrape BAL (Balenciaga) and PRD (Prada)
    await agent.scrape_category("cloyad", "bal", limit=1)
    await agent.scrape_category("cloyad", "prd", limit=1)
    
    await agent.close()

if __name__ == "__main__":
    asyncio.run(main())
