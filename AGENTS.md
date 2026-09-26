# 🧠 AGENTS.md — OBSCURA AI Fashion Pipeline Master Knowledge File
> **Last Updated:** 2026-07-30
> **Purpose:** This is the single source of truth for the entire project. Any AI agent (Gemini, Claude, Antigravity, Codex) that reads this file should fully understand the project without needing any prior context.

---

## 1. BUSINESS OVERVIEW

**Brand:** OBSCURA — AI-powered luxury fashion content & resale business.

**Business Operations:**
1. **OBSCURA Luxury Fashion Resale:** Source premium blanks and independent designer streetwear from Chinese suppliers (Weidian, 1688, Taobao), generate AI model photos, sell via Next.js storefront.
2. **Standalone AI UGC & Product Ad Agency (`mini_projects/ai_ugc_ad_agency/`):** Completely independent B2B ad agency business. Uses AI image (Flow API) and video models (Veo 3.1) to generate studio product photos, lifestyle model photos, and 9:16 video ad campaigns for external client brands across 10 niches (soap, necklace, wristwatch, bags, clothes, wigs, perfume, skincare, glasses, shoes).

**Aesthetic Standard:** Every image must look like it belongs in Vogue or a Balenciaga campaign. See `FASHION_MANIFESTO.md` for the non-negotiable quality rules.

---

## 2. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│                   SOURCING LAYER                     │
│                                                      │
│  chinese_sourcing_agent.py ← Weidian/1688/Taobao    │
│  yupoo_scraper.py        ← Yupoo album scraper      │
│  competitor_spy.py       ← Competitor monitoring     │
│  tiktok_trend_scraper.py ← TikTok trend mining      │
│  brand_scout.py          ← IG lead generation        │
│  sourcing_utils.py       ← Contact sheet generation  │
│  reverse_search.py       ← Bing reverse image search │
└───────────────┬─────────────────────────────────────┘
                │ products / catalogs → Discord / downloads
                ▼
┌─────────────────────────────────────────────────────┐
│                   REVIEW LAYER                       │
│                                                      │
│  discord_listener.py     ← Discord bot (review UI)   │
│  review_pending/         ← JSON mappings per sheet   │
│  MANUAL_CURATION/        ← Approved HQ images        │
│  color_matcher.py        ← CN→EN color mapping       │
│  auto_image_classifier.py ← VLM image categorization │
└───────────────┬─────────────────────────────────────┘
                │ approved products
                ▼
┌─────────────────────────────────────────────────────┐
│          CLOUD AI GENERATION LAYER (24/7)           │
│                                                      │
│  cloud_generator_gha.py ← Cloud Lookbook Generator  │
│  .github/workflows/obscura_cloud_generator.yml       │
│  generation_router.py   ← Direct Flow API Dispatch  │
│  google_token_manager.py← OAuth 2.0 Rotation Pool   │
│  prompt_library.py      ← Curated prompts/categories│
│  vision_evaluator.py    ← VLM Quality scoring       │
│  scene_director.py      ← Editorial scene planning  │
│  photo_director.py      ← Lighting/camera/pose      │
│  style_tagger.py        ← Auto gender/niche tags    │
│  composite_builder.py   ← 9:16 outfit composites    │
└───────────────┬─────────────────────────────────────┘
                │ generated lookbook images
                ▼
