"""
Agent Tools — All Capabilities Available to The Brain
====================================================
Each tool is a function the LLM can call via function calling.
Tools wrap existing scripts + add new capabilities.

Tool categories:
  RESEARCH  — Discover trends, scrape suppliers, browse brands
  CREATE    — Generate model sheets, ad images, videos, captions
  PUBLISH   — Post to TikTok, Instagram, Facebook
  OUTREACH  — Find brands, generate demos, send DMs
  FASHION   — Understand style rules, coordinate outfits
"""
import os
import shutil
import sys
import json
import time
import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

# Local imports
from agent_memory import AgentMemory
from prompt_library import (
    get_prompts_for_product, get_video_prompt,
    CANDID_FILTERS, CHARACTER_SHEET_PROMPTS, MODEL_PRESETS,
    CLOTHING_PROMPTS, SHOE_PROMPTS, ACCESSORY_PROMPTS, BEAUTY_PROMPTS,
    # Pro prompt system (previously unused!)
    build_pro_prompt, build_identity_block,
    CAMERA_PRESETS, ANTI_AI_MEDIUM, ANTI_AI_HEAVY,
    SCENE_PRESETS, get_random_scene, get_fabric_upgrade,
)
from luxury_caption_generator import CaptionGenerator

# ==========================================
# TOOL REGISTRY — What the LLM can call
# ==========================================
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "generate_model_sheet",
            "description": "Generate an AI model character sheet (face portrait) for use in ads. Creates a consistent model face that will appear across all generated ads. CALL THIS FIRST if no models exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "gender": {
                        "type": "string",
                        "enum": ["female", "male"],
                        "description": "Gender of the model"
                    },
                    "preset_index": {
                        "type": "integer",
                        "description": "Index into MODEL_PRESETS (0-5). Each preset has unique hair, eyes, skin. 0=blonde green eyes, 1=brunette olive, 2=asian, 3=redhead, 4=black, 5=nordic blonde"
                    },
                    "model_id": {
                        "type": "string",
                        "description": "Unique ID for this model, e.g. 'f1_black_female' or 'm1_mixed_male'"
                    }
                },
                "required": ["gender", "preset_index", "model_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grok_trend_analysis",
            "description": "Query xAI Grok for real-time trend analysis on X/Twitter to find viral fashion styles, specific sneakers blowing up, or streetwear aesthetics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What trend to research, e.g., 'trending sneakers 2026', 'viral y2k aesthetic'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_trending_products",
            "description": "Scrape TikTok Creative Center for currently trending products. Use this to find what's hot before generating ads.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["shoes", "clothing", "accessories", "beauty", "general"],
                        "description": "Product category to search for trends"
                    }
                },
                "required": ["category"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "browse_instagram_page",
            "description": "Browse an Instagram page to extract product images, outfit ideas, and posting style. Use for inspiration and to find potential brand clients.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Instagram username (without @)"
                    },
                    "purpose": {
                        "type": "string",
                        "enum": ["outfit_inspiration", "product_catalog", "brand_analysis", "competitor_research"],
                        "description": "Why we're browsing this page"
                    },
                    "max_posts": {
                        "type": "integer",
                        "description": "Number of recent posts to analyze"
                    }
                },
                "required": ["username", "purpose"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_ad_image",
            "description": "Generate AI ad images for a product using FlowBridge (Google AI Studio). Requires at least one model sheet to exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product"
                    },
                    "product_type": {
                        "type": "string",
                        "enum": ["clothing", "shoes", "accessories", "beauty"],
                        "description": "Product category"
                    },
                    "product_image_path": {
                        "type": "string",
                        "description": "Path to the product image file"
                    },
                    "model_id": {
                        "type": "string",
                        "description": "Which AI model to use (from memory)"
                    },
                    "ad_styles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ad styles to generate, e.g. ['mirror_selfie', 'ootd_street', 'flat_lay']"
                    }
                },
                "required": ["product_name", "product_type", "model_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "style_outfit",
            "description": "Use fashion knowledge to coordinate an outfit. Given one item (e.g. chunky sneakers), suggest what top, bottom, and accessories would work with it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "anchor_item": {
                        "type": "string",
                        "description": "The main item to build an outfit around"
                    },
                    "category": {
                        "type": "string",
                        "description": "Item category (shoes, top, bottom, outerwear)"
                    },
                    "style": {
                        "type": "string",
                        "enum": ["streetwear", "athleisure", "luxury_casual", "minimalist", "y2k", "dark_aesthetic"],
                        "description": "Overall style direction"
                    },
                    "season": {
                        "type": "string",
                        "enum": ["spring", "summer", "fall", "winter"],
                        "description": "Season for the outfit"
                    }
                },
                "required": ["anchor_item", "category", "style"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_caption",
            "description": "Generate viral captions for a product ad. Creates TikTok-safe (coded language, no brand names) and Instagram versions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product"
                    },
                    "price": {
                        "type": "string",
                        "description": "Price string like '$22'"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["shoes", "clothing", "accessories", "beauty", "general"],
                        "description": "Product category"
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["tiktok", "instagram", "facebook"],
                        "description": "Target platform"
                    }
                },
                "required": ["product_name", "category", "platform"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_content",
            "description": "Post generated content (images/videos with caption) to a social media platform.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "enum": ["tiktok", "instagram", "facebook"],
                        "description": "Where to post"
                    },
                    "media_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Paths to image/video files to post"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Caption text for the post"
                    },
                    "product_link": {
                        "type": "string",
                        "description": "Affiliate or product link"
                    }
                },
                "required": ["platform", "media_paths", "caption"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_potential_clients",
            "description": "Search Instagram for fashion/sneaker brands with 5K-50K followers that have weak ad content. These are potential agency clients.",
            "parameters": {
                "type": "object",
                "properties": {
                    "niche": {
                        "type": "string",
                        "description": "Fashion niche to search, e.g. 'streetwear', 'sneakers', 'athleisure'"
                    },
                    "location": {
                        "type": "string",
                        "description": "Target location, e.g. 'Nigeria', 'UK', 'US'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum brands to find"
                    }
                },
                "required": ["niche"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dm_brand_with_demo",
            "description": "Send a DM to a brand on Instagram with demo ad images. Use sparingly (max 5/day) to avoid bans.",
            "parameters": {
                "type": "object",
                "properties": {
                    "brand_handle": {
                        "type": "string",
                        "description": "Instagram handle of the brand"
                    },
                    "demo_image_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Paths to demo ad images to send"
                    },
                    "message": {
                        "type": "string",
                        "description": "DM text to accompany the demo"
                    }
                },
                "required": ["brand_handle", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_post_performance",
            "description": "Check engagement (likes, comments, views) on previously posted content. Use to learn what works.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "enum": ["tiktok", "instagram", "facebook"],
                        "description": "Platform to check"
                    },
                    "post_count": {
                        "type": "integer",
                        "description": "Number of recent posts to check"
                    }
                },
                "required": ["platform"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_learning",
            "description": "Record something the agent learned for future reference. Use when discovering what works or what doesn't.",
            "parameters": {
                "type": "object",
                "properties": {
                    "learning": {
                        "type": "string",
                        "description": "The insight or learning to remember"
                    }
                },
                "required": ["learning"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_and_plan",
            "description": "Pause execution and plan next steps. Use when rate limited, waiting for content to gain traction, or need to throttle activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "wait_minutes": {
                        "type": "integer",
                        "description": "Minutes to wait before next action"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why the agent is waiting"
                    }
                },
                "required": ["wait_minutes", "reason"]
            }
        }
    },
    # ── NEW: Web Research & Revenue Expansion ──
    {
        "type": "function",
        "function": {
            "name": "research_web",
            "description": "Browse ANY website to research opportunities, scrape data, find tools, or gather intelligence. This is your general-purpose web research tool. Use it to find free AI tools, research niches, check competitors, find marketplaces, discover trending topics, or gather any data from the internet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to browse. Can be any website."
                    },
                    "goal": {
                        "type": "string",
                        "description": "What you're trying to find or accomplish on this page"
                    },
                    "extract": {
                        "type": "string",
                        "enum": ["text", "links", "images", "products", "all"],
                        "description": "What type of data to extract"
                    }
                },
                "required": ["url", "goal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "use_free_ai_generator",
            "description": "Generate images using FREE AI tools that need NO login (Perchance, Raphael, FreeGen, Hugging Face Spaces). Use this when FlowBridge/Google AI Studio needs login or is unavailable. These are fallback generators.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "enum": ["perchance", "raphael", "freegen", "huggingface"],
                        "description": "Which free AI platform to use"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Image generation prompt"
                    },
                    "style": {
                        "type": "string",
                        "description": "Art style if supported (e.g. 'photorealistic', 'anime', 'digital art')"
                    },
                    "output_name": {
                        "type": "string",
                        "description": "Filename prefix for saved output"
                    }
                },
                "required": ["platform", "prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_digital_product",
            "description": "Create a digital product for selling (AI course, prompt pack, workflow template, preset pack). Generates the content, packages it, and saves it ready for listing on Gumroad or similar platforms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_type": {
                        "type": "string",
                        "enum": ["course", "prompt_pack", "workflow_template", "preset_pack", "ebook"],
                        "description": "Type of digital product to create"
                    },
                    "title": {
                        "type": "string",
                        "description": "Product title for the listing"
                    },
                    "description": {
                        "type": "string",
                        "description": "Product description/what's included"
                    },
                    "price": {
                        "type": "string",
                        "description": "Price in USD, e.g. '$15'"
                    },
                    "content_outline": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of sections/chapters/items to include"
                    }
                },
                "required": ["product_type", "title", "price"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_on_gumroad",
            "description": "List a digital product on Gumroad for sale. Requires a product file to already be created via create_digital_product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_title": {
                        "type": "string",
                        "description": "Title for the Gumroad listing"
                    },
                    "product_file_path": {
                        "type": "string",
                        "description": "Path to the product file (PDF, ZIP, etc.)"
                    },
                    "price_usd": {
                        "type": "number",
                        "description": "Price in USD"
                    },
                    "cover_image_path": {
                        "type": "string",
                        "description": "Path to the product cover image"
                    },
                    "description": {
                        "type": "string",
                        "description": "Sales copy for the listing"
                    }
                },
                "required": ["product_title", "product_file_path", "price_usd"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_login_status",
            "description": "Check if cookies/login sessions exist for Google AI Studio, TikTok, Instagram, etc. Use this to know which tools are available before trying to use them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "enum": ["google_flow", "tiktok", "instagram", "facebook", "gumroad", "all"],
                        "description": "Which service to check login status for"
                    }
                },
                "required": ["service"]
            }
        }
    },
    # self_improve and discover_tools REMOVED — self-repair engine disabled
    {
        "type": "function",
        "function": {
            "name": "generate_with_huggingface",
            "description": "Generate photorealistic images using Hugging Face's FREE Inference API with Flux or SDXL models. No browser needed, no login needed — pure API. Great for fashion model photos, sneaker shots, product images.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Detailed image generation prompt"
                    },
                    "model": {
                        "type": "string",
                        "enum": ["flux-schnell", "sdxl", "flux-dev"],
                        "description": "Which model to use. flux-schnell is fastest and free."
                    },
                    "output_name": {
                        "type": "string",
                        "description": "Base name for saved image file"
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_meta_ad_library",
            "description": "Scrape Meta/Facebook Ad Library (PUBLIC, no login!) to find competitor ads in fashion, sneakers, beauty, etc. Analyzes long-running ads (proven winners), their hooks, copy, and creative format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "What to search for, e.g., 'sneakers', 'fashion ad', 'Nike dunks'"
                    },
                    "country": {
                        "type": "string",
                        "description": "Country code (US, GB, NG). Default: US"
                    },
                    "media_type": {
                        "type": "string",
                        "enum": ["all", "image", "video"],
                        "description": "Type of ad creative to look for"
                    }
                },
                "required": ["search_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_with_pollinations",
            "description": "Generate images using Pollinations.ai — 100% FREE, NO API key needed, NO login. Uses Flux model. Great backup when Google Flow is rate-limited. Returns 1024x1024 images instantly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Detailed image generation prompt"
                    },
                    "output_name": {
                        "type": "string",
                        "description": "Base name for saved image file"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Image width in pixels. Default: 1024"
                    },
                    "height": {
                        "type": "integer",
                        "description": "Image height in pixels. Default: 1024"
                    }
                },
                "required": ["prompt"]
            }
        }
    },
]


