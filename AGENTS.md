# 🧠 AGENTS.md — OBSCURA AI Fashion Pipeline Master Knowledge File
> **Last Updated:** 2026-06-05
> **Purpose:** This is the single source of truth for the entire project. Any AI agent (Gemini, Claude, Antigravity, Codex) that reads this file should fully understand the project without needing any prior context.

---

## 1. BUSINESS OVERVIEW

**Brand:** OBSCURA — AI-powered luxury fashion content & resale business.

**Revenue Streams:**
1. **Blanks & Streetwear Resale:** Source premium blanks and independent designer fashion from Chinese sellers (Weidian, 1688, Taobao), generate AI model photos, sell via storefront.
2. **AI Content Agency:** Find small fashion brands with bad product photos on Instagram, pitch them AI-generated lookbook upgrades for a fee.
3. **UGC Generation:** Create user-generated-content style videos/photos using AI for brand campaigns.

**Aesthetic Standard:** Every image must look like it belongs in Vogue or a Balenciaga campaign. See `FASHION_MANIFESTO.md` for the non-negotiable quality rules.

---

## 2. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│                   SOURCING LAYER                     │
│                                                      │
│  auto_scout_v2.py        ← Main storefront scraper  │
│  brand_website_sourcer.py ← Original brand scraping  │
│  crawl4ai_scraper.py     ← Generic web scraping     │
│  competitor_spy.py       ← Competitor monitoring     │
│  tiktok_trend_scraper.py ← TikTok trend mining      │
│  brand_scout.py          ← IG lead generation        │
└───────────────┬─────────────────────────────────────┘
                │ products / catalogs → Discord / downloads
                ▼
┌─────────────────────────────────────────────────────┐
│                   REVIEW LAYER                       │
│                                                      │
│  discord_listener.py     ← Discord bot (review UI)   │
│  review_pending/         ← JSON mappings per sheet   │
│  MANUAL_CURATION/        ← Approved HQ images        │
└───────────────┬─────────────────────────────────────┘
                │ approved products
                ▼