┌─────────────────────────────────────────────────────┐
│               SALES & DISTRIBUTION                   │
│                                                      │
│  store_manager.py        ← Product listing mgmt     │
│  storefront_uploader.py  ← Upload to web store      │
│  social_autoposter.py    ← IG/TikTok auto posting   │
│  order_fulfillment.py    ← Order processing         │
│  pricing_engine.py       ← Dynamic pricing          │
│  lead_hunter.py          ← DM outreach automation   │
│  lead_tracker.py         ← CRM for brand leads      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              CLOUD AUTH & INFRASTRUCTURE            │
│                                                      │
│  Azure VPS (20.215.232.214) ← 24/7 autonomous runner│
│  google_accounts.json    ← Permanent OAuth refresh  │
│  Persistent Profile      ← VPS browser disk profile │
│  litellm_router.py       ← API key rotation/fallback│
│  agent_brain_vps.py      ← VPS orchestration agent  │
│  agent_tools_vps.py      ← VPS tool definitions     │
│  agent_memory.py         ← Persistent agent memory  │
│  .env                    ← API keys & configurations│
└─────────────────────────────────────────────────────┘
```

---

## 3. CRITICAL FILE MAP

### 📦 Sourcing
| File | Purpose | Status |
|------|---------|--------|
| `chinese_sourcing_agent.py` | Primary Weidian/1688/Taobao scraper using Playwright/Stealth. Extracts prices, variants, sizes, images. | **ACTIVE — CORE** |
| `yupoo_scraper.py` | Yupoo album scraper for HQ uncensored product photos. | **ACTIVE — CORE** |
| `brand_scout.py` | Searches Instagram for small brands with bad content → generates pitch DMs. "Agency Mode". | **ACTIVE** |
| `competitor_spy.py` | Monitors competitor stores and pricing via Bing Visual Search. | **ACTIVE** |
| `tiktok_trend_scraper.py` | Scrapes TikTok for trending fashion products/hashtags. | **ACTIVE** |
| `meta_ad_scraper.py` | Scrapes Meta Ad Library for competitor ad creatives. | **ACTIVE** |
| `sourcing_utils.py` | Contact sheet generation, image grouping, dedup utilities. | **ACTIVE** |
| `reverse_search.py` | Bing Visual Search stealth reverse image lookup for finding Chinese suppliers. | **ACTIVE** |
| `color_matcher.py` | Maps VLM-detected color names to Chinese Weidian variant text. | **ACTIVE** |

### 👕 Outfit & Fulfillment
| File | Purpose | Status |
|------|---------|--------|
| `outfit_warehouse.py` | Warehouse staging manifest for outfit assembly (tops + bottoms + shoes). | **ACTIVE** |
| `auto_matcher.py` | 24/7 VPS outfit matching service. Scans MANUAL_CURATION for style tags, pairs items. | **ACTIVE** |
| `auto_stock_sync.py` | Automated stock sync between Weidian and storefront catalog. | **ACTIVE** |
| `auto_fulfillment.py` | Automated order fulfillment and DDP agent dispatch. | **ACTIVE** |
| `start_engine.py` | CLI Control Center launcher — menu for all pipeline operations. | **ACTIVE** |

### 🤖 Discord Bot
| File | Purpose | Status |
|------|---------|--------|
| `discord_listener.py` | Full Discord bot. Handles: manual drops (images + link), contact sheet replies, Weidian/1688/Taobao direct link scraping, natural language chat via Gemini. | **ACTIVE — CORE** |

### 🎨 Generation
| File | Purpose | Status |
|------|---------|--------|
| `cloud_generator_gha.py` | Primary Autonomous Cloud Generation worker for GitHub Actions (16GB RAM) and Azure VPS. Manages Flow execution, Pillow 9:16/1:1 formatting, and UGC brief creation. | **ACTIVE — CORE** |
| `generation_router.py` | API dispatch engine. Handles Flow image/video generation, token refresh, OAuth key rotation. | **ACTIVE — CORE** |
| `test_complete_generation_cycle.py` | Standalone VPS script for uploading flat lay garments as Flow ingredients and generating editorial looks. | **ACTIVE — CORE** |
| `google_token_manager.py` | Permanent Google OAuth 2.0 refresh token rotation pool across 4 accounts. Zero login expiration. | **ACTIVE — CORE** |
| `scene_director.py` | Plans scenes, locations, lighting for AI photoshoots. | **ACTIVE** |
| `photo_director.py` | Camera angles, poses, composition planning. | **ACTIVE** |
| `prompt_library.py` | 90KB of curated prompts for different product types, scenes, styles. | **ACTIVE — CORE** |
| `vision_evaluator.py` | VLM-based quality scoring of generated images. | **ACTIVE** |
| `style_tagger.py` | Auto-tags products with gender, niche, category, scene using Gemini Vision. | **ACTIVE** |
| `carousel_builder.py` | Builds multi-image carousels for social media. | **ACTIVE** |
| `composite_builder.py` | Assembles vertical 9:16 composite flat lays (top + bottom + shoes). | **ACTIVE** |
| `auto_image_classifier.py` | VLM image classification: front/back/detail/size_chart/model_shot. | **ACTIVE** |
| `meta_ai_video_worker.py` | AI video generation worker for Meta AI / Flow video pipeline. | **ACTIVE** |

### 🧠 Brain / Infrastructure
| File | Purpose | Status |
|------|---------|--------|
| `litellm_router.py` | **Critical.** Manages ALL API key rotation. Uses LiteLLM Router with latency-based routing and automatic fallback cascading. | **ACTIVE — CORE** |
| `google_accounts.json` | Permanent OAuth 2.0 refresh tokens for 4 Google accounts. Eliminates web session expiration. | **ACTIVE — CORE** |
| `.github/workflows/obscura_cloud_generator.yml` | 100% Free GitHub Actions workflow running lookbook generation every 4 hours autonomously. | **ACTIVE — CORE** |
| `agent_brain_vps.py` | VPS orchestration agent (24/7 server version). | **ACTIVE** |
| `agent_tools_vps.py` | VPS version of agent tools (90KB). | **ACTIVE** |
| `agent_memory.py` | Persistent agent memory using SQLite + JSON. | **ACTIVE** |
| `utils.py` | Shared utilities including `safe_print()` for Windows cp1252 safety. | **ACTIVE** |

### 🏪 Storefront
| Directory | Purpose |
|-----------|---------|
| `../storefront/` | Next.js web store for displaying and selling products. |

---

## 4. KEY DIRECTORIES

| Directory | Purpose |
|-----------|---------|
| `input_sourcing/` | Staging area for thumbnails and contact sheets (temporary). |
| `review_pending/` | JSON files mapping contact sheet message IDs → image URL maps. **This is the dedup source.** |
| `MANUAL_CURATION/` | Approved products with HQ images + metadata.json. Ready for AI generation. |
| `OUTPUT_READY_FOR_SALE/` | Final generated images ready for store upload. |
| `data/` | Persistent data: `reddit_discovered_sellers.json`, `brain_sqlite.db`. |
| `models/` | Model roster character sheets (`f1_1.jpg`, `m1_1.jpg`) for AI generation references. |
| `flow_extension/` | Chrome extension source code for token harvesting from Google Flow. |
| `mini_projects/` | Self-contained side projects separated from core pipeline (KDP, UGC, lookbook PDF, lead scrapers). |
| `_archive/` | Archived old code: `legacy/` (superseded scripts), `login_scripts/` (deprecated), `tests/` (debug scripts). |
| `_TRASH_CLEANUP_2026/` | Files scheduled for deletion. |

---

## 5. API KEYS & LLM CONFIGURATION

### Current API Keys (.env)
| Provider | Key Env Var | Free Tier | Used For |
|----------|------------|-----------|----------|
| **Google Gemini** | `GEMINI_API_KEY` through `_7` (7 keys) | 10-15 RPM per project, ~1500 RPD | Discord bot brain, style tagging, VLM evaluation |
| **Groq** | `GROQ_API_KEY` | 30 RPM, varies by model | Fast inference fallback |
| **NVIDIA NIM** | `NVIDIA_API_KEY` | 40 RPM | Vision model (Llama 3.2 11B Vision) |
| **OpenRouter** | `OPENROUTER_API_KEY` | Some models free | Fallback routing |
| **xAI Grok** | `XAI_API_KEY` | Free credits | Not yet integrated |
| **DeepSeek** | `DEEPSEEK_API_KEY` | 5M tokens on signup | Coding/reasoning tasks |
| **Supabase** | `SUPABASE_URL` + `_KEY` | Free tier | Database & auth |

### ⚠️ CRITICAL: Gemini Rate Limits
- **Limits are PER PROJECT, not per key.** Having 7 keys in the same project does NOT multiply your quota.
- **To actually multiply limits:** Create SEPARATE Google Cloud projects, each with its own key.
- The `litellm_router.py` cascading fallback order is: `gemini-flash → gemini-lite → groq-llama-70b → nvidia-nemotron → openrouter-gemini-free → nvidia-llama-maverick → groq-llama-8b`

### Recommended Additional Free APIs (NOT YET ADDED)
| Provider | URL | Free Tier | Notes |
|----------|-----|-----------|-------|
| **Cerebras** | cloud.cerebras.ai | 1M tokens/day, 30 RPM, no CC | Extremely fast inference. Add ASAP. |
| **SambaNova** | cloud.sambanova.ai | $5 starting credits | Credits expire in 30-90 days |
| **Fireworks AI** | fireworks.ai | ~$1 trial credits | Fast open-weight models |

---

## 6. YUPOO SOURCING — HOW IT WORKS

### ⚠️ CRITICAL: IMAGE SOURCE RULE (NON-NEGOTIABLE)
- **Product images for AI generation MUST ALWAYS come from YUPOO**, never from Weidian, Taobao, or 1688.
- **Why:** Yupoo is where replica sellers post their HIGH-RESOLUTION, UNCENSORED product photos with brand names, logos, and details clearly visible. This is the entire purpose of Yupoo for these sellers.
- **Weidian/Taobao/1688 listings almost always BLUR OUT brand names and logos** to avoid platform takedowns and copyright enforcement. 9 out of 10 marketplace listings have censored images.
- **Marketplace links (Weidian/Taobao/1688) are ONLY used for:** pricing, sizing/variants, color options, and placing orders. NEVER for sourcing product images.
- **Pipeline rule:** The scraper must download product images from the Yupoo album page. The marketplace link extracted from the Yupoo album description is saved as metadata for ordering only.

### Yupoo Structure (CRITICAL TO UNDERSTAND)
```
Seller (subdomain.x.yupoo.com)
  └── Categories (e.g., /categories/4644452)
        └── Albums (individual product pages)
              └── Images (thumbnails + HQ originals)  ← THIS IS THE IMAGE SOURCE