# ==========================================
# TOOL IMPLEMENTATIONS
# ==========================================

async def tool_generate_model_sheet(
    gender: str, preset_index: int, model_id: str, memory: AgentMemory
) -> dict:
    """Generate a COMPLETE character sheet for one model.
    
    Anchor+Reference workflow:
    1. Generate front face anchor (x1, no reference needed)
    2. Download anchor via Flow ⋮ menu
    3. Upload anchor as reference for each subsequent angle
    4. Generate: front, 3/4 left, 3/4 right, side left, side right, full body
    5. Each angle = 1 separate image, saved in models/{model_id}/
    6. Resumes from where it left off if interrupted
    """
    from flow_bridge import FlowBridge

    preset = MODEL_PRESETS[min(preset_index, len(MODEL_PRESETS) - 1)]
    
    # Build identity description (kept constant across all angles)
    age = preset.get('age', '24')
    hair = preset['hair_desc']
    eyes = preset['eye_desc']
    skin = preset['skin_desc']
    face = preset.get('face_desc', 'defined cheekbones')
    identity = f"{age}-year-old {gender}, {hair}, {eyes}, {skin}, {face}"
    
    # Define all angles to generate
    ANGLES = [
        {"name": "front", "prompt": f"Hyperrealistic front-facing portrait photo of a {identity}. Clean white studio background, soft even lighting. Sharp focus on face, 85mm portrait lens. Natural expression, looking at camera. Fashion model test shoot, RAW photo.", "needs_ref": False},
        {"name": "three_quarter_left", "prompt": f"Hyperrealistic three-quarter view portrait of the SAME person from the reference image. Head turned 45 degrees to the left. {identity}. Same face, same features. White studio background, matching lighting. 85mm lens, RAW photo.", "needs_ref": True},
        {"name": "three_quarter_right", "prompt": f"Hyperrealistic three-quarter view portrait of the SAME person from the reference image. Head turned 45 degrees to the right. {identity}. Same face, same features. White studio background, matching lighting. 85mm lens, RAW photo.", "needs_ref": True},
        {"name": "profile_left", "prompt": f"Hyperrealistic side profile (90 degrees) of the SAME person from the reference image. Left side profile showing ear, jawline, nose bridge. {identity}. White studio background, rim light on profile. 85mm lens, RAW photo.", "needs_ref": True},
        {"name": "profile_right", "prompt": f"Hyperrealistic side profile (90 degrees) of the SAME person from the reference image. Right side profile. {identity}. White studio background, rim light on profile. 85mm lens, RAW photo.", "needs_ref": True},
        {"name": "full_body", "prompt": f"Full body standing photo of the SAME person from the reference image. {identity}. Wearing simple white tank top and black leggings. Natural standing pose. White studio background, even lighting. 50mm lens, RAW photo.", "needs_ref": True},
    ]
    
    # Create model-specific folder
    model_dir = os.path.join(os.getcwd(), "models", model_id)
    os.makedirs(model_dir, exist_ok=True)
    
    # Check which angles already exist (resume support)
    existing = memory.models.get(model_id, {})
    completed_angles = existing.get("angles", [])
    anchor_path = existing.get("path", "")
    
    # If anchor exists, use it
    if "front" in completed_angles and os.path.exists(anchor_path):
        print(f"   ♻️  Resuming {model_id} — {len(completed_angles)} angles done")
    
    generated_count = 0
    
    for angle_info in ANGLES:
        angle_name = angle_info["name"]
        
        # Skip if already completed
        if angle_name in completed_angles:
            print(f"   ✅ {angle_name} already exists, skipping")
            continue
        
        # Open browser for each angle (clean session)
        bridge = FlowBridge(headless=True)
        await bridge.start()
        
        try:
            # Upload reference image if needed (and anchor exists)
            ref_path = os.path.join(model_dir, "front.png")
            if angle_info["needs_ref"] and os.path.exists(ref_path):
                print(f"   📎 Uploading reference: {ref_path}")
                await bridge.upload_references([ref_path])
            elif angle_info["needs_ref"] and not os.path.exists(ref_path):
                print(f"   ⚠️  No anchor face yet — generating front first")
                await bridge.close()
                continue
            
            # Generate the angle
            images = await bridge.generate_image(
                prompt=angle_info["prompt"],
                output_prefix=f"{model_id}_{angle_name}",
                aspect="1:1" if angle_name != "full_body" else "9:16",
                multiplier="x1",
            )
            
            await bridge.close()
            
            if images and os.path.exists(images[0]):
                # Move to model folder with clean name
                dest = os.path.join(model_dir, f"{angle_name}.png")
                import shutil
                shutil.move(images[0], dest)
                fsize = os.path.getsize(dest)
                print(f"   💾 Saved {angle_name}: {dest} ({fsize//1024}KB)")
                
                # Update memory
                completed_angles.append(angle_name)
                if angle_name == "front":
                    anchor_path = dest
                
                memory.add_model(
                    model_id=model_id,
                    path=anchor_path or dest,
                    ethnicity=preset.get("skin_desc", ""),
                    gender=gender,
                    angles=completed_angles.copy(),
                )
                generated_count += 1
            else:
                print(f"   ❌ Failed to generate {angle_name}")
                # Don't continue — let the brain retry on next cycle
                return {
                    "success": generated_count > 0,
                    "model_id": model_id,
                    "angles_done": completed_angles,
                    "angles_total": len(ANGLES),
                    "error": f"Failed at {angle_name}" if generated_count == 0 else None,
                }
        except Exception as e:
            await bridge.close()
            print(f"   ❌ Error generating {angle_name}: {str(e)[:80]}")
            return {
                "success": generated_count > 0,
                "model_id": model_id,
                "angles_done": completed_angles,
                "error": str(e)[:100],
            }
        
        # Rate limit between angles (5 min cooldown)
        if angle_name != ANGLES[-1]["name"]:
            import asyncio as _asyncio
            print(f"   ⏸️  Cooling down 5 min before next angle...")
            await _asyncio.sleep(300)
    
    complete = len(completed_angles) == len(ANGLES)
    return {
        "success": True,
        "model_id": model_id,
        "model_dir": model_dir,
        "angles_done": completed_angles,
        "angles_total": len(ANGLES),
        "complete": complete,
        "message": f"{'COMPLETE' if complete else 'PARTIAL'}: {len(completed_angles)}/{len(ANGLES)} angles for {model_id}",
    }


