import os
import io
import json
import base64
import requests
import numpy as np
from PIL import Image, ImageFilter
from dotenv import load_dotenv
from litellm_router import shared_router
from utils import safe_print

# Override print to ensure safe console output on Windows (cp1252)
print = safe_print

# Load .env explicitly if needed
load_dotenv()

class VisionEvaluator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        
        if not self.api_key:
            print("⚠️  VisionEvaluator: GEMINI_API_KEY not found in environment! Falling back to LiteLLM router.")

    def _encode_image(self, image_path: str) -> dict:
        """Compress and encode image for the API to save parsing time and payload size. (Legacy/External compatibility)"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB to avoid alpha channel issues with JPEG
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if it's huge — we don't need 4K for anomaly detection
                img.thumbnail((1024, 1024))
                
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                return {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": base64_data
                    }
                }
        except Exception as e:
            print(f"VisionEvaluator error encoding image {image_path}: {e}")
            return None

    def _encode_image_base64(self, image_path: str) -> str:
        """Compress and encode image as base64 string for LiteLLM format."""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.thumbnail((1024, 1024))
                
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"VisionEvaluator error encoding base64 image {image_path}: {e}")
            return None

    def evaluate_image(self, image_path: str) -> dict:
        """
        Evaluates a single fashion generation for typical AI anomalies using 6 numerical criteria + CoT.
        Returns: { "passed": bool, "reason": str, ... }
        """
        print(f"👁️  Vision analyzing (LiteLLM): {os.path.basename(image_path)}...")
        
        base64_data = self._encode_image_base64(image_path)
        if not base64_data:
            return {"passed": False, "reason": "File read/corrupt error"}

        prompt = """
        You are an expert AI quality control system for a premium fashion agency (OBSCURA).
        Analyze this generated fashion model photo and score it on the following 6 criteria from 1 to 10 (where 10 is flawless editorial quality and 1 is catastrophic failure):

        1. Anatomical Correctness: Check for extra fingers, mangled hands, warped limbs, missing parts, or multiple heads/people (must score < 5 if any anatomical anomalies exist).
        2. Garment Fidelity: Check if the clothing looks realistic, structurally sound, cleanly draped, and free of chaotic AI warpings.
        3. Lighting Quality: Check if lighting is consistent, editorial, and realistic (not flat, overexposed, or unnaturally glowing).
        4. Background Complexity: Check for high-end backdrop or environment, with realistic shadows and without blending/bleeding into the subject.
        5. Skin Realism: Check if skin texture has realistic pores/imperfections rather than uncanny-valley plastic/doll-like smoothness.
        6. Overall Editorial: Check if the shot looks like a high-end luxury campaign (Vogue, Balenciaga tier).

        First, write out your detailed step-by-step reasoning (Chain of Thought) for each criteria.
        Then, calculate the scores and the average.
        The generation passes ONLY if the average score is 6.0 or higher, AND Anatomical Correctness is at least 5.

        Return ONLY a JSON object in this exact format:
        {
          "reasoning": "Your detailed step-by-step chain of thought analyzing the image...",
          "anatomical_correctness": 8,
          "garment_fidelity": 7,
          "lighting_quality": 9,
          "background_complexity": 8,
          "skin_realism": 6,
          "overall_editorial": 7,
          "average_score": 7.5,
          "passed": true
        }
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_data}"
                        }
                    }
                ]
            }
        ]

        try:
            response = shared_router.get_chat_completion_sync(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content.strip()
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            try:
                result = json.loads(response_text, strict=False)
            except Exception:
                import re
                result = {}
                # Regex score extractions
                for metric in ["anatomical_correctness", "garment_fidelity", "lighting_quality", 
                               "background_complexity", "skin_realism", "overall_editorial"]:
                    m = re.search(rf'"{metric}"\s*:\s*(\d+)', response_text)
                    if m:
                        result[metric] = int(m.group(1))
                        
                avg_m = re.search(r'"average_score"\s*:\s*([0-9.]+)', response_text)
                if avg_m:
                    result["average_score"] = float(avg_m.group(1))
                elif result:
                    scores = [v for k, v in result.items() if isinstance(v, (int, float))]
                    result["average_score"] = round(sum(scores) / len(scores), 2)
                    
                pass_m = re.search(r'"passed"\s*:\s*(true|false)', response_text, re.IGNORECASE)
                if pass_m:
                    result["passed"] = pass_m.group(1).lower() == "true"
                else:
                    result["passed"] = result.get("average_score", 0) >= 6.0 and result.get("anatomical_correctness", 10) >= 5
                    
                reason_m = re.search(r'"reasoning"\s*:\s*"([^"]+)"', response_text)
                result["reasoning"] = reason_m.group(1) if reason_m else response_text[:200]



            
            # Extract basic passed / reason for backwards compatibility
            passed = result.get("passed", False)
            avg_score = result.get("average_score", 0.0)
            reason = result.get("reasoning", "")
            
            if not passed:
                print(f"   ❌ Vision REJECTED (Score: {avg_score:.2f}): {reason[:120]}...")
                result["reason"] = reason
                return result
            
            print(f"   ✅ Vision PASSED (Score: {avg_score:.2f})")
            result["reason"] = ""
            return result
            
        except Exception as e:
            print(f"⚠️  Vision API error via LiteLLM: {e}")
            # If the API fails, we tentatively pass rather than discarding potentially good assets
            return {"passed": True, "reason": f"API Failure Fallback: {e}", "average_score": 7.0}

    def is_valid_product_image(self, image_path: str) -> dict:
        """
        Uses Gemini Vision via LiteLLM to classify if a scraped image is a clean product photo
        or a rejected type (sizing chart, grid/collage, etc).
        """
        base64_data = self._encode_image_base64(image_path)
        if not base64_data:
            return {"passed": False, "reason": "File read/corrupt error"}

        prompt = """
        You are a quality control AI for an e-commerce clothing scraper.
        Examine this image. We need to filter out garbage images to ensure the AI generator has a clean reference.
        
        REJECT the image if it is:
        1. A sizing chart, measurement guide, or contains large tables of text/numbers.
        2. A grid or collage of MULTIPLE different items.
        3. A close-up of a price tag, neck label, wash tag, or receipt, without showing the full garment.
        4. The main garment is mostly cropped out, obscured, or not clearly visible.
        
        ACCEPT the image ONLY if it features a single clear, unobstructed clothing item or outfit.
        
        Answer ONLY with a JSON object in this exact format:
        {"passed": true|false, "reason": "brief explanation"}
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_data}"
                        }
                    }
                ]
            }
        ]

        try:
            response = shared_router.get_chat_completion_sync(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            
            result = json.loads(response_text)
            return {"passed": result.get("passed", False), "reason": result.get("reason", "Unknown")}
            
        except Exception as e:
            print(f"⚠️  Vision API error in is_valid_product_image: {e}")
            return {"passed": False, "reason": f"API/Parse Failure: {e}"}

    def _delete_bad_image(self, file_path: str):
        try:
            os.remove(file_path)
            print(f"🗑  Deleted failed generation: {os.path.basename(file_path)}")
        except OSError as e:
            print(f"⚠️  Failed to delete file {file_path}: {e}")

    def quick_quality_check(self, image_path: str) -> dict:
        """
        FREE instant pre-filter using PIL + numpy.
        Checks blur, brightness, and resolution BEFORE burning a Gemini API call.
        Returns: { "passed": bool, "reason": str }
        """
        try:
            with Image.open(image_path) as img:
                w, h = img.size

                # 1. Resolution check — below 400px is almost always junk
                if w < 400 or h < 400:
                    return {"passed": False, "reason": f"Too small ({w}x{h})"}

                # Convert to grayscale for analysis
                gray = img.convert("L")

                # 2. Blur detection — edge variance (Laplacian-like)
                edges = gray.filter(ImageFilter.FIND_EDGES)
                edge_arr = np.array(edges, dtype=np.float64)
                blur_score = edge_arr.var()
                if blur_score < 50:
                    return {"passed": False, "reason": f"Too blurry (score: {blur_score:.0f})"}

                # 3. Brightness check — mean pixel value
                pixels = np.array(gray, dtype=np.float64)
                mean_brightness = pixels.mean()
                if mean_brightness < 30:
                    return {"passed": False, "reason": f"Too dark (brightness: {mean_brightness:.0f})"}
                if mean_brightness > 245:
                    return {"passed": False, "reason": f"Overexposed (brightness: {mean_brightness:.0f})"}

            return {"passed": True, "reason": ""}
        except Exception as e:
            return {"passed": False, "reason": f"File error: {e}"}

    def filter_batch(self, downloaded_files: list) -> list:
        """
        Evaluates a list of image paths and DELETES the ones that fail.
        Uses FREE instant pre-filter first, then Gemini AI for borderline cases.
        Returns the list of ONLY the safe, passed image paths.
        """
        passed_files = []
        skipped_by_prefilter = 0
        for file_path in downloaded_files:
            if not os.path.exists(file_path):
                continue
            size_kb = os.path.getsize(file_path) / 1024
            if size_kb < 50:
                print(f"   🗑  Corrupted file detected ({size_kb:.1f}KB). Deleting...")
                self._delete_bad_image(file_path)
                continue

            quick = self.quick_quality_check(file_path)
            if not quick["passed"]:
                print(f"   ⚡ Pre-filter REJECTED: {quick['reason']}")
                self._delete_bad_image(file_path)
                skipped_by_prefilter += 1
                continue

            result = self.evaluate_image(file_path)
            if result["passed"]:
                passed_files.append(file_path)
            else:
                self._delete_bad_image(file_path)

        if skipped_by_prefilter:
            print(f"   ⚡ Pre-filter saved {skipped_by_prefilter} Gemini API calls")
        return passed_files

    def evaluate_vton_match(self, original_product_path: str, generated_image_path: str) -> dict:
        """
        Uses Semantic Vision via LiteLLM to compare the supplier product with the generated try-on result.
        Returns { "passed": True/False, "reason": str }
        """
        print(f"👁  Semantic checking VTON match via LiteLLM...")
        
        orig_base64 = self._encode_image_base64(original_product_path)
        gen_base64 = self._encode_image_base64(generated_image_path)
        
        if not orig_base64 or not gen_base64:
            return {"passed": False, "reason": "File read/corrupt error"}

        prompt = """
        You are an expert fashion semantic evaluator.
        I am giving you two images.
        Image 1: A raw product photo from a supplier.
        Image 2: An AI-generated Virtual Try-On of a model wearing that product.
        
        Does the clothing item worn by the model in Image 2 fundamentally MATCH the structure, general pattern, and style of the real item in Image 1?
        If the AI Hallucinated something completely different (e.g. turned a T-shirt into a hoodie, or changed a floral pattern to solid black), you MUST reject it.
        Minor lighting and fold differences are okay.
        
        Answer ONLY with a JSON object in this exact format:
        {"passed": true|false, "reason": "brief explanation"}
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{orig_base64}"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{gen_base64}"
                        }
                    }
                ]
            }
        ]

        try:
            response = shared_router.get_chat_completion_sync(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content.strip()
            
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
                
            result = json.loads(response_text)
            
            if not result.get("passed", False):
                print(f"   ❌ Semantic Mismatch: {result.get('reason', 'Unknown failure')}")
                return {"passed": False, "reason": result.get("reason", "Unknown")}
            
            print("   ✅ Semantic Match PASSED")
            return {"passed": True, "reason": ""}
            
        except Exception as e:
            print(f"⚠️  Vision API error in evaluate_vton_match: {e}")
            return {"passed": True, "reason": f"API Failure Fallback: {e}"}