```

**IMPORTANT:** A single Yupoo ALBUM can contain MULTIPLE product types/categories. For example, one album might show a hoodie, matching pants, and accessories all together. The scraper must handle this — it should NOT assume 1 album = 1 product category.

### Current Seller List
Stored in `data/yupoo_sellers.json`. 15 trusted sellers across: Clothing (Taurus, TopAcney, 3Madman, Goat, Kobe Factory, FOG Store, Allsole, Shark Breeder, CNFashion, DDShop, TopHat), Shoes (WWTOP), Bags (BagKing), Watches (WatchRep), Accessories (LuxuryGoods).

### Reddit-Discovered Sellers
Stored in `data/reddit_discovered_sellers.json`. The Reddit scout runs before each scraping session and discovers new Yupoo subdomains from r/FashionReps, r/DesignerReps, r/RepLadies, r/QualityReps, r/Repsneakers.

---

## 7. DISCORD BOT — HOW IT WORKS

**Bot Token:** In `.env` as `DISCORD_TOKEN`
**Review Channel:** `DISCORD_REVIEW_CHANNEL`

### Message Formats
```
📦 SINGLE DROP:     [images] Product Name | Color | ¥price | link
🎨 MULTI-COLOR:    Send each colour as a separate message (or reply to contact sheet with: colours: black, white)
👕👖 SETS:          Include "set" or "tracksuit" in the name
📏 SIZE CHART:      Name file "size.jpg" or add "size: 8" to reply
📋 CONTACT SHEET:   Reply with "2, 5, 12" or "all"
🔗 MARKETPLACE LINK: Paste a Weidian, 1688, or Taobao link → auto-scrape & rich embed
💬 CHAT:            Any plain text → routed to Gemini brain
```

### Flow
1. Scraper sends contact sheet to Discord with product info (or pasting a Weidian/1688/Taobao link auto-triggers a rich embed and contact sheet)
2. User replies with image numbers (e.g., "2, 5, 12")
3. Bot downloads only those HQ images
4. Images saved to `MANUAL_CURATION/` with metadata.json (supports separate folder generation per color variant if colours specified)
5. Generation worker picks up the product and creates AI photos

---

## 7.1 COMPLETE PIPELINE FLOW (END-TO-END)

This section traces the exact data flow from a product link to a live storefront listing.

### Step 1: Product Entry (Discord)
```
User pastes Weidian/1688/Taobao link in Discord
        │
        ▼
discord_listener.py → on_message()
        │
        ├─ parse_item_id() — extract platform item ID
        ├─ is_imported() — check review_pending/ + MANUAL_CURATION/ for duplicates
        ├─ ChineseSourcingAgent.scrape_product() — Playwright stealth scrape
        │    └─ Extracts: title, price_cny, sizes, colors (Chinese), images
        ├─ classify_images_by_color() — VLM groups images by color variant
        └─ create_color_grouped_contact_sheets() — visual grid per color
                │
                ▼
        Discord embeds: Main Product Card + per-color Contact Sheets
        Interactive UI: Front/Back/Detail dropdown selectors + Confirm Pick button
```

### Step 2: Image Approval (Discord)
```
User selects images via dropdowns → clicks "Confirm Pick"
        │
        ▼
ColorPickView / ProductCardView → save_pending()
        │
        ├─ Downloads selected HQ images from source
        ├─ Creates folder: MANUAL_CURATION/<title>_<color>_<timestamp>_<uuid>/
        ├─ Saves images as: front_angle_1.jpg, back_angle_1.jpg, angle_3.jpg, size.jpg
        ├─ Writes metadata.json (see schema below)
        ├─ Stages front image to outfit_warehouse.py for outfit assembly
        └─ Updates Discord card → GREEN "Picked & Saved" with image breakdown
```

### Step 3: AI Generation (Autonomous Cloud — GHA 16GB Runner & Azure VPS)
```
cloud_generator_gha.py / VPS runner → autonomous cloud execution (Zero PC Dependency)
        │
        ├─ Discovers pending products from queue_pending.json or MANUAL_CURATION/
        ├─ Synthesizes editorial multi-category prompts & 10s Omni Flash UGC video briefs
        ├─ Flow Reference Execution:
        │    ├─ Option A: Direct API via google_token_manager.py ya29 OAuth rotation
        │    └─ Option B: Cloud Playwright (xvfb-run) via persistent VPS profile
        │         └─ Uploads scraped flat lay front angle as media ingredient
        │         └─ Adds ingredient to prompt + enters editorial styling prompt
        ├─ Generates certified lookbooks with Nano Banana Pro (GEM_PIX_2)
        ├─ Pillow Post-Processing: True 9:16 Vertical (TikTok/Reels) & 1:1 Square (IG)
        └─ vision_evaluator.py — quality scores output before acceptance
                │
                ▼
        OUTPUT_READY_FOR_SALE/<product_slug>/
            ├─ tiktok_9_16_1.webp (Certified 9:16 vertical)
            ├─ ig_feed_post_1.webp (Certified 1:1 square)
            ├─ ugc_video_brief.json (Omni Flash 10s UGC script)
            ├─ campaign_info.json (Complete drop metadata)
            ├─ front_angle.jpg (source flat lay)
            └─ back_angle.jpg (source flat lay)
```

### Step 4: Storefront Upload (Local PC)
```
storefront_uploader.py → scan_and_upload()
        │
        ├─ Scans OUTPUT_READY_FOR_SALE/ for completed campaigns
        ├─ Copies images to storefront/public/products/<product_slug>/
        ├─ Strips ALL supplier URLs, Chinese prices, pipeline names (Rule 16)
        ├─ Stores private data in supplier_mappings.json (Rule 17)
        ├─ Builds storefront/src/data/products.js
        └─ Logs to uploaded_campaigns.json (prevents re-upload)