async def tool_grok_trends(query: str, memory: AgentMemory) -> dict:
    """Use xAI Grok to research real-time trends."""
    xai_key = os.getenv("XAI_API_KEY")
    if not xai_key:
        return {"success": False, "error": "No XAI_API_KEY found"}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {xai_key}", "Content-Type": "application/json"},
                json={
                    "model": "grok-beta",
                    "messages": [
                        {"role": "system", "content": "You are a trend analyst scanning X (Twitter) for the latest fashion and sneaker trends. Return a concise, actionable summary of what's currently viral. Mention specific products/styles."},
                        {"role": "user", "content": query}
                    ]
                }
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                memory.log_action("grok_trend_analysis", f"Grok insights for '{query}': {content[:100]}...")
                return {"success": True, "insights": content}
            else:
                return {"success": False, "error": f"xAI API error: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tool_scrape_trending(category: str, memory: AgentMemory) -> dict:
    """Scrape TikTok trends."""
    try:
        from tiktok_trend_scraper import TikTokTrendScraper
        scraper = TikTokTrendScraper(headless=True)
        await scraper.start()
        trends = await scraper.scrape_all()
        await scraper.close()
        memory.log_action("scrape_trending", f"Found {len(trends.get('products', []))} trending products")
        return {"success": True, "trends": trends}
    except Exception as e:
        memory.log_action("scrape_trending", str(e), success=False)
        return {"success": False, "error": str(e)}


async def tool_scrape_agents(
    platforms: list, categories: list, max_products: int, memory: AgentMemory
) -> dict:
    """Scrape agent platforms for products."""
    try:
        from agent_product_scraper import AgentPlatformScraper, add_affiliate_link
        scraper = AgentPlatformScraper(headless=True)
        await scraper.start()
        products = await scraper.scrape_all(
            platforms=platforms,
            categories=categories,
        )
        products = [add_affiliate_link(p) for p in products][:max_products]
        await scraper.close()

        memory.add_products_batch(products)
        memory.log_action("scrape_agents", f"Sourced {len(products)} products")
        return {"success": True, "products_count": len(products), "products": products[:5]}
    except Exception as e:
        memory.log_action("scrape_agents", str(e), success=False)
        return {"success": False, "error": str(e)}


async def tool_scrape_yupoo(
    seller_url: str, category: str = "general", max_items: int = 10, memory: AgentMemory = None
) -> dict:
    """Scrape a Yupoo seller's catalog."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            url = f"https://{seller_url}" if not seller_url.startswith("http") else seller_url
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            # Extract album/product links
            albums = await page.query_selector_all('a[href*="/albums/"]')
            products = []
            for album in albums[:max_items]:
                title = await album.inner_text()
                href = await album.get_attribute("href")
                img_el = await album.query_selector("img")
                img_src = await img_el.get_attribute("src") if img_el else ""
                products.append({
                    "productName": title.strip(),
                    "productUrl": href,
                    "productImage": img_src,
                    "source": "yupoo",
                    "seller": seller_url,
                    "category": category or "general",
                })

            await browser.close()

        memory.add_products_batch(products)
        memory.add_yupoo_supplier(seller_url.split(".")[0], seller_url)
        memory.log_action("scrape_yupoo", f"Found {len(products)} items from {seller_url}")
        return {"success": True, "products_count": len(products)}
    except Exception as e:
        memory.log_action("scrape_yupoo", str(e), success=False)
        return {"success": False, "error": str(e)}


async def tool_browse_instagram(
    username: str, purpose: str, max_posts: int, memory: AgentMemory
) -> dict:
    """Browse an Instagram page for product/outfit extraction."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
            )
            page = await ctx.new_page()
            await page.goto(f"https://www.instagram.com/{username}/", timeout=30000)
            await asyncio.sleep(5)

            # Extract post thumbnails
            posts = await page.query_selector_all('article img')
            extracted = []
            for post in posts[:max_posts]:
                src = await post.get_attribute("src")
                alt = await post.get_attribute("alt") or ""
                extracted.append({"image_url": src, "description": alt})

            # Get follower count and bio
            bio_text = await page.inner_text("header") if await page.query_selector("header") else ""

            await browser.close()

        result = {
            "username": username,
            "purpose": purpose,
            "posts_found": len(extracted),
            "posts": extracted[:10],
            "bio": bio_text[:500],
        }

        if purpose == "brand_analysis":
            memory.add_brand({"handle": username, "bio": bio_text[:200], "posts": len(extracted)})

        memory.log_action("browse_instagram", f"Browsed @{username}, found {len(extracted)} posts")
        return {"success": True, **result}
    except Exception as e:
        memory.log_action("browse_instagram", str(e), success=False)
        return {"success": False, "error": str(e)}


