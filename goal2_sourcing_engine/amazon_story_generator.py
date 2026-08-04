import os
import sys
import json
import time
import asyncio
from typing import List, Dict, Optional

from litellm_router import LiteLLMRouter
from voice_generator import VoiceGenerator

def safe_print(msg: str):
    """Safely print messages on Windows to avoid UnicodeEncodeErrors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode('utf-8', errors='replace').decode(sys.stdout.encoding, errors='replace'))
        except Exception:
            print("[Print Error] Unable to encode output print message.")

PRODUCT_PROFILES = {
    "faraday_bag": {
        "name": "Faraday Signal Blocking Bag",
        "description": "A military-grade mesh bag that blocks all wireless signals (Cellular, GPS, WiFi, RFID, Bluetooth) to prevent remote tracking, hacking, and car key fob signal relay attacks.",
        "threat": "Section 702 warrant-less location tracking, IMSI catchers (stingrays) intercepting calls, and key fob cloning where thieves steal cars by copying key signals from outside the house.",
        "amazon_link": "https://amzn.to/3exampleFaraday"
    },
    "water_filter": {
        "name": "Portable Survival Water Purifier",
        "description": "A compact survival water filter straw that filters out 99.999% of parasites, microplastics, and bacteria from dirty streams, puddles, or contaminated water supplies.",
        "threat": "Natural disasters, cyberattacks on municipal water treatment grids, and biological contamination that leaves entire cities without clean drinking water.",
        "amazon_link": "https://amzn.to/3exampleWater"
    },
    "signal_detector": {
        "name": "Hidden Spy Camera & RF Detector",
        "description": "An infrared lens finder and radio-frequency signal sweeper that locates hidden pinhole cameras, GPS trackers on vehicles, and active audio listening bugs.",
        "threat": "Hidden spy cameras in hotels and rental properties, private investigators installing magnetic trackers under cars, and corporate espionage listening devices.",
        "amazon_link": "https://amzn.to/3exampleDetector"
    },
    "solar_radio": {
        "name": "Emergency Solar Hand-Crank Radio & Flashlight",
        "description": "An emergency broadcast receiver powered by solar panels, a manual hand-crank generator, or batteries, equipped with an NOAA weather alert channel, power bank, and SOS alarm.",
        "threat": "Severe storms, space weather/solar storms disabling satellite communication, and complete power grid blackouts where standard cell towers go completely dark.",
        "amazon_link": "https://amzn.to/3exampleRadio"
    }
}

class AmazonStoryGenerator:
    def __init__(self):
        self.router = LiteLLMRouter()
        self.voice_gen = VoiceGenerator()
        self.output_root = os.path.join(os.getcwd(), "output_ugc")
        os.makedirs(self.output_root, exist_ok=True)

    async def generate_package(self, product_key: str, custom_product: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Generates the full story script, image prompts, SEO metadata, and TTS narration audio."""
        if custom_product:
            profile = custom_product
            p_name = profile.get("name", "Survival Gadget")
        else:
            profile = PRODUCT_PROFILES.get(product_key)
            if not profile:
                safe_print(f"[!] Invalid product key: {product_key}. Available: {list(PRODUCT_PROFILES.keys())}")
                return None
            p_name = profile["name"]

        safe_print(f"\n{'='*60}")
        safe_print(f"  AMAZON AFFILIATE STORY GENERATOR — {p_name.upper()}")
        safe_print(f"{'='*60}\n")

        # 1. Ask Gemini to write script & prompts
        prompt = f"""
You are an expert copywriter and documentary scriptwriter for "The Untold Files." 
We are creating a viral 9:16 vertical video (2:30 to 3:00 duration) for TikTok and Reels to drive Amazon affiliate sales.

Product Profile:
- Name: {profile['name']}
- Threat/Context: {profile['threat']}
- Description: {profile['description']}

Generate the script in Markdown format exactly as follows:

# Title: [Curiosity title under 60 characters]

## Narration
[Write a full, continuous voiceover script (around 200 words) with no scene labels, just clean narration text. Limit to 5 paragraphs.]

## Scene Breakdown
### Scene 1
Voiceover: [narration for scene 1]
Image Prompt: [cinematic prompt for image generation: 9:16 aspect ratio, dark noir cinematic realism, volumetric fog, hyper-detailed photography]

### Scene 2
Voiceover: [narration for scene 2]
Image Prompt: [cinematic prompt for image generation]

[Generate exactly 5 scenes in this format]

## SEO Description
[Curiosity-driven social media caption with 5-8 relevant hashtags]

## Tags
[Comma-separated list of tags]
"""

        messages = [{"role": "user", "content": prompt}]
        safe_print("[*] LLM: Generating script and visual prompts via LiteLLM...")
        
        try:
            response = await self.router.get_chat_completion(
                messages=messages,
                primary_model="gemini-flash",
                temperature=0.75,
                max_tokens=4096
            )
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Custom Markdown Parser
            title = f"{p_name} Untold Story"
            narration_full = ""
            scenes = []
            seo_description = ""
            tags = []
            
            current_section = ""
            current_scene = {}
            
            for line in content.split("\n"):
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Identify sections
                if line_stripped.startswith("# Title:") or line_stripped.startswith("# TITLE:"):
                    title = line_stripped.split(":", 1)[1].strip()
                    current_section = "title"
                    continue
                elif line_stripped.startswith("## Narration") or line_stripped.startswith("## NARRATION"):
                    current_section = "narration"
                    continue
                elif line_stripped.startswith("## Scene Breakdown") or line_stripped.startswith("## SCENE BREAKDOWN"):
                    current_section = "scenes"
                    continue
                elif line_stripped.startswith("## SEO Description") or line_stripped.startswith("## SEO DESCRIPTION"):
                    current_section = "seo"
                    continue
                elif line_stripped.startswith("## Tags") or line_stripped.startswith("## TAGS"):
                    current_section = "tags"
                    continue
                
                # Parse lines based on current section
                if current_section == "narration":
                    narration_full += line_stripped + " "
                elif current_section == "seo":
                    seo_description += line_stripped + "\n"
                elif current_section == "tags":
                    parts = line_stripped.split(",")
                    tags.extend([p.replace('"', '').replace("'", "").strip() for p in parts if p.strip()])
                elif current_section == "scenes":
                    if line_stripped.startswith("### Scene") or line_stripped.startswith("### SCENE"):
                        if current_scene:
                            scenes.append(current_scene)
                        current_scene = {"voiceover": "", "image_prompt": ""}
                    elif "Voiceover:" in line_stripped or "voiceover:" in line_stripped:
                        txt = line_stripped.split("Voiceover:", 1 if "Voiceover:" in line_stripped else 0)[-1].strip()
                        current_scene["voiceover"] = txt.lstrip(" -*")
                    elif "Image Prompt:" in line_stripped or "image_prompt:" in line_stripped:
                        txt = line_stripped.split("Image Prompt:", 1 if "Image Prompt:" in line_stripped else 0)[-1].strip()
                        current_scene["image_prompt"] = txt.lstrip(" -*")

            if current_scene:
                scenes.append(current_scene)
                
            data = {
                "title": title,
                "narration_full": narration_full.strip(),
                "scenes": scenes,
                "seo_description": seo_description.strip(),
                "tags": tags
            }
            
        except Exception as e:
            safe_print(f"[!] LLM: Script generation failed: {e}")
            return None

        # Create output directory
        timestamp = int(time.time())
        folder_name = f"affiliate_{product_key}_{timestamp}"
        out_dir = os.path.join(self.output_root, folder_name)
        os.makedirs(out_dir, exist_ok=True)

        # 2. Write Script & Prompts files
        script_path = os.path.join(out_dir, "script.md")
        prompts_path = os.path.join(out_dir, "image_prompts.txt")
        posting_guide_path = os.path.join(out_dir, "posting_guide.md")
        
        # Save script.md
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(f"# The Untold Files - Episode: {data.get('title')}\n\n")
            f.write(f"**Target Product:** {p_name}\n")
            f.write(f"**Affiliate Link:** {profile['amazon_link']}\n\n")
            f.write("## 📝 Voiceover Narration\n\n")
            f.write(data.get("narration_full", "") + "\n\n")
            f.write("## 🎬 Scene Breakdown\n\n")
            for i, scene in enumerate(data.get("scenes", [])):
                f.write(f"### Scene {i+1}\n")
                f.write(f"* **Voiceover:** {scene.get('voiceover')}\n")
                f.write(f"* **Image Prompt:** {scene.get('image_prompt')}\n\n")
                
        # Save image_prompts.txt
        with open(prompts_path, "w", encoding="utf-8") as f:
            for scene in data.get("scenes", []):
                f.write(scene.get("image_prompt") + "\n\n")

        # Save posting_guide.md
        with open(posting_guide_path, "w", encoding="utf-8") as f:
            f.write(f"# Social Media Posting Guide\n\n")
            f.write(f"**Video Title:** {data.get('title')}\n\n")
            f.write(f"**Description/Caption:**\n{data.get('seo_description')}\n\n")
            f.write(f"**Pinned Comment / Call-To-Action Link:**\n")
            f.write(f"👉 Secure yours here: {profile['amazon_link']} (Safe link in bio/comments)\n\n")
            f.write(f"**Recommended Tags:** {', '.join(data.get('tags', []))}\n")

        safe_print(f"[OK] Saved text assets to: {out_dir}")

        # 3. Generate Audio Narration File
        safe_print("[*] TTS: Synthesizing full narration voiceover...")
        audio_out_path = os.path.join(out_dir, "narration.mp3")
        audio_path = await self.voice_gen.generate_audio(
            text=data.get("narration_full", "Obscura"),
            voice_name="default",
            output_path=audio_out_path
        )
        
        if audio_path and os.path.exists(audio_path):
            safe_print(f"[OK] TTS: Audio voiceover saved to: {audio_path}")
        else:
            safe_print("[!] TTS: Failed to generate audio voiceover narration.")

        safe_print(f"\n📂 Completed package is located in: {out_dir}\n")
        return out_dir

async def test_generator():
    gen = AmazonStoryGenerator()
    await gen.generate_package("faraday_bag")

if __name__ == "__main__":
    asyncio.run(test_generator())
    # Force exit to prevent LiteLLM background thread hangs
    os._exit(0)