```

### metadata.json Schema
```json
{
  "product_name": "Obsidian Heritage Track Jacket",
  "color": "black",
  "item_id": "7817897798",
  "platform": "weidian",
  "link": "https://weidian.com/item.html?itemID=7817897798",
  "price_cny": 158.0,
  "colors": ["Khaki", "Green", "Black", "Beige"],
  "sizes": ["S", "M", "L", "XL", "2XL"],
  "variant_mappings": {
    "colors": { "Black": "Black color-blocking KC 3115" },
    "sizes": { "S": "S", "M": "M" }
  },
  "selected_indices": { "front": [1, 2], "back": [], "detail": [3, 4] },
  "product_category": "jacket",
  "seller": { "name": "seller_name", "shipping_origin": "Guangzhou", "domestic_shipping_cny": 10.0 },
  "generation_status": "pending",
  "storefront_status": "not_listed"
}
```

### Key Data Files
| File | Purpose |
|------|---------|
| `review_pending/*.json` | Active Discord review state. Maps message IDs → scraped image URLs + VLM groups + pending picks. Dedup source. |
| `supplier_mappings.json` | **STRICTLY PRIVATE.** Maps public product IDs → Chinese supplier URLs, RMB costs, Chinese variant names for procurement. |
| `uploaded_campaigns.json` | Tracks all campaigns successfully published to storefront. Prevents duplicate listings. |

---

## 7.2 OBSCURA ORGANIC UGC VIDEO AD STRATEGY (NON-NEGOTIABLE)

### 📌 Core Principle: Zero-Budget Organic Conversion
- **Paid Ads Policy:** Zero budget allocated for paid ads initially. We rely 100% on high-converting **organic social reach** across **TikTok, Instagram Reels, Pinterest Watch/Idea Pins, and YouTube Shorts** until revenue is generated.

### 🎥 Video Engine Engine: Omni Flash on Google Flow (NOT Veo 3.1)
- **Model Engine:** **`Omni Flash`** on Google Flow (`veo_3_1_i2v_lite` / `flow_omni`).
- **Generation Duration:** Exactly **10 seconds** per video generation (`10s video length`).
- **Native Audio & Speech Generation:** **Omni Flash generates native audio & synchronized speech** directly inside the 10-second video generation payload!

### 🤳 High-Converting Organic "Selfie UGC / Fit Check" Ad Formula
- **Concept:** AI Fashion Model holding the phone front-camera / mirror selfie style, wearing the OBSCURA product (hoodie, jacket, tee, cargo pants).
- **Format:** Authentic 9:16 vertical front-facing selfie video that feels like a real fashion influencer or TikToker doing a fit check.
- **Speech / Script Formula (10 Seconds Native Speech):**
  - *"Look at this top I got from OBSCURA..."*
  - *"Stop buying overpriced blank hoodies. OBSCURA just dropped this 500GSM vintage grey fit..."*
  - Shows close-up detail, fabric drape, and turns 360° to highlight the quality in 10 seconds.
- **CTA:** "Link in bio to shop the drop."

---

## 7.3 DUAL-TRACK GENERATION SYSTEM (NON-NEGOTIABLE)

### Architecture: Two Parallel Generation Paths

The generation worker (`local_generation_worker.py`) runs two tracks simultaneously:

#### Track 1: Singular Item Generation (ANY individual product)
Every individual product (hoodie, pants, sneakers, etc.) receives:
1. **Product-only shots** (ghost mannequin, flat lay, detail) — for storefront product pages
2. **1 on-model editorial photo** — model wearing just that item with neutral styling (`CLOTHING_PROMPTS` / `MALE_UGC_PROMPTS`)
3. **1 Omni Flash 10s UGC selfie video** — organic TikTok/Reels ad (`OBSCURA_SELFIE_UGC_AD_PROMPTS`)
- Items are also **staged** in `outfit_warehouse.py` for Track 2 matching

#### Track 2: Full Outfit Generation (warehouse-matched sets)
When `outfit_warehouse.py` matches a **top + bottom** (same brand, compatible color):
1. **3 on-model outfit shots** — full look editorial photography
2. **1 outfit transition UGC video** — Omni Flash 10s video showing the complete outfit
3. **1 composite flat lay** — vertically stacked top + bottom + shoes image

### ⚠️ RULE: Singular items DO get on-model shots now
- **Previous rule (DEPRECATED):** "On-model is ONLY for curated outfits via generate_outfit_shots()"
- **Current rule:** Individual items get 1 on-model shot + 1 UGC video. Full outfits get 3 on-model shots + 1 outfit video.

### Generation Router: Omni Flash Video Model
- `generation_router.py` `generate_video()` now accepts `video_model="omni_flash"` parameter
- Maps to Flow API model keys: `flow_omni_i2v` (image-to-video) or `flow_omni_t2v` (text-to-video)
- Default (`video_model="veo"`) still uses `veo_3_1_i2v_lite` / `veo_3_1_t2v_lite`

### Social Media Posting Cadence (Zero-Budget Organic)
| Platform | Content | Frequency |
|----------|---------|-----------|
| TikTok | 10s UGC selfie videos | 2-3x/day |
| Instagram Reels | Same videos + carousel product shots | 2x/day |
| Pinterest Watch | 10s videos as Watch Pins | 1x/day |
| YouTube Shorts | Same 10s videos | 1x/day |



## 8. KNOWN BUGS & ISSUES

### 🟢 FIXED: Reverse Image Search Pipeline (June 2026)
- **Problem:** Google Lens direct uploading and URL requests were completely blocked by CAPTCHAs/429 errors. Direct HTTP calls to Bing Visual Search did not return results because they load dynamically via JavaScript.
- **Solution:** Refactored `reverse_search.py` and `competitor_spy.py` to use `reverse_search_bing_stealth()`. This leverages Playwright + Stealth to navigate to Bing Visual Search, upload product images, wait for dynamic results, and scrape matching Chinese suppliers (1688, Taobao, Weidian, AliExpress). Google Lens and basic HTTP Bing calls are kept only as disabled/deprecated fallbacks.

### 🟢 FIXED: Video Download Pipeline — Phase 3 Discovery (July 2026)
- **Problem:** Video generation succeeded on Google's servers (`MEDIA_GENERATION_STATUS_SUCCESSFUL`, credits deducted), but the router could never retrieve the actual video file. The code searched the status poll response for `googleusercontent.com` download URLs, but the status endpoint **NEVER returns video download URLs** (unlike images which return `fifeUrl` inline).
- **Root Cause:** Google Flow's Video API uses a **3-phase async model**. The router only had Phase 1 (Submit) and Phase 2 (Poll). Phase 3 (Fetch) was completely missing.
- **Solution:** After status confirms `MEDIA_GENERATION_STATUS_SUCCESSFUL`, call `GET https://aisandbox-pa.googleapis.com/v1/media/{media_name}` which returns the video as **base64-encoded JSON** in `video.encodedVideo`. Decode with `base64.b64decode()` → valid MP4 file. Fixed in `generation_router.py` → `_generate_flow_video_api()`.
- **Key Difference (Image vs Video):**
  - **Images:** Synchronous. One POST → response contains `fifeUrl` download links immediately.
  - **Videos:** Async 3-phase. Submit → Poll → Fetch (separate GET endpoint returning base64).

### 🟡 BUG: API Rate Limits on Discord Bot
**Symptom:** Bot replies with "Brain is temporarily overloaded" frequently.
**Root Cause:** All 7 Gemini API keys are in the SAME Google Cloud project, so they share a single 10-15 RPM quota.
**Fix Required:** Create separate GCP projects for separate keys, OR add Cerebras/SambaNova as additional free providers.

### 🔴 REMOVED: brand_website_sourcer.py
This file was removed from the codebase. Brand website scraping should be reimplemented if needed.

### 🟢 FIXED: Dead vlm_product_sourcer Import (July 2026)
- **Problem:** `local_generation_worker.py` line 1234 imported `from vlm_product_sourcer import VLMSourcer, SELLERS`, but `vlm_product_sourcer.py` was archived when replica sourcing was removed. This caused `ModuleNotFoundError` caught by a broad `except Exception`, making the worker silently loop every 60 seconds doing nothing.
- **Solution:** Replaced the dead import block with a clean idle wait that logs clearly and waits 120s for new products to appear via the Discord pipeline.

---

## 9. BRAND TARGETS (CHINESE BRANDS / CJ DROPSHIPPING)

These are the legitimate Chinese wholesale, blanks, and original streetwear designer brands we source from (primarily via CJ Dropshipping and Buying Agents) rather than Western fast fashion:

### Sourcing Platforms
- **Alibaba DDP Agents (Primary for Replicas & Africa Resale):** Direct shipping/shopping agents found on Alibaba. They handle the purchasing of replica products and ship to Africa via DDP (Delivered Duty Paid) air cargo, which includes all customs, taxes, and domestic shipping. Replicas are strictly prohibited on standard dropshipping platforms like CJ.
- **BuckyDrop**: buckydrop.com (For legal pipeline: direct Shopify App integration for 1688, Taobao, and Weidian)
- **CJ Dropshipping**: cjdropshipping.com (For legal pipeline: direct automated dropshipping, supports custom requests)
- **1688**: Direct manufacturers for unbranded heavyweight basics (tees, hoodies, cargo pants)

### Brand & Manufacturer Targets
- **Aesthetic OEM Blanks (IDLT)**: High-end washed vintage Y2K blanks.
- **Studio Blanks (PYC)**: Premium heavyweight drop shoulder blanks.
- **UnionKingdom Basics**: Premium vintage heavyweight basics.
- **Artie Master Blanks**: Heavyweight drop shoulder blanks.
- **ROARINGWILD**: Hypebeast urban techwear.
- **Randomevent**: 90s cargo fleece vintage style.
- **SoulGoods**: Beijing-based heritage streetwear.
- **CLOT**: East-meets-west hype fashion.
- **Li-Ning / ANTA**: Chinese sports street heritage.
- **BJHG (不即胡同)**: Gen-Z trendy retro streetwear, graphic tees, and cargo pants.
- **UMAMIISM**: Futuristic minimalist and military-inspired deconstructed outerwear.
- **FMACM**: Contemporary sportswear and youth-culture streetwear.
- **WHOOSIS**: Skatewear, cozy hoodies, work jackets.
- **Maden Vintage**: Rugged heritage workwear and military fatigue blanks.
- **ATTEMPT**: Deconstructed architectural minimalist streetwear.
- **Simple Project**: Minimalist draping, wide-leg structured trousers, clean tailoring.
- **Common Divisor**: Archival darkwear and drapery silhouettes.
- **ENSHADOWER**: Techwear, tracksuits, functional cargo pants.
- **MEDM (Mr. Enjoy Da Money)**: Hiphop culture varsity graphics and bold street prints.

### Goal
Extract flat-lay and ghost mannequin imagery from these Chinese suppliers so we can run them through the AI model generation pipeline to create premium, Western-style editorial lookbooks.

---

## 10. GEMINI CLI & AUTOMATION TOOLS

### Gemini CLI (being replaced by Antigravity CLI June 18, 2026)
- Install: `npm install -g @google/gemini-cli`
- Can run headless/non-interactive with `--output-format json`
- Supports MCP (Model Context Protocol) servers
- Can be used in CI/CD pipelines for automated tasks
- Has 1M token context window — can read entire project
- **Use case for us:** Could run overnight autonomous scraping/generation tasks

### Antigravity CLI (Successor)
- Built in Go, faster execution
- Multi-agent workflows with skills, hooks, subagents, plugins
- Already the platform we're on in the IDE

### Verdict
For our use case, the **LiteLLM Router + Python scripts** approach is more powerful and flexible than the Gemini CLI. The CLI is better for developer workflows (code review, refactoring). Our pipeline benefits more from direct API access with key rotation.

---

## 11. DEPLOYMENT & AUTONOMOUS CLOUD ARCHITECTURE (ZERO PC DEPENDENCY)

### Infrastructure Diagram
```
┌────────────────────────────────────────────────────────┐
│             AZURE VPS (20.215.232.214)                 │
│             Ubuntu 22.04 LTS — 24/7 Autonomous Uptime  │
│                                                        │
│  Systemd Services / Background daemons:                │
│    → discord_listener.py (Sourcing & Discord bot)      │
│    → auto_matcher.py --watch (Outfit pairing)          │
│    → cloud_generator_gha.py (xvfb-run headless gen)    │
│                                                        │
│  Autonomous Generation:                                │
│    → Scans queue_pending.json & MANUAL_CURATION/       │
│    → References exact scraped garment via Flow         │
│    → Generates 9:16 and 1:1 certified lookbooks        │
│    → Outputs directly to OUTPUT_READY_FOR_SALE/        │
└──────────────────────────┬─────────────────────────────┘
                           │
             Autonomous Git Sync & Scheduled Cron
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│        GITHUB ACTIONS RUNNER (16GB RAM CLOUD)          │
│        .github/workflows/obscura_cloud_generator.yml   │
│                                                        │
│  Cron Execution: Every 4 hours (0 */4 * * *)           │
│    → 100% free, 16GB RAM, headless Ubuntu              │
│    → Runs cloud_generator_gha.py                       │
│    → Commits generated outputs & updates queue         │
└────────────────────────────────────────────────────────┘
```

### 100% Autonomous Execution — Zero PC Dependency
- **Local PC is NEVER required:** The user's home computer does NOT need to be turned on, awake, or running any scripts.
- **No Local Bridges or Extensions:** Sourcing, curation, image referencing, AI lookbook synthesis, UGC briefs, and storefront catalog creation happen 100% in the cloud.
- **Persistent Disk Queues:** All products in `review_pending/` and `MANUAL_CURATION/` persist safely in cloud storage and git.

### Azure VPS Access Details
- **IP:** `20.215.232.214`
- **User:** `azureuser`
- **SSH Key:** `~/.ssh/azure_obscura_key.pem`
- **Directory:** `/home/azureuser/ai-ugc/`
- **Python Virtualenv:** `/home/azureuser/ai-ugc/venv/bin/python3`

---

## 12. RULES (NON-NEGOTIABLE)

1. **NEVER generate AI images without real scraped source photos.** No placeholders.
2. **NEVER post to socials without human review.** Everything goes to `review_pending` first.
3. **NEVER hardcode API keys in source files.** Always use `.env`.
4. **ALWAYS preserve existing comments and docstrings** when editing code.
5. **ALWAYS use `safe_print()` on Windows** to avoid UnicodeEncodeError on cp1252.
6. **Scraper dedup MUST be permanent** — never delete history files.
7. **Brand catalogs can contain multiple product categories** — don't assume 1 catalog page = 1 type.
8. **Gender matching is STRICT** — male products on male models, female on female. No exceptions.
9. **Image quality: AI-generated images must be RAW PNG, minimum 1024x1024.** Source flat lay images (downloaded from Yupoo) may be in their original format (JPG/PNG/WebP), minimum 800px on shortest side. Both AI PNGs and source JPGs appear together in the storefront gallery.
10. **Keep the aesthetic elite** — every image must look editorial, not amateur.
11. **ALWAYS use `Nano Banana Pro` (`GEM_PIX_2`) for images and `Veo 3.1 - Lite` for videos on Google Flow.**
12. **Double check the multiplier for video generation to avoid burning credits (Veo 3.1 Lite costs 10 credits per video base, while Omni Flash costs 15 credits for 10s).**
13. **100% AUTONOMOUS CLOUD EXECUTION (ZERO LOCAL PC DEPENDENCY).** The AI generation pipeline MUST run fully autonomously in the cloud (via GitHub Actions 16GB runner `.github/workflows/obscura_cloud_generator.yml` or Azure VPS headless `xvfb-run`). The USER's personal local computer must NEVER be required to stay turned on for generation or pipeline operations. All Google Flow generation runs headlessly in the cloud using the authenticated session (`session_google_account.json` / `GFLOW` secret).
14. **Video downloads use Phase 3 (base64 decode), NOT URL scraping.** After poll shows `SUCCESSFUL`, call `GET v1/media/{name}` → decode `video.encodedVideo` from base64. NEVER search poll responses for download URLs — they don't exist for videos.
15. **PRIMARY ASPECT RATIO IS STRICTLY 9:16 (PORTRAIT)** for all image and video generation. All marketing & UGC content is optimized for TikTok, Instagram Reels, and Instagram Stories.
16. **NEVER expose supplier links in public storefront catalogs.** The storefront uploader must hide all `supplierLink` references from public files to protect source confidentiality.
17. **ALWAYS maintain a private `supplier_mappings.json` file** to store original Chinese marketplace URLs, costs, and variant mappings (colors/sizes translated from English to Chinese).
18. **ALWAYS reverse-map customer options back to Chinese** when processing orders for procurement. The DDP agent needs the exact Chinese option text (e.g. `黑色`, `XL码`) to purchase the correct items.
19. **REPLICAS REQUIRE DDP AGENTS FOR AFRICA SHIPMENTS.** Do not use Kakobuy, Superbuy, or CJ Dropshipping for replica orders due to high shipping costs and replica bans. Only use Alibaba DDP agents.
20. **PRODUCT IMAGES FOR AI GENERATION MUST ALWAYS COME FROM YUPOO, NEVER FROM WEIDIAN/TAOBAO/1688.** Marketplace listings blur out brand names and logos to avoid takedowns (9 out of 10 have censored images). Yupoo is where sellers post uncensored, high-resolution product photos. Marketplace links are ONLY for pricing, sizing, and ordering.
21. **DOWNLOAD ALL YUPOO IMAGES EXCEPT MODEL SHOTS.** Do NOT cap or prune the number of images. The VLM classifier deletes ONLY `model_shot` and `lifestyle` images (photos showing a human wearing the garment). ALL other images are kept: product flat lays, detail closeups, tag labels, size charts, packaging. Front/back product shots are used for AI ad generation; detail/tag/size chart images are displayed in the storefront "Photos" subcategory for customers browsing.
22. **MULTI-COLOR PRODUCTS: GROUP IMAGES BY DETECTED COLOR.** When the VLM detects multiple colors in a product's images, it groups them by color variant (e.g., `black`, `cream`, `olive`). Each color group gets its own front/back for separate AI ad generation. Size charts, packaging, and color swatches are shared across all colors.
23. **DOWNLOADED SOURCE PHOTOS ARE THE FLAT LAYS.** Do NOT use Flow API to generate flat lay, ghost mannequin, or detail shots. The downloaded front/back product photos from Yupoo ARE the flat lays displayed in the storefront gallery. Flow API is used ONLY for generating on-model outfit shots.
24. **INDIVIDUAL ITEMS (tops, bottoms, single clothing) get ZERO AI generation.** Their gallery consists entirely of the downloaded source photos: front flat lay + back flat lay. No Flow API calls. No credits burned.
25. **FULL OUTFIT MODEL SHOTS are the ONLY AI generation.** When a complete outfit is assembled (top + bottom + shoe), a single Flow API model shot is generated showing all items on one model, facing the camera. This is the only time Flow API is called for product imagery.
26. **FRONT IMAGES GO TO THE WAREHOUSE for outfit assembly.** After downloading front/back images for individual items, the front images are staged in the warehouse. The warehouse merges matching top fronts + bottom fronts + shoe fronts into combined outfit groups. The combined outfit then gets ONE full-body model shot generated via Flow.
27. **GALLERY IMAGE ORDER: Model shot → Front flat lay → Back flat lay → Other source images.** AI-generated model shots (if any) appear first, followed by the front and back flat lay source photos. All other downloaded images (details, tags, size charts) appear LAST after the primary gallery images.
28. **WEIDIAN/MARKETPLACE COLOR & PRICE EXTRACTION IS MANDATORY (TOP PRIORITY).** We are merging Yupoo (HQ uncensored photos) and Weidian (supplier prices, translated color variants, sizing, stock levels) for every product in our store. Weidian color option and price extraction MUST succeed regardless of how long Playwright takes. NEVER abort, skip, or timeout Weidian variant/price extraction.
29. **GRAND ARCHITECTURAL PURPOSE: MERGING YUPOO + WEIDIAN.** Yupoo provides the visual asset layer (unedited, uncensored HQ studio photos for AI lookbooks and storefront galleries). Weidian provides the operational data layer (supplier cost, Chinese variant mapping, inventory, ordering endpoints). Every curated item MUST merge both sources into a unified product record.
30. **FOR SETS (hoodie + trousers): Generate ONE full outfit model shot with shoes.** The model shot shows all 3 items (top + bottom + shoe) on one model. Individual front/back flat lays for each piece (top front, top back, bottom front, bottom back) follow in the gallery. This produces the richest product page: 1 model shot + 4 flat lays per color.
31. **WEIDIAN COLOR SELECTOR IS THE SOURCE OF TRUTH FOR AVAILABLE COLORS.** Step 1: Scrape the Weidian product page's option drawer to discover all available color variants (e.g., 黑色/Black, 蓝色/Blue, 军绿/Army Green). This gives the definitive list of colors the seller stocks. Step 2: Match/group the downloaded Yupoo source images to those Weidian colors using the VLM classifier. Each color variant gets its own front/back flat lay pair in the gallery and its own color swatch on the storefront. Colors are stored in `product_record.json` → `variants.colors[]` with both Chinese (`chinese`) and English (`english`) names.
32. **COLOR DIFFERENTIATION IS CRITICAL FOR THE STOREFRONT.** Every color variant MUST have its own distinct gallery (front flat lay + back flat lay at minimum). Customers must be able to click a color swatch and see the ACTUAL product in that specific color — not the same images across all swatches. If images for a specific color are missing, that color swatch must NOT appear on the storefront.
33. **AUTO-WAREHOUSE STAGING ON PICK.** When a user confirms an image pick in Discord, the front image is IMMEDIATELY staged to the outfit warehouse (`outfit_warehouse.py`). The discord bot does NOT wait for the generation worker. This enables instant outfit assembly detection — as soon as a matching top + bottom exist, Discord notifies the user.
34. **PRODUCT COMPLETION SUMMARY.** When ALL color cards for a product have been confirmed or skipped, Discord posts a summary card showing: each color's status (confirmed/skipped), image counts per color, price estimate, and warehouse staging status. This is the user's confirmation that the product is fully processed.
35. **COMPOSITE FLAT LAYS.** When an outfit is generated (top + bottom + optional shoe), `composite_builder.py` creates a single 9:16 portrait image stacking all flat lays vertically. This composite image appears in the storefront gallery alongside the individual flat lays and model shot.
36. **NEVER SUGGEST OR FALL BACK TO STANDARD TEXT-TO-IMAGE APIS (NON-NEGOTIABLE).** Generic text-to-image APIs (OpenAI DALL-E, Gemini Imagen, Flux, Midjourney) CANNOT perform garment image referencing — they cannot place the exact scraped product flat lay onto the specific brand model's face and body. Google Flow (`Nano Banana Pro` / `GEM_PIX_2`) with its multi-image reference inputs is the ONLY permitted generation engine. Never suggest API fallbacks that lack real image referencing.


---

### 12.1 IMAGE GENERATION PIPELINE ARCHITECTURE (CRITICAL)

```
┌──────────────────────────────────────────────────────────┐
│                 SOURCE IMAGE DOWNLOAD                     │
│                                                           │
│  Yupoo/Weidian → Download front + back of each garment   │
│  Per color variant: front_angle.jpg + back_angle.jpg      │
│  Also: detail_close, tag_label, size_chart (secondary)    │
└──────────────┬────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│              INDIVIDUAL ITEM PROCESSING                   │
│                                                           │
│  Tops / Bottoms / Single Clothing:                        │
│    → NO AI generation (zero Flow API calls)               │
│    → Front photo = gallery flat lay front                  │
│    → Back photo = gallery flat lay back                    │
│    → Front image → staged in WAREHOUSE for outfit merge   │
│    → Detail/tag/chart images → secondary "Photos" tab     │
└──────────────┬────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│                  WAREHOUSE (Outfit Assembly)               │
│                                                           │
│  Collects front images from individual items:              │
│    top_front + bottom_front + shoe_front                   │
│  Merges into a combined outfit group                       │
│  Triggers FULL OUTFIT model generation                     │
└──────────────┬────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│           FULL OUTFIT MODEL GENERATION (Flow API)         │
│                                                           │
│  ONLY AI generation in the pipeline:                      │
│    → Upload: model face ref + top front + bottom front    │
│      + shoe front as Flow references                      │
│    → Generate: ONE full-body model shot (facing camera)   │
│    → Model: GEM_PIX_2 (Nano Banana Pro), 9:16 portrait   │
│    → Gender-matched (male model for male products)        │
│    → Result: 01_model_front_0.png                         │
└──────────────┬────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│              STOREFRONT GALLERY (per color)                │
│                                                           │
│  Display order:                                           │
│    1. Model shot (AI generated, if outfit assembled)      │
│    2. Top front flat lay (downloaded source photo)         │
│    3. Top back flat lay (downloaded source photo)          │
│    4. Bottom front flat lay (downloaded, if set)           │
│    5. Bottom back flat lay (downloaded, if set)            │
│    6. Other source images (details, tags) — LAST          │
└──────────────────────────────────────────────────────────┘
```

---

## 13. AUTONOMOUS GOOGLE FLOW GENERATION & PERMANENT AUTHENTICATION (LOG IN ONCE AND FOR ALL)

### A. Why Standard Text-to-Image APIs Are Strictly Banned (Rule 36)
- **The Core Problem:** Generic text-to-image APIs (OpenAI DALL-E, Gemini Imagen, Flux, Midjourney, Stable Diffusion) CANNOT perform garment image referencing. They can only imagine a generic item from a text description. They CANNOT take the exact scraped flat lay photo of a hoodie, pants, or jacket and composite it with 100% fidelity (exact brand logos, hardware, embroidery, wash, cut) onto a brand model.
- **The Solution:** Google Flow (`Nano Banana Pro` / `GEM_PIX_2`) is the ONLY engine with multi-image reference inputs (`IMAGE_INPUT_TYPE_REFERENCE` / Ingredients Media). It takes:
  1. **Reference 1:** Brand model face & body
  2. **Reference 2:** Scraped garment front flat lay
  3. **Reference 3:** Scraped garment back / pants / shoes
  And renders an authentic editorial lookbook featuring that exact garment.

### B. Autonomous Cloud Generation Architecture (Zero PC Dependency)
- Generation runs 100% autonomously in the cloud without requiring the user's local PC to be turned on or running any local servers.
- **Runners:**
  1. **Azure VPS (`20.215.232.214`):** Runs `cloud_generator_gha.py` and `test_complete_generation_cycle.py` headlessly under `xvfb-run`.
  2. **GitHub Actions 16GB Runner:** `.github/workflows/obscura_cloud_generator.yml` runs every 4 hours autonomously on cron or via manual trigger.
- **Execution Flow in Flow Studio:**
  1. Open project workspace (`flow.google.com/project/<project_id>`)
  2. Open ingredients menu (`button[aria-label="Add ingredients to the prompt box"]`)
  3. Upload scraped front flat lay image via file chooser
  4. Click `Add to prompt`
  5. Type category-specific editorial prompt into `div.ProseMirror`
  6. Click `Start generation` / press Enter
  7. Stream & download generated RAW PNG/WebP lookbook images
  8. Pillow Post-Processing: Certified true 9:16 vertical (TikTok/Reels) and 1:1 square (IG Posts)
  9. Synthesize 10s Omni Flash UGC video brief (`ugc_video_brief.json`)
  10. Output to `OUTPUT_READY_FOR_SALE/<slug>/` and update curation state

### C. Why Google Sessions Expired & The "Log In Once and For All" Solution
- **Why Sessions Expired Previously:**
  When session cookies are captured on a home PC (residential IP) and dumped into a raw JSON file, and then injected into an ephemeral Playwright context (`browser.new_context()`) on an Azure datacenter IP (`20.215.232.214`), Google's anti-fraud system flags the sudden IP/ASN mismatch and lack of persistent device credentials. Google invalidates the session and redirects to the account chooser showing `Signed out`.
- **The Permanent Fix (Log In ONCE on the Cloud):**
  1. **Persistent VPS Chrome Profile (`/home/azureuser/.obscura_chrome_profile`):**
     Instead of creating an empty temporary context every time, Playwright launches a *persistent user data directory* on the VPS disk via `launch_persistent_context`. The browser cache, LevelDB, IndexedDB, and TLS channel binding tokens remain permanently written to the VPS disk. Google recognizes it as the exact same installed desktop browser every run.
  2. **One-Time VPS Login Procedure (60 Seconds):**
     To log in once directly on the VPS browser:
     - On VPS, launch Chrome with remote debugging:
       `google-chrome-stable --remote-debugging-port=9222 --user-data-dir=/home/azureuser/.obscura_chrome_profile`
     - On local PC, forward port 9222 via SSH:
       `ssh -L 9222:localhost:9222 -i ~/.ssh/azure_obscura_key.pem azureuser@20.215.232.214`
     - In local Chrome, navigate to `chrome://inspect` -> Configure -> add `localhost:9222` -> Click "inspect".
     - Complete Google login to `flow.google.com` once.
     - The credentials and device trust tokens are saved directly to the VPS disk. Because Google issued the session to the Azure VPS IP itself, **it NEVER expires or gets revoked on IP changes**.
  3. **Permanent Google OAuth 2.0 Token Pool (`google_token_manager.py`):**
     Stored in `google_accounts.json` with 4 Google accounts. OAuth 2.0 `refresh_token` credentials **NEVER expire** (unless manually revoked). They exchange for fresh `ya29` access tokens in 200ms on demand 24/7/365 across all machines with zero user interaction.