┌─────────────────────────────────────────────────────┐
│                GENERATION LAYER                      │
│                                                      │
│  local_generation_worker.py ← AI image generation    │
│  flow_bridge.py           ← Connects to Flow API    │
│  scene_director.py        ← Scene/location planning │
│  photo_director.py        ← Lighting/camera/pose    │
│  prompt_library.py        ← 50KB of tuned prompts   │
│  vision_evaluator.py      ← Quality scoring         │
│  style_tagger.py          ← Auto gender/niche tags  │
│  carousel_builder.py      ← Multi-image carousels   │
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
│                  BRAIN / INFRA                       │
│                                                      │
│  litellm_router.py       ← API key rotation/fallback│
│  agent_brain_local.py    ← Local orchestration agent │
│  agent_tools.py          ← Tool definitions (100KB) │
│  agent_memory.py         ← Persistent memory        │
│  brain_memory.json       ← Memory state file        │
│  .env                    ← All API keys             │
└─────────────────────────────────────────────────────┘
```

---

## 3. CRITICAL FILE MAP

### 📦 Sourcing (Goal 2)
| File | Purpose | Status |
|------|---------|--------|
| `auto_scout_v2.py` | Main scouter for legitimate Chinese brands and 1688 unbranded basics. | **ACTIVE** |
| `brand_website_sourcer.py` | Scrapes original brand websites (Zara, Nike) for flat-lay images using ScrapeGraphAI + Gemini. | **ACTIVE but underused** |
| `crawl4ai_scraper.py` | Generic web scraper using crawl4ai library. | **ACTIVE** |
| `brand_scout.py` | Searches Instagram for small brands with bad content → generates pitch DMs. "Agency Mode". | **ACTIVE** |
| `competitor_spy.py` | Monitors competitor stores and pricing. | **ACTIVE** |
| `tiktok_trend_scraper.py` | Scrapes TikTok for trending fashion products/hashtags. | **ACTIVE** |
| `meta_ad_scraper.py` | Scrapes Meta Ad Library for competitor ad creatives. | **ACTIVE** |
| `vlm_product_sourcer.py` | Main Yupoo scraper (Replica Sourcing). | **ARCHIVED — REPS REMOVED** |
| `reddit_seller_scout.py` | Mines Reddit for replica sellers. | **ARCHIVED — REPS REMOVED** |
| `reddit_designer_scout.py` | Mines Reddit for blanks/designers. | **ARCHIVED — REPS REMOVED** |
| `smart_sourcer.py` | Alternative sourcing logic (older approach). | **LEGACY** |
| `yupoo_sourcing_agent.py` | Older Yupoo scraper. | **LEGACY** |

### 🤖 Discord Bot
| File | Purpose | Status |
|------|---------|--------|
| `discord_listener.py` | Full Discord bot. Handles: manual drops (images + link), contact sheet replies, Weidian/1688/Taobao direct link scraping, natural language chat via Gemini. | **ACTIVE — CORE** |

### 🎨 Generation
| File | Purpose | Status |
|------|---------|--------|
| `local_generation_worker.py` | Main AI image generation worker. Processes MANUAL_CURATION queue. | **ACTIVE — CORE** |
| `flow_bridge.py` | Bridge to external AI generation APIs (e.g., Flux/Flow). | **ACTIVE** |
| `scene_director.py` | Plans scenes, locations, lighting for AI photoshoots. | **ACTIVE** |
| `photo_director.py` | Camera angles, poses, composition planning. | **ACTIVE** |
| `prompt_library.py` | 50KB of curated prompts for different product types, scenes, styles. | **ACTIVE — CORE** |
| `vision_evaluator.py` | VLM-based quality scoring of generated images. | **ACTIVE** |
| `style_tagger.py` | Auto-tags products with gender, niche, category, scene using Gemini Vision. | **ACTIVE** |
| `carousel_builder.py` | Builds multi-image carousels for social media. | **ACTIVE** |

### 🧠 Brain / Infrastructure
| File | Purpose | Status |
|------|---------|--------|
| `litellm_router.py` | **Critical.** Manages ALL API key rotation. Uses LiteLLM Router with latency-based routing and automatic fallback cascading. | **ACTIVE — CORE** |
| `agent_brain_local.py` | Local orchestration agent that coordinates all subsystems. | **ACTIVE** |
| `agent_tools.py` | 100KB of tool definitions for the agent brain. | **ACTIVE** |
| `agent_memory.py` | Persistent agent memory using SQLite + JSON. | **ACTIVE** |

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
| `_archive/` | Archived old code. |
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

### Yupoo Structure (CRITICAL TO UNDERSTAND)
```
Seller (subdomain.x.yupoo.com)
  └── Categories (e.g., /categories/4644452)
        └── Albums (individual product pages)
              └── Images (thumbnails + HQ originals)
