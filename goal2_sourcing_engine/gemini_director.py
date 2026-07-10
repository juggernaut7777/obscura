"""
Gemini Fashion Director — The Multimodal Intelligence Layer
============================================================
Uses LiteLLM Router for multimodal analysis, designing complete
editorial shoots, and validating generated results.
"""
import os
import json
import re
import io
import base64
from PIL import Image
from dotenv import load_dotenv
from litellm_router import shared_router

load_dotenv()

# ─── SHOOT TYPES ───
SHOOT_TYPES = [
    {
        "name": "front_hero",
        "angle": "Front-facing hero shot, model looking directly at camera",
        "crop": "Full body, head to toe, 3:4 aspect"
    },
    {
        "name": "back_detail",
        "angle": "Back view showing rear design/branding details of the garment",
        "crop": "Full body from behind, slight over-shoulder glance, 3:4 aspect"
    },
    {
        "name": "lifestyle_action",
        "angle": "Dynamic lifestyle shot, model walking/moving confidently in the environment",
        "crop": "Full body with environment context, 3:4 aspect"
    },
    {
        "name": "detail_closeup",
        "angle": "Close-up detail shot focusing on fabric texture, stitching, logo, or unique design element",
        "crop": "Tight crop on the product detail, 1:1 aspect"
    },
]


class GeminiDirector:
    """
    The Multimodal Fashion Director.
    Uses LiteLLM router to visually 'think' about fashion logic.
    """

    def __init__(self):
        # Load the Manifesto for context
        manifesto_path = os.path.join(os.getcwd(), "FASHION_MANIFESTO.md")
        self.manifesto = ""
        if os.path.exists(manifesto_path):
            with open(manifesto_path, "r", encoding="utf-8") as f:
                self.manifesto = f.read()
        
        print("[Director] Gemini Director initialized using LiteLLM Router.")

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from response text."""
        try:
            # Try direct parse first
            return json.loads(text)
        except:
            pass
        # Try to find JSON block in markdown
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        # Try to find any {...} block
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        return {"raw": text}

    def _encode_image_base64(self, image_path: str) -> str:
        """Compress and encode image as base64 string for LiteLLM."""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to reasonable dimension to keep token usage optimal
                img.thumbnail((1024, 1024))
                
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"[Director] Error encoding base64 image {image_path}: {e}")
            return None

    async def design_shoot(self, product_img_path: str, model_img_path: str) -> dict:
        """
        Visually analyzes the product and model to design a complete editorial shoot.
        Returns a structured plan with prompts for each shot angle.
        """
        try:
            p_b64 = self._encode_image_base64(product_img_path)
            m_b64 = self._encode_image_base64(model_img_path)

            if not p_b64 or not m_b64:
                return None

            prompt = """You are the Creative Director for a high-end luxury fashion brand (OBSCURA).
            
Look at these two images:
IMAGE 1: The product we are selling (source garment).
IMAGE 2: The model who will wear it.

Design a complete, high-budget Vogue editorial shoot for this product on this model.