### D. Model Preferences & Credit Runbook
- **Image Generation:** Always use **`Nano Banana Pro`** (`GEM_PIX_2`) — Always **0 credits**.
- **Video Generation:**
  - `Veo 3.1 - Lite` (`veo_3_1_t2v_lite` / `veo_3_1_i2v_lite`): **10 credits** per 8s video. High quality, cost-efficient.
  - `Omni Flash` (`flow_omni`): **15 credits** per 10s video. Used for organic UGC selfie ads with native audio and speech.

---

## 14. STRATEGIC DECISION — HYBRID DUAL-ROUTED STOREFRONT (JULY 2026)

To balance high-margin replica sales with global scale and safety, OBSCURA operates an automated **Geo-IP Dual-Routed Hybrid Storefront**:

### A. Geo-IP Automated Routing Rules
1. **African Visitors (Nigeria, Ghana, South Africa):** 
   - **Catalog:** Curated Hybrid (Replicas + Original Heavyweight Blanks mixed, TugOfLooks style).
   - **Currency & Billing:** NGN (Naira) / GHS / ZAR via **Paystack, Flutterwave, or Local Bank Transfer**.
   - **Fulfillment:** 100% Direct China-to-Customer dropshipping via Guangzhou Sensitive Air Lines (SpeedyAF / CJ Sensitive).
   - **Safety:** Zero Stripe risk, zero chargeback risk, high 300%–500% net margins.
