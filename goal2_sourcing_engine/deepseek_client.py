"""
DeepSeek AI Client
==================
Since you don't have ChatGPT or Claude API keys, we use DeepSeek V3/R1.
DeepSeek provides state-of-the-art performance (GPT-4 level) but is incredibly cheap
and gives massive free trial credits when you sign up at platform.deepseek.com.

This client uses the standard OpenAI python package but points to DeepSeek's servers.
"""

import os
from openai import OpenAI

class DeepSeekClient:
    def __init__(self, api_key: str = None):
        # Fallback to env var if not provided
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        
        if not self.api_key:
            print("⚠️ Warning: DEEPSEEK_API_KEY not found in environment.")
            print("Get one for free at: https://platform.deepseek.com/")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )

    def generate_caption(self, product_description: str, vibe: str = "luxury minimalist") -> str:
        """Dynamically generate a highly aesthetic Instagram/TikTok caption."""
        if not self.client:
            return f"New Arrival: {product_description}\n\n#obscura #fashion"
            
        prompt = f"""
        You are the creative director for a high-end, mysterious fashion brand called OBSCURA GARMENTS.
        The aesthetic is {vibe}, dark mode, and intentional.
        
        Write a very short, punchy, and highly aesthetic social media caption for this product:
        {product_description}
        
        Rules:
        - Maximum 3 short sentences.
        - Sound expensive and curated.
        - Include 3-4 aesthetic hashtags at the end.
        - Do not use emojis unless they are dark/minimal (like ⛓️, 🖤, 🎬, ✦).
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat", # V3 model
                messages=[
                    {"role": "system", "content": "You are a luxury fashion copywriter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ DeepSeek API Error: {e}")
            return f"Archive 01: {product_description[:30]}...\n\n#obscuragarments"

if __name__ == "__main__":
    # Test
    ds = DeepSeekClient("test_key")
    if ds.client:
        print("DeepSeek Client Ready!")
