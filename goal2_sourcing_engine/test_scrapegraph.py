import os
import json
from dotenv import load_dotenv
load_dotenv()

# Use GEMINI_API_KEY from env if available
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

from scrapegraphai.graphs import SmartScraperGraph

config = {
    "llm": {
        "api_key": os.environ["GOOGLE_API_KEY"],
        "model": "google_genai/gemini-2.0-flash",
    },
    "verbose": False,
}

print("Testing ScrapeGraphAI on Goat-Official Yupoo...")
scraper = SmartScraperGraph(
    prompt=(
        "Extract ALL visible product albums from this Yupoo page. "
        "For EACH product, return: "
        "1) 'title': the product name, "
        "2) 'album_url': the DIRECT link to that specific product album, "
        "3) 'image_url': the thumbnail image URL. "
        "Return as JSON with key 'products'."
    ),
    source="https://goat-official.x.yupoo.com/",
    config=config
)

result = scraper.run()
print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
print(f"\n✅ Found {len(result.get('products', []))} products")