2. **Global Visitors (North America, UK, Europe, Rest of World):** 
   - **Catalog:** 100% Legal Original Heavyweight Blanks & Independent Chinese Streetwear Designers ONLY (IDLT, Maden, Simple Project). Zero replicas.
   - **Currency & Billing:** USD ($) / EUR (€) / GBP (£) via **Stripe, Apple Pay, Credit Cards**.
   - **Fulfillment:** Direct China-to-Customer air dropshipping via CJ Packet / YunExpress.
   - **Safety:** 100% legal, zero trademark risk, clean brand equity building.

### B. Technical Rules for Replicas (African Catalog)
- **Zero Brand Names in Titles:** Never write trademark names in titles (e.g. use "Gothic Hardware Leather Jacket" or "Geo-basket Sneaker").
- **Generic Vendor Tags:** Every item uses the vendor tag `"OBSCURA"` or `"THE STUDIO"` to bypass database catalog filters.
- **Descriptions:** Use rich, editorial fashion descriptions, dropping brand references only in the text (Tier 2) or relying purely on visual design cues (Tier 3).
- **Pricing:** Keep replica pricing aligned with original premium blank pricing so the catalog looks uniform and high-end.

---

## 15. SCRAPED COMPETITOR BENCHMARK & AFRICAN REPLICA MARKET PRIORITY (CRITICAL)