Use Chain-of-Thought reasoning:
1. Analyze the garment in IMAGE 1 (silhouette, fabric, design, style).
2. Analyze the model in IMAGE 2 (gender, skin tone, hair, features).
3. Formulate a luxury outfit combination around the product (do NOT keep the model's base reference clothes).
4. Select an expensive-looking location (e.g. brutalist concrete stairwell, private jet tarmac, luxury mansion garden). NO plain sky/clouds.
5. Plan the lighting (chiaroscuro, golden hour rim, overcast London flat lighting).
6. Draft highly descriptive prompts for 4 campaign shots:
   - Front Hero: Full body front shot.
   - Back Detail: Over-the-shoulder view showing back graphics/design.
   - Lifestyle: Dynamic action snap in context.
   - Detail Closeup: Close-up of fabric, stitching, or hardware.

Here is a few-shot example of the output structure:
{
    "reasoning": "Step-by-step styling logic: The black cargo pants have a heavy ripstop texture, so they pair perfectly with chunky boots (Reference 4) and a cropped washed tee (Reference 3) to create a rugged gorpcore look for the female model...",
    "gender": "female",
    "product_type": "bottom",
    "product_description": "washed black ripstop utility cargo pants",
    "styling_plan": "heavy black technical boots, washed grey cropped cotton tee, metal chain belt",
    "location": "A rain-slicked brutalist concrete courtyard in London",
    "lighting": "sodium-vapor street lamp rim lighting creating sharp teal-orange contrast",
    "front_prompt": "Using the exact person from the first reference image, generate a hyperrealistic front hero shot of her wearing these exact cargo pants from the second reference image... Shot on Hasselblad H6D-100c, 85mm portrait lens, raw photo, visible skin pores.",
    "back_prompt": "Using the exact person from the first reference image, generate a hyperrealistic back-view shot showing the rear pockets and custom strap details of these exact cargo pants... Shot on Hasselblad H6D-100c, 85mm portrait lens, raw photo.",
    "lifestyle_prompt": "Using the exact person from the first reference image, generate a hyperrealistic lifestyle photo of her walking down a wet urban concrete courtyard... Shot on Sony A1, 35mm lens.",
    "detail_prompt": "Close-up detail photograph of these exact cargo pants... Focus on ripstop fabric weave and metal buckle. Shot on 100mm macro lens."
}

Now, execute this for the provided images. Return ONLY a JSON object matching this schema.
"""

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{p_b64}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{m_b64}"
                            }
                        }
                    ]
                }
            ]

            response = shared_router.get_chat_completion_sync(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            result = self._extract_json(response_text)
            result["_raw"] = response_text
            return result

        except Exception as e:
            print(f"[!] Gemini Director Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _safe_load_image(self, img_path: str):
        """Safely loads an image, converts to RGB, and strips problematic metadata."""
        img = Image.open(img_path).convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return Image.open(buffer)

    async def design_full_fit(self, product_images: list, model_face_path: str, model_body_path: str) -> dict:
        """
        Smart Merge: Designs an outfit using dual-model references (Ref 1 & 2)
        and product references (Ref 3+).
        """
        try:
            face_b64 = self._encode_image_base64(model_face_path)
            body_b64 = self._encode_image_base64(model_body_path)

            if not face_b64 or not body_b64:
                return None

            prompt = f"""You are a technical Fashion Director.
You have {len(product_images)} products and a 2-part model sheet.

THE REFERENCE SYSTEM:
- Reference 1: Official Model Face.
- Reference 2: Official Model Body.
- Reference 3, 4, 5, etc: The specific products you select (in order).

TASK:
1. SELECT 2 items: 1 Top and 1 Bottom/Shoe for a logical outfit.
2. Write a technical prompt. Use 'Reference 1 and 2' for the model.
3. The first item you select is 'Reference 3', the second is 'Reference 4'.
4. CRITICAL: Ensure the `selected_indices` array matches the order of Reference 3, 4, etc.
5. Example: If you pick products at index 0 and 4, `selected_indices` must be [0, 4].

Return a JSON object:
{{
    "fit_name": "Editorial name",
    "selected_indices": [index_of_ref3, index_of_ref4],
    "full_fit_prompt": "Technical prompt. 'Put the [Item 1] from Reference 3 and [Item 2] from Reference 4 on the model from Reference 1 and 2...'",
    "flat_lay_prompt": "...",
    "location": "...",
    "styling_notes": "..."
}}

RULES:
- Always use 'Reference 1 and 2' for the model.
- No layering junk—keep the outfit realistic and clean.
- Cinematic lighting, 8K, raw photo aesthetic. No clouds.
"""
            
            content_parts = [{"type": "text", "text": prompt}]
            
            # Add each product with its index label
            for idx, img_path in enumerate(product_images):
                b64 = self._encode_image_base64(img_path)
                if b64:
                    content_parts.append({"type": "text", "text": f"Product Index {idx}:"})
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}"
                        }
                    })
            
            content_parts.append({"type": "text", "text": "Reference 1 (Model Face):"})
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{face_b64}"
                }
            })
            
            content_parts.append({"type": "text", "text": "Reference 2 (Model Body):"})
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{body_b64}"
                }
            })
            
            messages = [
                {
                    "role": "user",
                    "content": content_parts
                }
            ]

            response = shared_router.get_chat_completion_sync(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            return self._extract_json(response_text)

        except Exception as e:
            print(f"[!] Gemini Full Fit Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def validate_generation(self, product_img_path: str, generated_img_path: str) -> str:
        """
        Post-generation QC: Checks if the generated image matches the product and manifesto.
        Returns 'APPROVED' or 'REJECTED: reason'.
        """
        try:
            p_b64 = self._encode_image_base64(product_img_path)
            g_b64 = self._encode_image_base64(generated_img_path)

            if not p_b64 or not g_b64:
                return "ERROR: File read error"

            prompt = """You are a Quality Control Director for a luxury fashion brand.
Compare IMAGE 1 (the source product) with IMAGE 2 (the AI-generated result).

Evaluate the generated photo on the following 4 criteria from 1 to 10 (where 10 is flawless and 1 is total failure):
1. Product Fidelity: Does the generated garment in IMAGE 2 match the source product in IMAGE 1 exactly in terms of colors, patterns, graphics, and design? (Required: >= 7)
2. Background Quality: Is the background environment sharp, realistic, and premium? (Required: >= 6)
3. Anatomical Realism: Are hands, fingers, limbs, eyes, and skin texture hyperrealistic (no extra fingers, no plastic-doll skin)? (Required: >= 8)
4. Overall Aesthetic: Does the shot look premium, editorial-ready, and luxury-tier? (Required: >= 6)

First, write out your reasoning for each score.
If all criteria meet or exceed the required thresholds, return a JSON object:
{"passed": true, "reason": ""}

If any criteria fail, return a JSON object with passed=false and detail the scores and weaknesses in the reason field:
{"passed": false, "reason": "REJECTED: [detailed reason containing the scores and weaknesses]"}
"""
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{p_b64}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{g_b64}"
                            }
                        }
                    ]
                }
            ]

            response = shared_router.get_chat_completion_sync(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            result = self._extract_json(response_text)
            
            if result.get("passed", False):
                return "APPROVED"
            else:
                return result.get("reason", "REJECTED: Quality threshold not met")

        except Exception as e:
            print(f"[!] Gemini Validator Error: {e}")
            return f"ERROR: {e}"