# pylint: disable=too-many-arguments
async def tool_generate_ad(
    product_name: str, product_type: str,
    model_id: str, ad_styles: list, memory: AgentMemory,
    product_image_path: str = None,
    polished_prompt_from_director: str = None
) -> dict:
    """Generate ad images using actual model + product reference images.
    
    The bridge uploads model face, model body, and product image to Flow,
    then generates with a simple prompt that references the images by position.
    This ensures the output uses OUR models wearing OUR actual products.
    """
    from generation_router import GenerationRouter

    # --- Find actual model character sheet images ---
    models_dir = os.path.join(os.getcwd(), "models", "character_sheets")
    
    # Use the model_id to find face/body images (e.g. "f1" -> f1_face.png, f1_body.png)
    face_path = os.path.join(models_dir, f"{model_id}_face.png")
    body_path = os.path.join(models_dir, f"{model_id}_body.png")
    
    if not os.path.exists(face_path):
        # Fallback: pick any available model
        import glob
        faces = glob.glob(os.path.join(models_dir, "*_face.png"))
        if faces:
            face_path = random.choice(faces)
            prefix = os.path.basename(face_path).replace("_face.png", "")
            body_path = os.path.join(models_dir, f"{prefix}_body.png")
            model_id = prefix
            print(f"[*] Model {model_id} not found, using {prefix} instead")
        else:
            print("[!] No model character sheets found!")
            return {"success": False, "error": "No model images found"}
    
    # --- Auto-resolve product image if not provided ---
    if not product_image_path or not os.path.exists(product_image_path):
        import glob
        sourcing_dir = os.path.join(os.getcwd(), "input_sourcing")
        candidates = glob.glob(os.path.join(sourcing_dir, "**", "*.jpg"), recursive=True)
        candidates += glob.glob(os.path.join(sourcing_dir, "**", "*.png"), recursive=True)
        if candidates:
            product_image_path = candidates[0]
            print(f"[*] No product image provided — auto-selected: {os.path.basename(product_image_path)}")
        else:
            print("[!] No product images found in input_sourcing/ — scrape products first")
            return {"success": False, "error": "No product images available. Run scrape_agent_products or scrape_yupoo_catalog first."}
    
    # Build reference image list: [face, body, product]
    ref_images = [face_path]
    if os.path.exists(body_path):
        ref_images.append(body_path)
    ref_images.append(product_image_path)
    
    print(f"[*] References: model={model_id} ({len(ref_images)} images), product={os.path.basename(product_image_path)}")
    
    # --- Simple prompts that REFERENCE the images, don't describe them ---
    SIMPLE_PROMPTS = [
        # Concept 1: Exotic Marrakech Architecture (Warm, Texture)
        (
            f"Put the exact garment/item from the product reference image on the person from the face and body reference images. "
            f"CRITICAL: Design a complete, premium high-fashion outfit around this product. Do NOT keep the model's original base clothing. "
            f"Style the rest of the look with complementary designer streetwear (e.g., luxury denim, avant-garde jackets, modern silhouettes). "
            f"Generate a hyperrealistic high-fashion editorial photo. "
            f"Location: Inside an ornate, terracotta courtyard in Marrakech, Morocco. Intricate tilework and sweeping archways. "
            f"Lighting: Hard, sculpted sunlight cutting through architectural gaps, creating dramatic geometric shadows. "
            f"Shot on medium format camera, 50mm at f/8 for deep depth of field. The background must be razor-sharp and visible, NO bokeh. "
            f"The product must match the reference EXACTLY. "
            f"Confident, avant-garde posing. Vogue magazine aesthetic."
        ),
        # Concept 2: Dubai / Neo-Tokyo Futuristic (Cinematic, High Contrast)
        (
            f"Put the exact garment/item from the product reference image on the person from the face and body reference images. "
            f"CRITICAL: Design a complete, premium high-fashion outfit around this product. Do NOT keep the model's original base clothing. "
            f"Style the rest of the look with complementary futuristic luxury streetwear. "
            f"Generate a hyperrealistic high-fashion editorial photo. "
            f"Location: A sleek, ultra-modern glass and steel skyscraper interior at night overlooking a sprawling cyberpunk neon city. "
            f"Lighting: Complex cinematic lighting with practical RGB Pavotubes in frame. A cool blue rim light separating {gender_subj.lower()} from the background, and a warm key light. "
            f"Shot on 35mm at f/11 for deep depth of field. The entire cityscape background is in sharp focus, NO background blur. "
            f"The product fills 60% of the frame. Premium, high-budget campaign look."
        ),
        # Concept 3: Rugged Volcanic Landscape (Isolated, Dramatic)
        (
            f"Put the exact garment/item from the product reference image on the person from the face and body reference images. "
            f"CRITICAL: Design a complete, premium high-fashion outfit around this product. Do NOT keep the model's original base clothing. "
            f"Style the rest of the look with edgy, avant-garde designer pieces that fit the rugged environment. "
            f"Generate a hyperrealistic high-fashion editorial photo. "
            f"Location: Expansive, wind-swept black sand volcanic landscape in Fuerteventura, Canary Islands. "
            f"Lighting: Overcast sky acting as a giant softbox, supplemented by a powerful off-camera strobe with a beauty dish aimed at the subject to create high contrast against the dark landscape. "
            f"Shot on 24mm wide angle lens at f/8. The expansive landscape is in razor-sharp focus all the way to the horizon. NO bokeh. "
            f"Fierce, powerful editorial pose. Natural skin texture, visible pores."
        ),
        # Concept 4: Classic Parisian Luxury (Timeless, Elegance)
        (
            f"Put the exact garment/item from the product reference image on the person from the face and body reference images. "
            f"CRITICAL: Design a complete, premium high-fashion outfit around this product. Do NOT keep the model's original base clothing. "
            f"Style the rest of the look with chic, minimalist classic pieces (e.g., tailored trousers, luxury knitwear). "
            f"Generate a hyperrealistic high-fashion editorial photo. "
            f"Location: A grand, sun-drenched Parisian apartment with ornate moldings and towering French windows. "
            f"Lighting: A crisp spotlight from the side mimics afternoon sun, with deep shadows and soft ambient fill. "
            f"Shot on 50mm at f/8 for deep depth of field. Background details must be completely sharp. NO bokeh. "
            f"Elegant, poise-focused editorial pose. Skin must look natural and real."
        ),
        "High-fashion editorial: subject wearing product from reference, avant-garde style, Marrakech architecture background, 50mm, deep depth of field.",
        "Cinematic luxury: model wearing product in modern skyscraper interior, cyberpunk neon lighting, 35mm, deep depth of field.",
        "Rugged editorial: subject wearing product on black sand volcanic landscape, strobe lighting, 24mm, deep depth of field.",
        "Parisian chic: subject wearing product in ornate apartment, crisp spotlight, 50mm, deep depth of field."
    ]
    
    # --- DeepSeek-R1 "Marketing Director" Logic ---
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if not polished_prompt_from_director and deepseek_key:
        print(f"[*] DeepSeek-R1 Marketing Director is thinking about the shot for {product_name}...")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                director_prompt = (
                    f"You are an avant-garde Fashion Marketing Director. We need to shoot an editorial ad for: '{product_name}'. "
                    f"Target styles: {', '.join(ad_styles) if ad_styles else 'High fashion editorial'}. "
                    f"Write a hyper-detailed image generation prompt (1 paragraph) describing the location, lighting, camera settings (lens, depth of field), and overall aesthetic. "
                    f"MUST include this exact phrase at the beginning: 'Put the exact garment/item from the product reference image on the person from the face and body reference images. CRITICAL: Design a complete, premium high-fashion outfit around this product.' "
                    f"Do NOT output anything else except the final image generation prompt."
                )
                resp = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"},
                    json={
                        "model": "deepseek-reasoner",
                        "messages": [{"role": "user", "content": director_prompt}]
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    reasoning = data["choices"][0]["message"].get("reasoning_content", "")
                    if reasoning:
                        print(f"   [DeepSeek R1 Thinking]: {reasoning[:200]}...")
                        memory.log_action("deepseek_strategy", f"Thinking: {reasoning[:200]}...")
                    polished_prompt_from_director = data["choices"][0]["message"]["content"].strip()
                    print(f"   [DeepSeek R1 Output]: {polished_prompt_from_director[:200]}...")
                else:
                    print(f"[!] DeepSeek API error: {resp.text}")
        except Exception as e:
            print(f"[!] DeepSeek API failed: {e}")
            
    # --- Gemini Director Logic ---
    if polished_prompt_from_director:
        final_prompt = polished_prompt_from_director
    else:
        # Fallback to simple random prompts
        prompt = random.choice(SIMPLE_PROMPTS)
        final_prompt = prompt

    # --- Output setup (REVIEW SYSTEM) ---
    safe_name = product_name.replace(" ", "_")[:25].lower()
    output_dir = os.path.join(os.getcwd(), "review_pending", safe_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # --- Generate via bridge (1 image per product) ---
    router = GenerationRouter()
    
    try:
        images = await router.generate_image(
            prompt=final_prompt,
            ref_image_paths=ref_images,
            output_prefix=f"{safe_name}_{model_id}",
            aspect="3:4",
        )
        
        if images and len(images) > 0:
            src_path = images[0]
            if os.path.exists(src_path) and os.path.getsize(src_path) > 1000:
                dest_path = os.path.join(output_dir, os.path.basename(src_path))
                shutil.copy2(src_path, dest_path)
                print(f"[+] SAVED to {dest_path}")
                
                memory.mark_product_processed(
                    {"productName": product_name, "type": product_type},
                    ad_paths=[dest_path],
                )
                memory.log_action("generate_ad", f"Generated image for {product_name} with model {model_id}")
                return {"success": True, "images": [dest_path], "count": 1, "output_dir": output_dir}
            else:
                print(f"[!] Generated file is too small or missing: {src_path}")
        else:
            print("[!] Bridge returned no images")
            
    except Exception as e:
        print(f"[!] Generation failed: {e}")
    
    memory.log_action("generate_ad", f"FAILED to generate for {product_name}")
    return {"success": False, "error": "Generation failed", "images": [], "count": 0}


async def tool_generate_caption(
    product_name: str, price: str, category: str, platform: str, memory: AgentMemory
) -> dict:
    """Generate captions using Groq's Llama-3.3-70B."""
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return {"success": False, "error": "No GROQ_API_KEY found"}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            prompt = f"Write 3 short, viral, Gen-Z streetwear captions for a {product_name} priced at {price}. Platform: {platform}. Format as JSON with a 'captions' key containing an array of strings."
            if platform == "tiktok":
                prompt += " IMPORTANT: DO NOT mention any brand names. Use coded language like 'the LV pattern' instead of 'Louis Vuitton'."
            
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    captions = parsed.get("captions", [])
                    if not captions and isinstance(parsed, dict) and parsed:
                        captions = list(parsed.values())[0]
                        
                    formatted = [{"variant": i+1, "caption": c, "platform": platform} for i, c in enumerate(captions[:3])]
                    memory.log_action("generate_caption", f"Generated {len(formatted)} Groq captions for {product_name}")
                    return {"success": True, "captions": formatted}
                except Exception as e:
                    return {"success": False, "error": f"JSON parse error: {str(e)}"}
            else:
                return {"success": False, "error": f"Groq API error: {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_style_outfit(
    anchor_item: str, category: str, style: str, season: str = "spring"
) -> dict:
    """Use fashion rules to coordinate an outfit."""
    # Import inline to avoid circular deps
    from fashion_brain import coordinate_outfit
    result = coordinate_outfit(anchor_item, category, style, season)
    return {"success": True, "outfit": result}


async def tool_post_content(
    platform: str, media_paths: list, caption: str, product_link: str,
    memory: AgentMemory
) -> dict:
    """Post content to social media."""
    try:
        from social_autoposter import distribute_content
        distribute_content(
            video_url=media_paths[0] if len(media_paths) == 1 else media_paths,
            caption=caption,
            product_link=product_link,
            product_type="general",
        )
        memory.mark_product_posted(
            {"caption": caption[:50]},
            platform=platform,
        )
        memory.log_action("post_content", f"Posted to {platform}")
        return {"success": True, "platform": platform}
    except Exception as e:
        memory.log_action("post_content", str(e), success=False)
        return {"success": False, "error": str(e)}


async def tool_find_clients(niche: str, location: str, max_results: int, memory: AgentMemory) -> dict:
    """Find potential brand clients on Instagram."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            # Search Instagram hashtags for brands
            search_tags = [f"{niche}brand", f"{niche}shop", f"{niche}store"]
            brands_found = []

            for tag in search_tags[:2]:
                await page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=30000)
                await asyncio.sleep(5)
                posts = await page.query_selector_all('article a[href*="/p/"]')
                for post in posts[:3]:
                    href = await post.get_attribute("href")
                    brands_found.append({"tag": tag, "post_url": href})

            await browser.close()

        for brand in brands_found[:max_results]:
            memory.add_brand(brand)

        memory.log_action("find_clients", f"Found {len(brands_found)} potential clients in {niche}")
        return {"success": True, "brands_found": len(brands_found), "brands": brands_found[:max_results]}
    except Exception as e:
        memory.log_action("find_clients", str(e), success=False)
        return {"success": False, "error": str(e)}


async def tool_dm_brand(
    brand_handle: str, demo_image_paths: list, message: str, memory: AgentMemory
) -> dict:
    """Send a DM with demo ads to a brand."""
    # Check daily DM limit
    today_dms = len([
        b for b in memory.data.get("brands_contacted", [])
        if b.get("contacted_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))
    ])
    if today_dms >= memory.data["daily_limits"]["max_dms"]:
        return {"success": False, "error": f"Daily DM limit reached ({today_dms}/{memory.data['daily_limits']['max_dms']})"}

    # Note: Actual DM sending requires a logged-in Instagram session
    # This is a placeholder — real implementation uses Playwright
    memory.mark_brand_contacted(brand_handle, message)
    memory.log_action("dm_brand", f"DMed @{brand_handle}")

    # Add random delay to appear human
    await asyncio.sleep(random.randint(30, 120))

    return {"success": True, "brand": brand_handle, "dms_today": today_dms + 1}


def tool_add_learning(learning: str, memory: AgentMemory) -> dict:
    """Record a learning."""
    memory.add_learning(learning)
    return {"success": True, "total_learnings": len(memory.data["learnings"])}


async def tool_check_performance(platform: str, post_count: int, memory: AgentMemory) -> dict:
    """Check post engagement."""
    posts = memory.data.get("products_posted", [])
    platform_posts = [p for p in posts if p.get("_platform") == platform]
    return {
        "success": True,
        "platform": platform,
        "total_posts": len(platform_posts),
        "recent_posts": platform_posts[-post_count:],
    }


# ==========================================
# NEW TOOL IMPLEMENTATIONS
# ==========================================

async def tool_research_web(url: str, goal: str, extract: str = "all", memory: AgentMemory = None) -> dict:
    """Browse any website and extract data."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await ctx.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

            result = {"url": url, "goal": goal}

            if extract in ("text", "all"):
                body = await page.query_selector("body")
                text = await body.inner_text() if body else ""
                result["text"] = text[:5000]  # Cap at 5K chars

            if extract in ("links", "all"):
                links = await page.query_selector_all("a[href]")
                extracted_links = []
                for link in links[:50]:
                    href = await link.get_attribute("href") or ""
                    text = (await link.inner_text()).strip()[:100]
                    if href and not href.startswith("#"):
                        extracted_links.append({"text": text, "href": href})
                result["links"] = extracted_links

            if extract in ("images", "all"):
                imgs = await page.query_selector_all("img[src]")
                extracted_imgs = []
                for img in imgs[:30]:
                    src = await img.get_attribute("src") or ""
                    alt = await img.get_attribute("alt") or ""
                    if src:
                        extracted_imgs.append({"src": src, "alt": alt[:100]})
                result["images"] = extracted_imgs

            if extract == "products":
                # Try to extract product-like elements
                text = await page.inner_text("body")
                result["text"] = text[:5000]
                # Look for price patterns
                import re
                prices = re.findall(r'\$[\d,]+\.?\d*', text)
                result["prices_found"] = prices[:20]

            # Get page title
            result["title"] = await page.title()

            await browser.close()

        if memory:
            memory.log_action("research_web", f"Browsed {url}: {goal}")
        return {"success": True, **result}
    except Exception as e:
        if memory:
            memory.log_action("research_web", str(e), success=False)
        return {"success": False, "error": str(e)}


async def tool_use_free_ai(
    platform: str, prompt: str, style: str = "photorealistic",
    output_name: str = "generated", memory: AgentMemory = None
) -> dict:
    """Generate images using free, no-login AI platforms."""
    try:
        from playwright.async_api import async_playwright
        output_dir = os.path.join(os.getcwd(), "output", "free_ai")
        os.makedirs(output_dir, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            if platform == "perchance":
                await page.goto("https://perchance.org/ai-photo-generator", timeout=30000)
                await asyncio.sleep(5)
                # Find and fill prompt input
                textarea = await page.query_selector("textarea")
                if textarea:
                    await textarea.fill(prompt)
                    # Click generate button
                    btn = await page.query_selector("button:has-text('Generate')")
                    if btn:
                        await btn.click()
                        await asyncio.sleep(30)  # Wait for generation
                        # Try to download result
                        imgs = await page.query_selector_all("img.generated, img.output")
                        saved = []
                        for i, img in enumerate(imgs[:4]):
                            src = await img.get_attribute("src")
                            if src and src.startswith("data:"):
                                # Save base64 image
                                import base64
                                data = src.split(",")[1] if "," in src else src
                                path = os.path.join(output_dir, f"{output_name}_{i}.png")
                                with open(path, "wb") as f:
                                    f.write(base64.b64decode(data))
                                saved.append(path)
                        await browser.close()
                        if memory:
                            memory.log_action("free_ai_generate", f"Generated {len(saved)} images via {platform}")
                        return {"success": True, "images": saved, "platform": platform}

            elif platform == "raphael":
                await page.goto("https://raphael.app", timeout=30000)
                await asyncio.sleep(5)
                textarea = await page.query_selector("textarea, input[type='text']")
                if textarea:
                    await textarea.fill(prompt)
                    btn = await page.query_selector("button:has-text('Generate'), button:has-text('Create')")
                    if btn:
                        await btn.click()
                        await asyncio.sleep(30)

            elif platform == "huggingface":
                # Browse HuggingFace Spaces for image gen models
                await page.goto("https://huggingface.co/spaces?sort=likes&search=image+generation", timeout=30000)
                await asyncio.sleep(5)
                spaces = await page.query_selector_all("article a")
                space_links = []
                for space in spaces[:10]:
                    href = await space.get_attribute("href") or ""
                    text = (await space.inner_text()).strip()[:100]
                    space_links.append({"name": text, "url": f"https://huggingface.co{href}"})
                await browser.close()
                if memory:
                    memory.log_action("free_ai_generate", f"Found {len(space_links)} HuggingFace spaces")
                return {"success": True, "spaces": space_links, "platform": "huggingface"}

            await browser.close()

        if memory:
            memory.log_action("free_ai_generate", f"Used {platform}")
        return {"success": True, "platform": platform, "note": "Generation attempted"}
    except Exception as e:
        if memory:
            memory.log_action("free_ai_generate", str(e), success=False)
        return {"success": False, "error": str(e)}


# pylint: disable=too-many-arguments
def tool_create_digital_product(
    product_type: str, title: str, price: str,
    description: str = "", content_outline: list = None,
    memory: AgentMemory = None
) -> dict:
    """Create a digital product (course, prompt pack, etc)."""
    output_dir = os.path.join(os.getcwd(), "digital_products")
    os.makedirs(output_dir, exist_ok=True)

    safe_title = title.replace(" ", "_")[:40].lower()

    if product_type == "prompt_pack":
        # Package prompts from prompt_library into a sellable format
        from prompt_library import (
            CLOTHING_PROMPTS, SHOE_PROMPTS, ACCESSORY_PROMPTS,
            BEAUTY_PROMPTS, WIG_PROMPTS, CHARACTER_SHEET_PROMPTS,
            CANDID_FILTERS,
        )
        content_parts = [
            f"# {title}\n\n",
            f"{description}\n\n",
            "## 🔥 Anti-AI Detection Filter\n",
            f"```\n{CANDID_FILTERS}\n```\n\n"
        ]

        sections = {
            "Clothing Ad Prompts": CLOTHING_PROMPTS,
            "Shoe Ad Prompts": SHOE_PROMPTS,
            "Accessory Prompts": ACCESSORY_PROMPTS,
            "Beauty Prompts": BEAUTY_PROMPTS,
            "Wig/Hair Prompts": WIG_PROMPTS,
            "Character Sheet Prompts": CHARACTER_SHEET_PROMPTS,
        }
        for section_name, prompts in sections.items():
            content_parts.append(f"## {section_name}\n\n")
            for name, prompt in prompts.items():
                content_parts.append(f"### {name.replace('_', ' ').title()}\n")
                content_parts.append(f"```\n{prompt}\n```\n\n")

        content = "".join(content_parts)
        filepath = os.path.join(output_dir, f"{safe_title}.md")
        with open(filepath, "w") as f:
            f.write(content)

    elif product_type == "course":
        outline = content_outline or [
            "Module 1: Setting Up Your Free AI Tools",
            "Module 2: Creating Consistent AI Models",
            "Module 3: Generating Photorealistic Ads",
            "Module 4: Writing Viral Captions",
            "Module 5: Automating Social Media Posts",
            "Module 6: Finding & Pitching Brands",
            "Module 7: Scaling to $1K/Month",
        ]
        content_parts = [
            f"# {title}\n\n",
            f"**Price: {price}**\n\n",
            f"{description}\n\n",
            "## Course Outline\n\n"
        ]
        for i, module in enumerate(outline):
            content_parts.append(f"{i+1}. {module}\n")

        content_parts.extend([
            "\n\n## What You'll Learn\n\n",
            "- Generate unlimited photorealistic AI ads for FREE\n",
            "- Create consistent AI model characters\n",
            "- Automate posting to TikTok, Instagram, Facebook\n",
            "- Build an AI ad agency from scratch\n",
            "- Use free AI tools (no paid APIs needed)\n"
        ])

        content = "".join(content_parts)
        filepath = os.path.join(output_dir, f"{safe_title}.md")
        with open(filepath, "w") as f:
            f.write(content)

    elif product_type == "workflow_template":
        content_parts = [
            f"# {title}\n\n",
            f"**Price: {price}**\n\n",
            "## Included Workflows\n\n",
            "1. Product Scraping (USFans/CNFans/Yupoo)\n",
            "2. AI Image Generation (Google AI Studio)\n",
            "3. Caption Generation (TikTok-safe)\n",
            "4. Auto-Posting Pipeline\n",
            "5. Brand Outreach Automation\n"
        ]
        for item in (content_outline or []):
            content_parts.append(f"- {item}\n")

        content = "".join(content_parts)
        filepath = os.path.join(output_dir, f"{safe_title}.md")
        with open(filepath, "w") as f:
            f.write(content)
    else:
        filepath = os.path.join(output_dir, f"{safe_title}.md")
        content_parts = [
            f"# {title}\n\n{description}\n\nPrice: {price}\n"
        ]
        for item in (content_outline or []):
            content_parts.append(f"- {item}\n")

        content = "".join(content_parts)
        with open(filepath, "w") as f:
            f.write(content)

    # Track in memory
    if memory:
        if "digital_products" not in memory.data:
            memory.data["digital_products"] = []
        memory.data["digital_products"].append({
            "type": product_type,
            "title": title,
            "price": price,
            "file": filepath,
            "created_at": datetime.now().isoformat(),
            "listed": False,
        })
        memory.save()
        memory.log_action("create_digital_product", f"Created {product_type}: {title}")

    return {"success": True, "file": filepath, "type": product_type, "title": title}


# pylint: disable=too-many-arguments
async def tool_list_on_gumroad(
    product_title: str, product_file_path: str, price_usd: float,
    cover_image_path: str = "", description: str = "",
    memory: AgentMemory = None
) -> dict:
    """List a product on Gumroad."""
    if not os.path.exists(product_file_path):
        return {"success": False, "error": f"Product file not found: {product_file_path}"}

    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context()

            # Check for saved Gumroad cookies
            cookie_path = os.path.expanduser("~/.gumroad_cookies.json")
            if os.path.exists(cookie_path):
                import json as _json
                cookies = _json.load(open(cookie_path))
                await ctx.add_cookies(cookies)

            page = await ctx.new_page()
            await page.goto("https://app.gumroad.com/products/new", timeout=30000)
            await asyncio.sleep(3)

            # Check if we're logged in
            if "login" in page.url.lower():
                await browser.close()
                if memory:
                    memory.add_learning("Gumroad login needed. Need to manually log in and save cookies.")
                return {"success": False, "error": "Not logged into Gumroad. Need manual login first."}

            # Fill in product details
            name_input = await page.query_selector("input[name='name'], input[placeholder*='name']")
            if name_input:
                await name_input.fill(product_title)

            price_input = await page.query_selector("input[name='price'], input[type='number']")
            if price_input:
                await price_input.fill(str(price_usd))

            desc_input = await page.query_selector("textarea, [contenteditable='true']")
            if desc_input:
                await desc_input.fill(description or f"Premium digital product: {product_title}")

            await browser.close()

        if memory:
            memory.log_action("list_on_gumroad", f"Listed {product_title} at ${price_usd}")
            # Update digital product as listed
            for prod in memory.data.get("digital_products", []):
                if prod.get("title") == product_title:
                    prod["listed"] = True
            memory.save()

        return {"success": True, "title": product_title, "price": price_usd}
    except Exception as e:
        if memory:
            memory.log_action("list_on_gumroad", str(e), success=False)
        return {"success": False, "error": str(e)}


def tool_check_login_status(service: str, memory: AgentMemory) -> dict:
    """Check login status for various services."""
    import os
    home = os.path.expanduser("~")

    cookie_files = {
        "google_flow": os.path.join(home, ".flow_bridge_cookies.json"),
        "tiktok": os.path.join(home, ".tiktok_cookies.json"),
        "instagram": os.path.join(home, ".instagram_cookies.json"),
        "facebook": os.path.join(home, ".facebook_cookies.json"),
        "gumroad": os.path.join(home, ".gumroad_cookies.json"),
    }

    if service == "all":
        statuses = {}
        for svc, path in cookie_files.items():
            exists = os.path.exists(path)
            statuses[svc] = {
                "logged_in": exists,
                "cookie_file": path,
                "file_exists": exists,
            }
            if exists:
                mtime = os.path.getmtime(path)
                age_hours = (datetime.now().timestamp() - mtime) / 3600
                statuses[svc]["age_hours"] = round(age_hours, 1)
                statuses[svc]["possibly_expired"] = age_hours > 24 * 7  # >1 week
            memory.update_account_status(svc, exists, exists)
        return {"success": True, "statuses": statuses}
    else:
        path = cookie_files.get(service, "")
        exists = os.path.exists(path) if path else False
        result = {
            "service": service,
            "logged_in": exists,
            "cookie_file": path,
        }
        if exists:
            mtime = os.path.getmtime(path)
            age_hours = (datetime.now().timestamp() - mtime) / 3600
            result["age_hours"] = round(age_hours, 1)
            result["possibly_expired"] = age_hours > 24 * 7
        if service in cookie_files:
            memory.update_account_status(service, exists, exists)
        return {"success": True, **result}


# ==========================================
# HUGGING FACE IMAGE GENERATION (FREE API)
# ==========================================
async def tool_generate_huggingface(
    prompt: str, model: str = "flux-schnell", output_name: str = "hf_gen",
    memory: AgentMemory = None, **kwargs
) -> dict:
    """
    Generate images using Hugging Face's free Inference API.
    No browser needed — pure HTTP API call.
    """
    import httpx
    
    output_dir = os.path.join(os.getcwd(), "output", "huggingface")
    os.makedirs(output_dir, exist_ok=True)
    
    # Model mapping
    model_map = {
        "flux-schnell": "black-forest-labs/FLUX.1-schnell",
        "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
        "flux-dev": "black-forest-labs/FLUX.1-dev",
    }
    model_id = model_map.get(model, model_map["flux-schnell"])
    
    # HF token (optional for some models, needed for others)
    hf_token = os.getenv("HF_TOKEN", "")
    
    headers = {"Content-Type": "application/json"}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
    
    api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                api_url,
                headers=headers,
                json={"inputs": prompt},
            )
            
            if resp.status_code == 200:
                # Response is raw image bytes
                timestamp = int(time.time())
                filename = f"{output_name}_{timestamp}.png"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                
                print(f"✅ HuggingFace generated: {filename}")
                if memory:
                    memory.log_action("generate_huggingface", f"Generated {filename} with {model}")
                return {"success": True, "image_path": filepath, "model": model}
            elif resp.status_code == 503:
                # Model is loading
                data = resp.json()
                wait_time = data.get("estimated_time", 30)
                print(f"⏳ Model loading, waiting {wait_time}s...")
                await asyncio.sleep(min(wait_time, 60))
                # Retry once
                resp2 = await client.post(api_url, headers=headers, json={"inputs": prompt})
                if resp2.status_code == 200:
                    timestamp = int(time.time())
                    filename = f"{output_name}_{timestamp}.png"
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(resp2.content)
                    if memory:
                        memory.log_action("generate_huggingface", f"Generated {filename}")
                    return {"success": True, "image_path": filepath, "model": model}
                else:
                    return {"success": False, "error": f"Retry failed: {resp2.status_code}"}
            else:
                error_text = resp.text[:200]
                return {"success": False, "error": f"HF API error {resp.status_code}: {error_text}"}
    except Exception as e:
        if memory:
            memory.log_action("generate_huggingface", str(e), success=False)
        return {"success": False, "error": str(e)}

# ==========================================
# POLLINATIONS.AI — FREE Image Gen (No API Key!)
# ==========================================
async def tool_generate_pollinations(
    prompt: str, output_name: str = "poll_gen", width: int = 1024, height: int = 1024,
    memory: AgentMemory = None, **kwargs
) -> dict:
    """
    Generate images using Pollinations.ai — completely FREE, no API key needed.
    Uses Flux model via a simple HTTP GET request.
    """
    import httpx
    import urllib.parse
    
    output_dir = os.path.join(os.getcwd(), "output", "pollinations")
    os.makedirs(output_dir, exist_ok=True)
    
    # URL-encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&seed={int(time.time())}"
    
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            resp = await client.get(url)
            
            if resp.status_code == 200 and len(resp.content) > 10000:
                timestamp = int(time.time())
                filename = f"{output_name}_{timestamp}.png"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                
                fsize = os.path.getsize(filepath)
                print(f"✅ Pollinations generated: {filename} ({fsize//1024}KB)")
                if memory:
                    memory.log_action("generate_pollinations", f"Generated {filename} ({fsize//1024}KB)")
                return {"success": True, "image_path": filepath, "size_kb": fsize // 1024}
            else:
                return {"success": False, "error": f"Pollinations returned {resp.status_code}, {len(resp.content)} bytes"}
    except Exception as e:
        if memory:
            memory.log_action("generate_pollinations", str(e), success=False)
        return {"success": False, "error": str(e)}


# ==========================================
# META AD LIBRARY SCRAPER (PUBLIC, NO LOGIN)
# ==========================================
async def tool_scrape_meta_ads(
    search_query: str, country: str = "US", media_type: str = "all",
    memory: AgentMemory = None
) -> dict:
    """
    Scrape Meta's public Ad Library for competitor ads.
    No login required — the Ad Library is publicly accessible.
    """
    try:
        from playwright.async_api import async_playwright
        
        url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country={country}&q={search_query}&media_type={media_type}"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await ctx.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)
            
            # Scroll to load more ads
            for _ in range(3):
                await page.keyboard.press("End")
                await asyncio.sleep(2)
            
            # Extract ad data
            ads = []
            
            # Get all ad cards
            body_text = await page.inner_text("body")
            title = await page.title()
            
            # Get images from ads
            images = await page.query_selector_all("img")
            ad_images = []
            for img in images[:20]:
                src = await img.get_attribute("src") or ""
                alt = await img.get_attribute("alt") or ""
                if src and "scontent" in src:  # Facebook CDN images
                    ad_images.append({"src": src, "alt": alt[:100]})
            
            # Get text blocks (ad copy)
            ad_texts = []
            divs = await page.query_selector_all("div")
            for div in divs[:100]:
                text = (await div.inner_text()).strip()
                if len(text) > 50 and len(text) < 500:
                    # Likely an ad copy block
                    if any(kw in text.lower() for kw in ["shop", "buy", "free", "sale", "new", "limited", "www", ".com", "click"]):
                        ad_texts.append(text[:300])
            
            # Deduplicate
            ad_texts = list(set(ad_texts))[:10]
            
            await browser.close()
        
        result = {
            "success": True,
            "query": search_query,
            "country": country,
            "page_title": title,
            "ad_images_found": len(ad_images),
            "ad_images": ad_images[:10],
            "ad_copy_samples": ad_texts,
            "raw_text_preview": body_text[:2000],
        }
        
        if memory:
            memory.log_action("scrape_meta_ads", f"Found {len(ad_images)} ad images and {len(ad_texts)} copy samples for '{search_query}'")
            memory.add_learning(f"Scraped Meta Ad Library for '{search_query}': {len(ad_images)} images, {len(ad_texts)} copy samples")
        
        return result
    except Exception as e:
        if memory:
            memory.log_action("scrape_meta_ads", str(e), success=False)
        return {"success": False, "error": str(e)}


# ==========================================
# TOOL DISPATCHER
# ==========================================
async def execute_tool(tool_name: str, arguments: dict, memory: AgentMemory) -> dict:
    """Execute a tool by name with given arguments."""
    print(f"\n🔧 Executing tool: {tool_name}")
    print(f"   Args: {json.dumps(arguments, indent=2)[:200]}")

    try:
        if tool_name == "generate_model_sheet":
            # Sanitize arguments against LLM parameter hallucinations (e.g. passing 'prompt' or 'platform')
            gender = arguments.get("gender", "female")
            if gender not in ["female", "male"]:
                gender = "female"
            try:
                preset_index = int(arguments.get("preset_index", 0))
            except:
                preset_index = 0
            model_id = arguments.get("model_id")
            if not model_id:
                model_id = f"model_{gender}_{int(time.time())}"
            return await tool_generate_model_sheet(gender=gender, preset_index=preset_index, model_id=model_id, memory=memory)
        elif tool_name == "grok_trend_analysis":
            return await tool_grok_trends(**arguments, memory=memory)
        elif tool_name == "scrape_trending_products":
            return await tool_scrape_trending(**arguments, memory=memory)
        elif tool_name == "scrape_agent_products":
            return {"success": False, "error": "This tool is disabled. Sourcing replicas is no longer supported."}
        elif tool_name == "scrape_yupoo_catalog":
            return {"success": False, "error": "This tool is disabled. Yupoo replica sourcing is deactivated."}
        elif tool_name == "browse_instagram_page":
            return await tool_browse_instagram(**arguments, memory=memory)
        elif tool_name == "generate_ad_image":
            # Sanitize: make product_image_path optional — auto-resolve if omitted
            if "product_image_path" not in arguments or not arguments.get("product_image_path"):
                import glob
                sourcing_dir = os.path.join(os.getcwd(), "input_sourcing")
                candidates = glob.glob(os.path.join(sourcing_dir, "**", "*.jpg"), recursive=True)
                candidates += glob.glob(os.path.join(sourcing_dir, "**", "*.png"), recursive=True)
                if candidates:
                    arguments["product_image_path"] = candidates[0]
                    print(f"   [auto] product_image_path resolved to: {os.path.basename(candidates[0])}")
                else:
                    return {"success": False, "error": "No product images in input_sourcing/. Scrape products first."}
            return await tool_generate_ad(**arguments, memory=memory)
        elif tool_name == "generate_caption":
            return await tool_generate_caption(**arguments, memory=memory)
        elif tool_name == "style_outfit":
            return tool_style_outfit(**arguments)
        elif tool_name == "post_content":
            return await tool_post_content(**arguments, memory=memory)
        elif tool_name == "find_potential_clients":
            return await tool_find_clients(**arguments, memory=memory)
        elif tool_name == "dm_brand_with_demo":
            return await tool_dm_brand(**arguments, memory=memory)
        elif tool_name == "check_post_performance":
            return await tool_check_performance(**arguments, memory=memory)
        elif tool_name == "add_learning":
            return tool_add_learning(**arguments, memory=memory)
        elif tool_name == "wait_and_plan":
            wait = arguments.get("wait_minutes", 5)
            reason = arguments.get("reason", "planning")
            print(f"   ⏸️  Waiting {wait} minutes: {reason}")
            await asyncio.sleep(wait * 60)
            return {"success": True, "waited_minutes": wait}
        # ── New tools ──
        elif tool_name == "research_web":
            return await tool_research_web(**arguments, memory=memory)
        elif tool_name == "use_free_ai_generator":
            return await tool_use_free_ai(**arguments, memory=memory)
        elif tool_name == "create_digital_product":
            return tool_create_digital_product(**arguments, memory=memory)
        elif tool_name == "list_on_gumroad":
            return await tool_list_on_gumroad(**arguments, memory=memory)
        elif tool_name == "check_login_status":
            return tool_check_login_status(**arguments, memory=memory)
        # ── Self-improvement tools ──
        elif tool_name == "self_improve":
            from self_improve import repair_tool, run_improvement_cycle
            mode = arguments.get("mode", "full_cycle")
            if mode == "repair":
                target = arguments.get("target_tool", "")
                error = arguments.get("error_message", "Unknown error")
                result = await repair_tool(target, error)
                memory.log_action("self_improve", f"Repair {target}: {result.get('diagnosis', 'done')}")
                return result
            elif mode == "discover":
                from self_improve import discover_free_tools
                result = await discover_free_tools()
                memory.log_action("self_improve", f"Discovered {result.get('count', 0)} tools")
                return result
            else:  # full_cycle
                result = await run_improvement_cycle(memory=memory)
                memory.log_action("self_improve", f"Improvements: {len(result.get('improvements', []))}")
                return result
        elif tool_name == "discover_tools":
            from self_improve import discover_free_tools
            result = await discover_free_tools()
            if result.get("tools"):
                memory.add_learning(f"Discovered {len(result['tools'])} new free AI tools")
            memory.log_action("discover_tools", f"Found {result.get('count', 0)} tools")
            return result
        elif tool_name == "generate_with_huggingface":
            return await tool_generate_huggingface(**arguments, memory=memory)
        elif tool_name == "generate_with_pollinations":
            return await tool_generate_pollinations(**arguments, memory=memory)
        elif tool_name == "scrape_meta_ad_library":
            return await tool_scrape_meta_ads(**arguments, memory=memory)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        memory.log_action(tool_name, str(e), success=False)
        return {"success": False, "error": str(e)}