### A. Scraped Competitor Benchmark: TugOfLooks (`tugoflooks.com`)
- **Background:** TugOfLooks is a prominent Nigerian Shopify store selling high-end luxury/streetwear replicas directly to local buyers under the guise of "curated archival fashion".
- **Scraped Live Catalog Highlights:**
  - **Marlboro F1 Racing Jacket:** Listed at **₦365,250.00** (~$240 USD) — Sourced from 1688 for ¥180 (~$25 USD).
  - **Archive Eagle Zip Hoodie:** Listed at **₦208,999.00** (~$138 USD) — Sourced from Weidian for ¥160 (~$22 USD).
  - **AFGK "Yellow Statement" Jacket:** Listed at **₦322,999.00** (~$215 USD).
  - **Bape WGM Patent Black/Red & Onitsuka Tiger Mexico 66:** Listed at **₦128,000–₦168,000**.
  - **Need A Pillow Thermal Top:** Listed at **₦138,999.00**.
  - **Carbon Drift Utility Shorts & Pinstripe Hardware Pants:** Listed at **₦148,000–₦166,000**.
- **Key Takeaways & Lessons from TugOfLooks:**
  1. **Enormous 300%–500% Margins:** Sourcing Chinese reps for $15–$30 USD and selling in Naira for ₦100k–₦350k yields massive net profits per order.
  2. **Subtle Generic Naming:** Use stylized names (*Archive Eagle Zip Hoodie*, *Pindex Track Jacket*, *Gnostic Neo-Gothic Crewneck*) with generic vendor tags (`"OBSCURA"` / `"THE STUDIO"`) to bypass automated database filters.
  3. **Local Payment Gateways:** Processed via Paystack, Flutterwave, or local bank transfers in NGN — zero chargebacks and zero Stripe risk.