```

**IMPORTANT:** A single Yupoo ALBUM can contain MULTIPLE product types/categories. For example, one album might show a hoodie, matching pants, and accessories all together. The scraper must handle this — it should NOT assume 1 album = 1 product category.

### Current Seller List (Hardcoded in vlm_product_sourcer.py)
15 trusted sellers across: Clothing (Taurus, TopAcney, 3Madman, Goat, Kobe Factory, FOG Store, Allsole, Shark Breeder, CNFashion, DDShop, TopHat), Shoes (WWTOP), Bags (BagKing), Watches (WatchRep), Accessories (LuxuryGoods).

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

### 🟡 ISSUE: Brand Website Sourcing Underused
The `brand_website_sourcer.py` exists but is only called manually via CLI. It should be integrated into the main sourcing pipeline with a list of target brand websites (Zara, Nike, Essentials, etc.).

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

## 11. DEPLOYMENT

### Local (Windows)
- Main machine for development and Discord bot
- Playwright browsers installed locally
- All scripts run via Python 3.11+

### VPS (Linux)
- For 24/7 operation of Discord bot + scraper
- Files: `agent_brain_vps.py`, `agent_tools_vps.py`
- Systemd services: `discord-listener.service`, `auto-matcher.service`
- Setup guide: `VPS_SETUP_GUIDE.md`

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
9. **Image quality: RAW PNG only, minimum 1024x1024** for generation pipeline.
10. **Keep the aesthetic elite** — every image must look editorial, not amateur.
11. **ALWAYS use `Nano Banana Pro` (`GEM_PIX_2`) for images and `Veo 3.1 - Lite` for videos on Google Flow.**
12. **Double check the multiplier for video generation to avoid burning credits (Veo 3.1 Lite costs 10 credits per video base, while Omni Flash costs 15 credits for 10s).**
13. **NEVER open a browser window using Playwright to force manual logins.** ALWAYS use the `OBSCURA` Chrome extension loaded in the user's personal Chrome session to harvest tokens, which communicate via the token bridge server (`all_in_one_bridge.py`) on port 9877.
14. **Video downloads use Phase 3 (base64 decode), NOT URL scraping.** After poll shows `SUCCESSFUL`, call `GET v1/media/{name}` → decode `video.encodedVideo` from base64. NEVER search poll responses for download URLs — they don't exist for videos.
15. **PRIMARY ASPECT RATIO IS STRICTLY 9:16 (PORTRAIT)** for all image and video generation. All marketing & UGC content is optimized for TikTok, Instagram Reels, and Instagram Stories.
16. **NEVER expose supplier links in public storefront catalogs.** The storefront uploader must hide all `supplierLink` references from public files to protect source confidentiality.
17. **ALWAYS maintain a private `supplier_mappings.json` file** to store original Chinese marketplace URLs, costs, and variant mappings (colors/sizes translated from English to Chinese).
18. **ALWAYS reverse-map customer options back to Chinese** when processing orders for procurement. The DDP agent needs the exact Chinese option text (e.g. `黑色`, `XL码`) to purchase the correct items.
19. **REPLICAS REQUIRE DDP AGENTS FOR AFRICA SHIPMENTS.** Do not use Kakobuy, Superbuy, or CJ Dropshipping for replica orders due to high shipping costs and replica bans. Only use Alibaba DDP agents.

---

## 13. GOOGLE FLOW API & CREDIT RUNBOOK

### Model Preferences (NON-NEGOTIABLE)
- **Always** use **`Nano Banana Pro`** (`GEM_PIX_2`) for images (high-fidelity premium look).
- **Always** use **`Veo 3.1 - Lite`** (`veo_3_1_t2v_lite`) for videos (highest quality/cost efficiency).
- **Omni Flash** (`omni_flash`) is allowed ONLY when duration control is needed (it lets you set 5s/10s). Costs 15 credits for 10s.

### Credit Cost Structure
- **Image Generation**: Always **0 credits** (even with a `4x` multiplier).
- **Video Generation**:
  - `Veo 3.1 - Lite`: **10 credits** per video (8s, fixed). Multiplier scale: `1x = 10`, `2x = 20`, `3x = 30`, `4x = 40` credits.
  - `Veo 3.1 - Fast`: **20 credits** per video (base).
  - `Veo 3.1 - Quality`: **50 credits** per video (base).
  - `Omni Flash`: **15 credits** per 10s video. Supports custom duration (5s/10s via UI). Only use when explicitly approved.

### Direct HTTP API Architecture (NON-NEGOTIABLE)
All generation goes through the Direct HTTP API using tokens from the OBSCURA Chrome extension via `all_in_one_bridge.py` on port 9877. **NEVER use Playwright browser automation for Flow.**

#### Image Generation (Synchronous)
```
POST /v1/projects/{pid}/flowMedia:batchGenerateImages
  → Response contains fifeUrl download links immediately
  → Download fifeUrl → done
```
- **Model Key:** `GEM_PIX_2` (Nano Banana Pro)
- **Reference Images:** Upload via `POST /v1/flow/uploadImage` → get `asset_id` → pass as `imageInputs: [{imageInputType: "IMAGE_INPUT_TYPE_REFERENCE", name: asset_id}]`

#### Video Generation (Async 3-Phase)
```
Phase 1: POST /v1/video:batchAsyncGenerateVideoText
  → Returns media_name (job ID)

Phase 2: POST /v1/video:batchCheckAsyncVideoGenerationStatus
  → Poll every 8s until mediaGenerationStatus == "MEDIA_GENERATION_STATUS_SUCCESSFUL"
  → ⚠️ This endpoint NEVER returns download URLs!

Phase 3: GET /v1/media/{media_name}
  → Returns JSON with video.encodedVideo (base64-encoded MP4)
  → base64.b64decode(encodedVideo) → save as .mp4