### B. African Market Priority Strategy (Nigeria, Ghana, South Africa)
- **Primary Market Focus:** Target **African consumers (Lagos, Abuja, Accra, Joburg) as the #1 priority** for high-margin replica drops (the *TugOfLooks* model).
- **Direct China-to-Buyer Fulfillment:** Orders route automatically from Paystack -> BuckyDrop/Guangzhou Agent -> Direct Air Cargo -> Customer Doorstep (0 local inventory handling).
- **Why Africa is Priority #1 for Replicas:**
  1. **Low Legal & Trademark Risk:** Western brand lawyers and DMCA agents do not target local African e-commerce dropshipping channels.
  2. **High Demand for Luxury Streetwear Aesthetics:** Massive appetite for high-end fashion, heavy-weight drapes, and bold luxury graphics.
  3. **Zero Chargeback Risk:** African buyers pay upfront via local payment channels (Paystack, Flutterwave, Bank Transfer, Crypto), eliminating Western Stripe/PayPal chargebacks.
  4. **Logistics Advantage:** Direct shipping via African freight forwarders / CJ / local agents with minimal customs friction.

### C. Design Reference Brand: ASTORR (`astorr.co`)
- **Scraped Catalog:** Anime-inspired luxury streetwear catalog (*ADAPT KING JEANS*, *KING OF CURSES HOODIE*, *GODSPEED KNIT*, *KURAPIKA JEANS*). Used for design inspiration and matching outfit drop structures.

---

## 16. AUTOMATED DEVELOPER AGENT & SOURCING TOOLS (JULES & MCP)

To support hands-off development and automated maintenance of the OBSCURA fashion pipeline, the codebase integrates with Google's cloud developer ecosystem:

### A. Google Labs Jules Integration (jules.google.com)
- **Repository:** Connected to `juggernaut7777/obscura` (Private GitHub repository).
- **Brain Integration:** Jules automatically parses this `AGENTS.md` file to understand the architecture, API keys, database design, and code patterns.
- **Proactive Suggestions:** Enabled for automated codebase overview, code cleanup, performance optimizations (fixing slow loops, string concats), and security audits.
- **Workflow:** You can prompt Jules on `jules.google.com` to create tests, refactor scraper tools, or upgrade storefront code. It operates in a secure cloud VM and submits pull requests (PRs) to the repository.

### B. Model Context Protocol (MCP) Capabilities
- **Jules as Client:** Jules can connect to external MCP servers to fetch contextual info or interface with external tools.
- **Custom Sourcing MCP Servers:** The python scrapers (`auto_scout_v2.py`, `chinese_sourcing_agent.py`) can be wrapped into a custom local or hosted MCP server to expose tool executions (e.g. `scrape_weidian`, `get_yupoo_catalog`) directly to AI models like Jules, Aider, or Antigravity IDE.
- **Jules REST API:** Google provides an official REST API (`X-Goog-Api-Key` token auth) that allows scripting or triggering Jules sessions from external CLI tools or CI/CD pipelines.

### C. Fully Autonomous Testing Loop Strategy
To test the pipeline end-to-end (from Yupoo/Weidian scraping, image processing, to storefront uploading and mock generation), we have built a self-healing testing loop (modeled on the Aider/SWE-agent architecture) in `goal2_sourcing_engine/_archive/tests/pipeline_test_runner.py`:

1. **The Test Runner:** Run `python pipeline_test_runner.py` to trigger a simulated product drop (scraping a test link, checking PIL file integrity, validating Flow Bridge token freshness, generating test output, and pushing metadata to Next.js).
2. **Autonomous Error Catching:** The test script captures all console logs, compiler diagnostics, and file trace logs.
3. **PIL-based Curation Checks:** In Stage 2, PIL verify() is executed against curated images to verify dimensions and check for corrupted image headers.
4. **Flow Bridge Health Checks:** In Stage 3, the bridge token is checked for freshness/expiration before calling Flow APIs to prevent silent credential failures.
5. **AI Self-Healing Corrections:** If any stage of the pipeline fails, passing the `--self-heal` flag triggers the local **Antigravity SDK Agent** (`from google.antigravity import Agent`). The agent receives the error traceback and code context, uses its `edit_file` tool to repair the bug in place, and the test runner auto-retries the stage (up to 2 attempts).
6. **CLI Control Center:** Both the End-to-End Test Runner and the Stock Sync scheduler (`auto_stock_sync.py`) are integrated directly as options 8 and 9 inside the control center (`python start_engine.py`).