```

#### Video API Model Keys & Payload
| Model | API Key | Mode | Duration | Credits |
|-------|---------|------|----------|---------|
| Veo 3.1 Lite | `veo_3_1_t2v_lite` | Text-to-Video | 8s fixed | 10 |
| Veo 3.1 Lite (I2V) | `veo_3_1_i2v_lite` | Image-to-Video | 8s fixed | 10 |
| Veo 3.1 Fast | `veo_3_1_t2v_fast` | Text-to-Video | 8s fixed | 20 |
| Omni Flash | `omni_flash` | Text-to-Video | 5s/10s selectable | 15 (10s) |

#### Reference Images for Video (Image-to-Video)
To use a reference image with video generation:
1. Upload the image via `POST /v1/flow/uploadImage` (same as image gen) → get `asset_id`
2. Switch the model key from `veo_3_1_t2v_lite` to `veo_3_1_i2v_lite`
3. Add the reference in the request object:
```json
{
  "aspectRatio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
  "videoModelKey": "veo_3_1_i2v_lite",
  "imageInput": { "name": "<asset_id>" },
  "textInput": { "structuredPrompt": { "parts": [{"text": "<prompt>"}] } }
}
```

### Video Prompting Best Practices
Video prompts must be **cinematic and specific** — unlike image prompts, vague descriptions produce poor results.

**BAD (vague, generic):**
> "A model wearing a hoodie walking"

**GOOD (cinematic, specific):**
> "Slow cinematic tracking shot following a tall male model in a black oversized heavyweight hoodie, walking through rain-soaked neon-lit Tokyo alley at night. Camera at waist height, shallow depth of field, anamorphic lens flare. Moody editorial fashion film aesthetic, 24fps."

**Key elements for fashion video prompts:**
1. **Camera movement:** tracking shot, dolly zoom, slow pan, orbit, static close-up
2. **Lighting:** neon, golden hour, studio softbox, moody backlit, high-key editorial
3. **Location:** specific and atmospheric (Tokyo alley, concrete brutalist interior, desert highway)
4. **Model action:** walking, turning, posing, adjusting collar, hands in pockets
5. **Lens/look:** shallow DOF, anamorphic, film grain, 24fps cinematic
6. **Garment description:** be VERY specific about the clothing ("oversized black heavyweight cotton hoodie with dropped shoulders")

### How to Maneuver the Flow UI
1. **Agent Toggle**: Pill toggle under prompt box (`(420, 663)`).
   - Keep **OFF** (`pressed=false`) to enable manual model, ratio, and duration settings.
2. **Opening Controls**: Click the model summary button (e.g. `🍌 Nano Banana 2 crop_16_9 x2`) in the bottom toolbar to open the manual controls popup.
3. **Tab Navigation**:
   - Click the **Image tab** (`imageImage` at `(697, 427)`) first before trying to select image models.
   - Click the **Video tab** (`play_circleVideo` at `(829, 427)`) first before trying to select video models.
4. **Dropdown Selection**:
   - Model dropdown is at `(763, 560)`. Click to open options.
   - Use normalized alphanumeric comparison to select the model (e.g., matching `"Veo 3.1 - Lite"` to `"veo 3.1 lite"`).
5. **Duration Control (Omni Flash only):**
   - When Omni Flash is selected, a duration slider/option appears allowing 5s or 10s.
   - Veo 3.1 models have fixed 8s duration — no duration control available.

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
To test the pipeline end-to-end (from Yupoo/Weidian scraping, image processing, to storefront uploading and mock generation), we implement a self-healing testing loop (modeled on the Aider/SWE-agent architecture):
1. **The Test Runner:** Run `goal2_sourcing_engine/start_test_run.py` to trigger a simulated product drop (scraping a test link, staging in `MANUAL_CURATION`, launching `local_generation_worker.py` in test mode, and pushing metadata to Next.js).
2. **Autonomous Error Catching:** The test script captures all console logs, compiler diagnostics, and playwright trace logs.
3. **AI Corrections:** If any stage of the pipeline fails (e.g. rate limit, selector change, syntax crash), the error is fed directly to the active agent (Jules in the cloud or Antigravity locally) with the instruction to fix the code, commit the repair, and re-run the test script. This forms a closed, self-healing loop until the test pipeline achieves a 100% green checkmark.





