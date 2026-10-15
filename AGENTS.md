# 🧠 AGENTS.md — OBSCURA AI Fashion Pipeline Master Knowledge File
> **Last Updated:** 2026-10-15
> **Purpose:** Single source of truth for all AI agents (Antigravity, GitHub Copilot, Gemini, Claude, Codex).
> **Copilot Handover:** Read `.github/copilot-instructions.md` and `COPILOT_BRIEF.md` for fast onboarding.

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
│  auto_image_classifier.py ← SUPERSEDED by V2      │
│  image_classifier_v2.py  ← Multi-model ensemble    │
│  pipeline_orchestrator.py← Classification pipeline  │
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
| `auto_image_classifier.py` | **SUPERSEDED** — Old single-model VLM classifier. Replaced by V2 pipeline below. | **ARCHIVED** |
| `image_classifier_v2.py` | Multi-model ensemble image classifier. Gemini primary + Qwen3-VL validator, partial JSON recovery, short-prompt retry. | **ACTIVE — CORE** |
| `seller_profiler.py` | Yupoo seller posting pattern profiler. Scrapes sample albums, classifies patterns, builds per-seller profiles. | **ACTIVE** |
| `storefront_image_selector.py` | Smart waterfall image selector. Category-specific priority (flat_lay → on_model → detail), seller profile boost. | **ACTIVE** |
| `background_enhancer.py` | AI background replacement for flat lays. Replaces white/grey Yupoo backgrounds with premium dark surfaces via Flow API. | **ACTIVE** |
| `pipeline_orchestrator.py` | CLI orchestrator wiring all classification pipeline components. `--classify`, `--select`, `--enhance`, `--full`, `--batch-all`. | **ACTIVE — CORE** |
| `storefront_curator_guard.py` | Gate 3 automated quality validator: 4 non-negotiable checks (selfie-free, MIME alignment, min 512x512 resolution, complete bundle). | **ACTIVE — CORE** |
| `antigravity_classifier.py` | Frontier multimodal spatial geometry classifier with binary boolean gates (100% or 0%). Multi-category support (clothing, shoes, bags, eyewear, watches, accessories). | **ACTIVE — CORE** |
| `vps_master_daemon.py` | 24/7 Autonomous Master Daemon orchestrating Sector 0 (Sourcing/Sizing), Sector 1 (AI Generation), Sector 2 (Curator Guard), and Sector 3 (Catalog Deployment). Zero local CLI needed. | **ACTIVE — CORE** |
| `meta_ai_video_worker.py` | AI video generation worker for Meta AI / Flow video pipeline. | **ACTIVE** |


### 🧠 Brain / Infrastructure
| File | Purpose | Status |
|------|---------|--------|
| `litellm_router.py` | **Critical.** Manages ALL API key rotation. Uses LiteLLM Router with latency-based routing and automatic fallback cascading. | **ACTIVE — CORE** |
| `google_accounts.json` | Permanent OAuth 2.0 refresh tokens for 4 Google accounts. Eliminates web session expiration. | **ACTIVE — CORE** |
| `.github/workflows/obscura_cloud_generator.yml` | 100% Free GitHub Actions workflow running lookbook generation every 4 hours autonomously. | **ACTIVE — CORE** |
| `obscura-master.service` | Azure VPS systemd service running `vps_master_daemon.py --daemon --interval 1800` continuously. | **ACTIVE — CORE** |
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

### 🔑 THE CORE BUSINESS MODEL (MUST UNDERSTAND)
Replica/independent fashion sellers in China operate a **two-platform system**:

1. **Yupoo = IMAGE GALLERY (Product Showcase)**
   - Yupoo is a free image hosting platform. Sellers use it as their **product catalog** with HIGH-RESOLUTION, UNCENSORED photos showing brand names, logos, stitching details, and tags clearly visible.
   - Sellers CANNOT post these photos on marketplace platforms (Weidian/Taobao/1688) because those platforms actively CENSOR brand names and logos to avoid copyright takedowns.
   - Each seller has a subdomain (e.g., `taurus.x.yupoo.com`) organized into categories and albums.
   - Each album = one product (or a set), containing 4-15 high-quality photos: front flat lay, back flat lay, detail closeups, on-model shots, size charts.
   - **Albums contain a hidden purchase link** in the description text — this links to the actual Weidian/Taobao/1688 listing where you can buy the item.

2. **Weidian/Taobao/1688 = PURCHASE BACKEND (Transaction Platform)**
   - This is where the actual e-commerce transaction happens — add to cart, select color/size variant, pay.
   - Listings here have BLURRED/CENSORED images (9 out of 10 blur brand logos).
   - BUT they have **accurate, live data**: real color variant names (in Chinese), real available sizes, real pricing, stock status, seller ratings, shipping info.
   - The Chinese color variant strings on these listings are the EXACT strings you must select when placing an order through an agent.

3. **OBSCURA = THE MERGER**
   - We merge BOTH sources into a single unified product listing on our storefront:
     - **HQ Product Images** → from Yupoo (uncensored, logo-visible, high-res)
     - **Colors, Sizes, Pricing, Stock** → from Weidian/Taobao/1688 marketplace listing
     - **AI Editorial Content** → generated by Flow using the Yupoo front flat lay as ingredient
   - The customer sees ONE polished product page with: hero images, multiple angles, AI model shots, real color swatches, real sizes, and a size guide — all sourced from different places and assembled by our pipeline.
   - **The purchase link and Chinese variant mappings are stored in `supplier_mappings.json` (PRIVATE, never exposed to customers)** so that when an order comes in, `auto_fulfillment.py` knows exactly which Weidian listing + variant string to order.

### ⚠️ CRITICAL: IMAGE SOURCE RULE (NON-NEGOTIABLE)
- **Product images for AI generation MUST ALWAYS come from YUPOO**, never from Weidian, Taobao, or 1688.
- **Why:** Yupoo is where sellers post their HIGH-RESOLUTION, UNCENSORED product photos. Weidian/Taobao/1688 listings BLUR OUT brand names and logos to avoid platform takedowns.
- **Pipeline rule:** The scraper must download product images from the Yupoo album page. The marketplace purchase link extracted from the Yupoo album description is saved as metadata for ordering and variant mapping.

### ⚠️ CRITICAL MANDATE: MARKETPLACE VARIANT & SIZING EXTRACTION (NON-NEGOTIABLE)
- **Mandatory Flow:** For EVERY Yupoo product album, the scraper/agent **MUST extract the marketplace purchase link** (Weidian, Taobao, or 1688) from the album description.
- **Immediate Marketplace Resolution:** The scraper **MUST open and scrape the Weidian/Taobao/1688 listing** to extract:
  1. **Accurate Color Options:** Scrape the exact Chinese color variant strings and translate/map them to authentic English luxury color names (e.g., "花灰" → "Heather Grey", "炭黑" → "Washed Charcoal", "军绿" → "Mineral Olive", "藏青" → "Deep Navy") with corresponding hex codes.
  2. **Accurate Sizing Options:** Extract live available sizes (e.g., `["S", "M", "L", "XL", "2XL"]`) and live stock status per size.
  3. **Accurate Sizing Chart:** Scrape the seller's specific measurement table (chest cm, length cm, shoulder cm, sleeve cm) for the interactive size guide modal.
- **Storefront Display Rule:** The extracted marketplace colors and sizes are **MANDATORY for populating `storefront/src/data/products.js`**.
  - **NEVER use generic placeholders** like `[{ "name": "Default", "hex": "#1a1a1a" }]` when the marketplace listing specifies actual colorways.
  - Sizing must accurately reflect what is physically purchasable from the Chinese supplier so customers only order in-stock sizes and real colors.

### ⚠️ CRITICAL MANDATE: FLOW GENERATION & STOREFRONT ANGLE RESOLUTION (NON-NEGOTIABLE)
- **Flow Generation Ingredient:** AI image and video generation (Flow API / Google Flow) **MUST STRICTLY use the FRONT FLAT LAY image** as the visual media ingredient reference.
  - **NEVER** pass a back angle, side angle, or detail close-up as the primary Flow generation ingredient. Flow requires the clean front flat lay of the garment to accurately understand and drape the item onto models.
  - For sets (tracksuit / top + bottom): Use the pre-combined flat lay or a 9:16 vertical composite (front top stacked above front bottom).
- **Storefront Comprehensive Multi-Angle Asset Bundle:**
  - Customers must be able to inspect every angle of the garment on the storefront catalog before purchasing.
  - The pipeline **MUST ALWAYS preserve and attach**:
    1. **Primary Hero:** Clean front flat lay (or enhanced background front flat lay).
    2. **Back Angle:** Back flat lay image (mandatory for customer evaluation and catalog hover cards).
    3. **Detail Extras:** Seam closeups, embroidery/print macros, hardware, wash tags, and fabric texture shots.
    4. **Size Chart:** Official seller measurement table image for the sizing guide modal.
    5. **Editorial Lookbook Stills:** High-fashion on-model runway and editorial shots (featured in the product gallery and Lookbook).
  - When scraping Yupoo albums and staging into `MANUAL_CURATION/`, the scraper and classifier must NEVER discard back angles or detail macros — they must be routed to `storefront/public/products/<slug>/` alongside the generated lookbook stills.

### 6.1 SELLER PROFILING & POSTING PATTERN ANALYSIS (MANDATORY BEFORE SCRAPING)
- **Why Profiling is Mandatory:** Every Chinese seller formats their Yupoo photo albums differently. Blindly selecting image `[0]` fails because sellers often place size charts, contact cards, or weight scales at the start or end of albums.
- **Posting Pattern Discovery:**
  - Before ingesting any new seller, `seller_profiler.py` analyzes 5-10 sample albums to determine the seller's typical sequence:
    - *Example (ChaosMade / 3Madman):* `[0]` = Size Chart, `[1-3]` = Front Flat Lay, `[4-5]` = Back Flat Lay, `[6-10]` = Detail Macros (tags, wash labels, embroidery, hardware), `[11]` = Scale/Mannequin.
  - Profiles are saved in `data/seller_profiles.json` and dynamically boost VLM classification confidence in `storefront_image_selector.py`.
- **Handling Multi-Piece Sets (Tracksuits / Ensembles):**
  - Albums showcasing matching sets often contain: top front flat lay, bottom front flat lay, and a combined flat lay.
  - The pipeline detects sets, builds 9:16 vertical composite flat lays (top stacked above bottom), and scrapes both top/bottom SKU options from the marketplace listing.

### 6.2 IMAGE ROLE MAPPING & DISCARD RULES (NON-NEGOTIABLE)
**STRICT BINARY ARBITER (100% or 0% — ZERO FUZZY 1–10 SCORES):**
Every image ingested by the pipeline is evaluated through a strict boolean spatial geometry gate (`antigravity_classifier.py` / `image_classifier_v2.py`). There are NO fuzzy 1–10 quality ratings. An image is either 100% verified for a role or rejected:
- `is_size_chart` (bool): True if official measurement table (chest, length, shoulder cm).
- `is_full_garment` (bool): True ONLY if the COMPLETE uncropped silhouette from collar/waist to hem/cuff is in frame with ZERO edge cuts. **MANDATORY RULE:** If `is_full_garment == False`, the image can NEVER be assigned a flat lay hero role (`front_flat_lay` or `back_flat_lay`).
- `is_front_facing` (bool): True if showcasing the front side of the garment/product.
- `is_back_facing` (bool): True if showcasing the clean reverse back side.
- `is_side_profile` (bool): True if outer lateral profile (critical for footwear).
- `is_detail_macro` (bool): True if high-res macro close-up of seams, wash labels, embroidery, hardware, or fabric weave.
- `is_discard` (bool): True for plastic mannequins, headless display dummies, WeChat QR codes, seller contact cards, and weight scale images.
- `is_set` (bool): True if the album depicts a 2-piece set (tracksuit/co-ord).

**Multi-Category Role Assignments:**
1. `front_flat_lay`:
   - **Role:** Primary storefront hero image + Visual media ingredient chip for Google Flow lookbook generation + source for dark background enhancement (`background_enhancer.py`).
   - **Strict Rule:** MUST have `is_full_garment: true` and `is_front_facing: true`.
2. `back_flat_lay`:
   - **Role:** Catalog hover card & secondary angle. Customers must inspect the back of garments before purchasing.
   - **Strict Rule:** MUST have `is_full_garment: true` and `is_back_facing: true`.
3. `shoe_lateral_profile`:
   - **Role:** Primary footwear hero image & Flow ingredient. Outer lateral side profile of the shoe on a clean surface.
4. `bag_front_upright`:
   - **Role:** Primary handbag/backpack hero image & Flow ingredient. Standing upright vertical front view with clean strap drape.
5. `watch_dial_face`:
   - **Role:** Primary watch hero image & Flow ingredient. Centered front-facing macro of dial, bezel, and vertical straps.
6. `eyewear_front_hero`:
   - **Role:** Primary sunglasses/eyewear hero image & Flow ingredient. Front straight-on lens and frame geometry.
7. `accessory_hero`:
   - **Role:** Primary hero image for belts, jewelry, scarves, or hats on clean dark/neutral background.
8. `detail_macro` (3 to 5 images):
   - **Role:** High-fashion craftsmanship inspection: seams, embroidery close-up, distressing, zipper/hardware, neck tag, fabric weave.
9. `size_chart`:
   - **Role:** Official measurement table (chest cm, length cm, etc.). Routed to the interactive sizing guide modal. NEVER used as hero or Flow ingredient.
10. `weight_scale`:
    - **Role:** Ingested solely to extract numeric weight in grams (`product.weight_grams = 680`, `product.gsm = 450`). **DISCARDED from the customer image gallery.**
11. `mannequin` & `seller_card`:
    - **Role:** Plastic headless display dummies, WeChat QR codes, and seller promo graphics are **DISCARDED COMPLETELY**.

### 6.3 PROMPT FORMULAS (ZERO BRAND NAMES — STRICTLY ENFORCED)
- **Zero-Brand-Name Mandate:**
  - NEVER mention brand names ("OBSCURA", "Balenciaga", "Hellstar", "Vogue", "Chrome Hearts", "Represent") in generation prompts.
  - Doing so causes catastrophic prompt collision, hallucinated text prints/watermarks on garments, and destroys reference fidelity.
  - The multimodal model receives the clean front flat lay as an image chip and derives 100% of color, fabric texture, cut, logos, and graphics directly from the reference.
  - Prompts refer strictly to: `"this exact garment from the referenced image"`, `"the complete matched set from the referenced image"`, or `"this exact product"`.

- **Comprehensive Category Editorial Formulas:**
  1. **Matching Sets & Tracksuits (Top + Bottom):**
     - *Backstage Runway (9:16):* `"Full-length vertical 9:16 high-fashion editorial runway lookbook photo of a model wearing the complete two-piece matched set from the referenced image: the top garment on the upper torso and the matching bottoms on the lower body. Both pieces strictly preserve the exact color, fabric drape, and detailing from the referenced composite flat lay. Model captured backstage in natural motion getting ready to walk during an architectural minimalist runway show. Natural backstage ambient daylight, sharp 85mm prime lens portrait photography, 8k resolution, raw photo."`
     - *Studio Chiaroscuro (1:1):* `"Square 1:1 waist-up luxury editorial lookbook photo of a high-fashion model wearing the complete matched outfit from the referenced image. Dramatic chiaroscuro studio rim lighting highlighting the realistic fabric drape, weight, and tailored seam architecture. Minimalist concrete gallery setting, high-fashion editorial standard, raw photo, 8k resolution."`
     - *Bed GRWM Spread (9:16):* `"Overhead vertical 9:16 high-angle flat lay photo of the complete matched outfit from the referenced image neatly styled on a modern minimalist bed with a sleek smartphone, slim laptop, and open art magazine like an authentic GRWM photoshoot spread. Soft morning window daylight, crisp textile weave and drape, raw photo, ultra-realistic."`
  2. **Outerwear (Jackets, Coats, Puffers, Shells, Bombers):**
     - *Colonnade Motion (9:16):* `"Full-length vertical 9:16 high-fashion editorial lookbook photo of a model wearing this exact jacket from the referenced image. Model in dynamic motion walking along a brutalist stone colonnade during twilight. Jacket styled with plain neutral dark tailored trousers and clean boots. Sharp 85mm prime lens, cinematic atmospheric ambient light, raw photo, 8k resolution."`
     - *Studio Architecture (1:1):* `"Square 1:1 luxury studio lookbook photo of a model wearing this exact jacket from the referenced image. Directional chiaroscuro rim lighting accentuating the structured shoulder silhouette, heavyweight textile texture, zipper hardware luster, and collar architecture. Raw photo, 8k resolution."`
  3. **Tops (Hoodies, T-Shirts, Knits, Overshirts):**
     - *Backstage Runway (9:16):* `"Full-length vertical 9:16 high-fashion editorial lookbook photo of a model wearing this exact garment from the referenced image. Model captured backstage in natural motion getting ready to walk during an architectural minimalist runway show. Paired with plain neutral tailored dark trousers and clean boots. Editorial styling, sharp 85mm prime lens photography, natural ambient lighting, raw photo, 8k resolution."`
     - *Studio Drape (1:1):* `"Medium waist-up high-fashion editorial studio photo of a model wearing this exact garment from the referenced image. Cinematic rim lighting emphasizing the heavy fabric drape, structured collar, and meticulous seam finishings. Minimalist concrete gallery setting. Square 1:1 composition, editorial campaign aesthetic, 85mm portrait, raw photo, 8k resolution."`
     - *Bed GRWM (9:16):* `"Overhead vertical 9:16 high-angle flat lay photo of this exact garment laid flat on a modern minimalist bed with a sleek smartphone, slim laptop, and open art magazine like an authentic GRWM fashion preparation spread. Soft morning window daylight, crisp textile texture, raw organic feel, ultra-realistic."`
  4. **Bottoms (Trousers, Cargo, Denim, Sweatpants):**
     - *Runway Stacking (9:16):* `"Full-body vertical 9:16 street-editorial runway lookbook photo of a model wearing the exact trousers from the referenced image. Styled with a minimal plain black boxy cropped top and clean brutalist boots. Model captured backstage in motion getting ready to walk during a fashion runway presentation. Crisp focus on silhouette, fabric drape, and clean hem stacking. Vertical 9:16 composition, natural ambient lighting, raw photo, 8k resolution."`
     - *Pavilion Stride (1:1):* `"Lower-body 1:1 square editorial shot focusing on the exact trousers from the referenced image in motion. Subtle dynamic stride in a modern brutalist pavilion. Morning architectural shadows highlighting textile weave, utility pockets, and seam construction. Square 1:1 framing, luxury editorial campaign standard, raw photo, 8k."`
  5. **Footwear (Sneakers, Boots, Loafers):**
     - *On-Foot Runway (9:16):* `"Vertical 9:16 high-fashion on-foot editorial photo of a model wearing the exact shoes from the referenced image. Paired with wide-leg neutral tailored wool trousers that break cleanly over the shoe silhouette. Model in motion backstage during a runway show. Vertical 9:16 angle, sharp editorial portrait lens, raw photo."`
     - *Travertine Step (1:1):* `"Dynamic close-up on-foot 1:1 editorial photo of the exact shoes from the referenced image stepping forward on a polished travertine marble slab. Cinematic soft directional lighting highlighting sculpted sole geometry, material grain, and clean stitching. Square 1:1 crop, luxury runway quality, 8k raw photo."`
  6. **Bags & Backpacks:**
     - *Coat Arm Drape (9:16):* `"Vertical 9:16 high-fashion editorial photo of a model in a minimalist charcoal coat, effortlessly carrying the exact bag from the referenced image over their arm. Model captured backstage getting ready to walk a runway show. Tactile focus on leather grain, edge finish, and brushed hardware. Vertical 9:16 framing, raw photo."`
     - *Upright Travertine Block (1:1):* `"Luxury editorial still life photo of the exact bag from the referenced image positioned upright on an Italian travertine marble block. Clean diffused morning side-light highlighting the supple material drape, structured base, and brushed hardware. Square 1:1 format, raw photo."`
  7. **Watches & Timepieces:**
     - *Wrist Editorial (9:16):* `"Vertical 9:16 close-up high-fashion editorial photo of a model wearing the exact watch from the referenced image on their wrist. Model in tailored dark suiting, captured in subtle motion against a minimalist studio background. Sharp macro prime lens, soft cinematic studio lighting, raw photo, 8k resolution."`
     - *Basalt Plinth Dial (1:1):* `"Square 1:1 centered macro editorial still life photo of the exact watch from the referenced image resting on a dark volcanic basalt stone plinth. Directional grazing light emphasizing dial finishing, bezel bevels, and metallic luster. Raw photo, 8k."`
  8. **Eyewear & Sunglasses:**
     - *Loft Frame Crop (9:16):* `"Vertical 9:16 high-fashion close-range editorial portrait of a model wearing the exact eyewear frames from the referenced image. Model standing in a bright sunlit loft with soft architectural shadows. Crisp focus on frame geometry, bridge alignment, and lens clarity. Vertical 9:16 framing, raw photo."`
     - *Travertine Rest (1:1):* `"Square 1:1 centered editorial still life photo of the exact eyewear frames from the referenced image resting open on a matte travertine stone slab. Natural overhead skylight showing crisp temple lines, hinge craftsmanship, and clear reflections. Raw photo, 8k."`
  9. **Accessories & Jewelry (Belts, Chains, Rings):**
     - *Editorial Macro (1:1):* `"Macro editorial commercial product photo of the exact luxury accessory from the referenced image displayed on a minimalist textured volcanic stone plinth. Crisp overhead directional strobe emphasizing micro-engravings, brushed metal bevels, and craftsmanship. Square 1:1 centered composition, editorial campaign quality, 8k resolution, raw photo."`

### 6.4 WEIDIAN MARKETPLACE RESOLUTION & LIVE VARIANT MAPPING
- **Thor API Endpoint:** `https://thor.weidian.com/detail/getItemSkuInfo/1.0?param={"itemId":"<id>"}` with `Referer: https://weidian.com/`.
- **Live Variant Ingestion:**
  - `attrTitle: "颜色"` / `attrValues`: Scrapes exact Chinese color variant names and translates them via `color_matcher.py` into authentic luxury English colorways with swatch hex codes (e.g. `黑色` → `Washed Obsidian` `#1A1A1A`, `花灰` → `Heather Grey` `#9CA3AF`, `军绿` → `Mineral Olive` `#4B5320`, `藏青` → `Deep Navy` `#0B3C5D`).
  - `attrTitle: "尺码"` / `attrValues`: Extracts true available sizes (`S`, `M`, `L`, `XL`, `2XL`).
  - `skuInfos`: Extracts live price in CNY (`discountPrice / 100`) and live stock count per size (`stock`). Sizes with zero stock are flagged out of stock.
  - `supplier_mappings.json`: Privately maps storefront product slugs and translated colors to exact Weidian item IDs and Chinese variant strings for automated agent fulfillment.

### 6.5 VLM COMPARATIVE VERIFICATION GATE
- Before any generated lookbook image is approved and attached to a storefront catalog listing, it must pass `VisionEvaluator.evaluate_reference_match()`:
  - Compares the generated image against the original Yupoo front flat lay.
  - Evaluates:
    1. Garment category & silhouette match (score >= 7/10)
    2. Color & wash fidelity (score >= 7/10)
    3. Pattern / graphic preservation without gibberish (score >= 7/10)
    4. Absence of hallucinated text or watermarks
    5. Anatomical correctness (score >= 5/10)
  - Generated images scoring below 6.5 average are automatically rejected and regenerated.

### 6.6 TESTING PROTOCOL BEFORE FULL AUTOMATION
- Before starting 24/7 background daemons (`obscura-master.service`, `cloud_generator_gha.py --daemon`), the pipeline must:
  1. Clean all legacy/corrupt test data from VPS and storefront catalog.
  2. Test and visually inspect 1 to 3 curated products end-to-end (Yupoo scrape → Weidian resolution → Classification → Flow generation → VLM verification → Storefront deployment).
  3. Verify all live pages on the storefront (`/`, `/shop`, `/lookbook`, `/product/[id]`) display genuine high-res assets with working cart, currency, and multi-angle galleries.

### 6.7 NEW SELLER ONBOARDING & FRONTIER AUDIT PROTOCOL (MANDATORY)
- **Problem Statement:** Blind automated scraping of unknown sellers causes pipeline contamination because Chinese Yupoo sellers follow completely arbitrary layout sequences (e.g. some put size charts at index 0, some place WeChat contact cards at index 0, others place mannequin shots or weight scales first).
- **Mandatory Onboarding Audit Protocol:**
  Whenever a new seller is introduced (from Reddit, Discord drop, or Yupoo catalog expansion):
  1. **Multimodal Frontier Inspection (`antigravity_classifier.py` / `seller_profiler.py`):**
     - Before automated batch ingestion, sample 5 to 10 diverse albums from the new seller.
     - Inspect the layout sequence using frontier multimodal vision (evaluating full garment bounding boxes, collar/hem margins, presence of text cards, measurement rulers, or mannequins).
  2. **Sequence Fingerprint Extraction:**
     - Identify where the seller places the front flat lay (e.g., indices `[1..3]`), back flat lay (e.g., indices `[4..5]`), detail macros (e.g., indices `[6..10]`), size chart, and scale.
     - Detect album format patterns: single garment vs. 2-piece tracksuit sets vs. 3-piece accessory packs.
  3. **Profile Registration (`data/seller_profiles.json`):**
     - Record the seller profile with verified key positions, typical image counts, and category specializations.
     - The profile dynamically boosts classification accuracy in `storefront_image_selector.py`.
  4. **Strict Gate:** Automated batch ingestion is STRICTLY FORBIDDEN for any seller without a registered profile in `seller_profiles.json`.

### 6.8 MULTI-CATEGORY REFERENCE IMAGE SPECIFICATION MATRIX
Every product category sold on OBSCURA has a strictly defined **optimal visual reference angle** for Google Flow lookbook generation and storefront hero presentation. The classifier and image selector MUST enforce these exact standards:

| Category | Primary Reference Angle (Flow Ingredient & Storefront Hero) | Discard / Rejection Triggers | Secondary Angles Preserved for Catalog |
| :--- | :--- | :--- | :--- |
| **Clothing (Tops, Outerwear, Bottoms)** | `front_flat_lay`: Complete silhouette from collar/waist to hem/cuff on clean neutral surface. Must satisfy `is_full_garment: true` and `is_front_facing: true`. | Partial crop, folded garment, plastic mannequin, hanger distortion, cropped collar or hem. | `back_flat_lay` (mandatory for hover card), 3-5 `detail_macro` (embroidery, wash tag, zipper), `size_chart`. |
| **Matching Sets (Tracksuits / Co-ords)** | 9:16 Vertical Composite (`composite_builder.py`): Top front flat lay stacked vertically above bottom front flat lay. | Disjointed crops, top-only or bottom-only selected as set hero. | Individual top flat lay, individual bottom flat lay, detail macros. |
| **Shoes & Sneakers** | `shoe_lateral_profile`: Outer lateral side profile showing the full silhouette from toe to heel on clean surface. | Dirty sole bottom, top-down foot opening view, interior insole, heel-only view. | Medial side profile, pair top-down view, outsole tread macro, heel logo macro, box label. |
| **Bags & Backpacks** | `bag_front_upright`: Standing vertical front view with clean strap drape showing full structure and silhouette. | Crushed/deflated flat, interior lining only, base bottom only. | Back view, interior compartment macro, hardware/buckle macro, leather grain closeup. |
| **Watches & Timepieces** | `watch_dial_face`: Direct front-facing macro centered on dial, hands, and bezel with vertical strap alignment. | Angled glare obscuring dial, caseback only, clasp only. | Caseback engraving, crown/pusher macro, bracelet/clasp macro, lume shot. |
| **Eyewear & Sunglasses** | `eyewear_front_hero`: Direct front straight-on view showing frame geometry, bridge, and lenses with zero distortion. | Folded flat upside down, extreme angle hiding frame width. | 45-degree angled temple view, side temple logo macro, case and cloth set. |
| **Jewelry & Belts** | `accessory_hero`: Centered high-resolution shot of uncoiled belt or laid-flat jewelry piece on dark velvet/stone surface. | Tightly coiled belt hiding buckle, tangled chain, blurry reflection. | Buckle engraving macro, clasp detail, hallmark stamp macro. |

### 6.9 AUTONOMOUS 24/7 VPS MASTER DAEMON ARCHITECTURE (Zero Local CLI)
- **User Directive:** The user will NEVER run local CLI scripts or manually test/verify pipeline images. The entire lifecycle runs 24/7 autonomously on the Azure VPS (`20.215.232.214`).
- **Master Daemon:** `goal2_sourcing_engine/vps_master_daemon.py` managed by systemd service `obscura-master.service` running under Python virtualenv (`/home/azureuser/ai-ugc/venv/bin/python3`).
- **Continuous 4-Sector Execution Cycle:**
  1. **Sector 0 (Autonomous Sourcing & Sizing):**
     - Scrapes Yupoo albums using seller profiles and anti-ban delays.
     - Resolves Weidian marketplace live inventory via Thor API: true available sizes, real stock counts, CNY pricing, and authentic luxury English colorway mappings.
     - Classifies images via strict binary arbiter (`antigravity_classifier.py` / `image_classifier_v2.py`).
     - Builds 9:16 vertical composites for matching sets.
     - Stages approved bundles into `MANUAL_CURATION/`.
  2. **Sector 1 (Cloud AI Generation):**
     - Autonomous lookbook generation using Google Flow API with OAuth token pool rotation (`google_token_manager.py`).
     - Feeds category-specific primary reference flat lays into zero-brand-name prompts (Runway Backstage, Bed GRWM, Studio Macro).
     - Crops and pads outputs into certified vertical 9:16 (TikTok/Reels) and square 1:1 (IG Feed).
  3. **Sector 2 (Curator Quality Guard):**
     - Gate 3 automated quality inspection (`storefront_curator_guard.py`):
       * Selfie-free check: Rejects any selfie/bathroom mirror artifacts.
       * Resolution check: Minimum 512x512 pixels.
       * MIME alignment: Certified JPEG/WebP formats.
       * Multi-angle bundle completeness: Hero + Back + Details + Size Guide.
  4. **Sector 3 (Catalog Deployment):**
     - Atomic synchronization into Next.js storefront (`storefront/src/data/products.js`).
     - Routes high-resolution assets into `storefront/public/products/<slug>/`.
     - Private supplier links and Chinese variant strings are securely committed to `supplier_mappings.json` for automated fulfillment.

### 6.10 COMPLEX SOURCING EDGE CASES & MULTI-PRODUCT RESOLUTION (MANDATORY RULES)

1. **Matching Sets & Tracksuits (Top + Bottom Co-ords):**
   - **Identification:** Triggered by Chinese keywords (`套装`, `运动套装`, `短袖套装`, `卫衣套装`, `夹克套装`, `套服`), English (`set`, `tracksuit`, `two-piece`, `co-ord`), or Weidian multi-piece SKU options.
   - **Pre-Combined Flat Lay Rule:** If the seller provided an uncensored photo showing both the top and bottom laid flat together (`combined_set`), the pipeline uses this directly as the primary reference.
   - **9:16 Vertical Composite Assembly:** If separate top and bottom flat lays are provided, [`composite_builder.py`](file:///c:/Users/USER/ai%20ugc%20and%20sales/goal2_sourcing_engine/composite_builder.py) stacks them:
     * **Top Front:** Upper 55% of the 1080x1920 canvas.
     * **Bottom Front:** Lower 45% of the 1080x1920 canvas.
     * **Strict Rule:** NEVER invert the order (pants on top of hoodie is strictly prohibited).
   - **Dual Size Charts:** Sets almost always have TWO measurement tables (Top: chest/length/shoulder cm; Bottom: waist/hip/pants length cm).
     * The pipeline preserves both as `size_chart_1.jpg` and `size_chart_2.jpg`.
     * Both charts are attached to `metadata.json` (`images.size_charts = ["size_chart_1.jpg", "size_chart_2.jpg"]`) so the interactive modal displays both Top & Bottom size guides.
   - **Weidian Multi-Tier SKU Pricing (Crucial Anti-Loss Rule):**
     * Sellers on Weidian often post single listings with separate SKUs: Top Only (¥150) vs. Pants Only (¥130) vs. Full Set (¥260).
     * The scraper extracts all `sku_options` and builds `price_tiers = {"set": 260.0, "top": 150.0, "bottom": 130.0}`.
     * For sets, `price_cny` is strictly set to `price_tiers["set"]` (¥260).
     * **NON-NEGOTIABLE:** Never default sets to `min(prices)` (¥130), as this would severely undercharge customers and cause fulfillment loss.

2. **Multiple Products / Sibling Silhouettes in the Same Album:**
   - Yupoo sellers occasionally post an entire capsule collection in one album (e.g. "Vintage Washed Black Collection" containing a T-shirt, a Hoodie, and Sweatpants all in the same color).
   - The classifier detects distinct silhouettes (`distinct_categories`) and flags `has_multiple_products: True`.
   - Distinct silhouettes are recorded in `metadata.json` (`detected_categories = ["top", "bottom"]`) to prevent mixing up back angles or confusing a hoodie as the back of a t-shirt.

3. **Digital Weight Scales & GSM Extraction:**
   - High-end streetwear sellers (ChaosMade, Goat, 3Madman, Taurus) frequently include a photo of the folded garment on a digital kitchen scale (e.g. reading "680g").
   - Spatial geometry classifier extracts the numeric value: `weight_grams: 680`.
   - The pipeline computes estimated fabric density: `gsm = int(weight_grams / 1.5)` (e.g. `450 GSM`).
   - The weight and GSM are written to `metadata.json` for luxury heavyweight copy.
   - **MANDATORY PURGE:** Digital scale photos are classified as `is_discard: True` and strictly PURGED from the public customer storefront gallery.

4. **3M Reflective Flash Comparisons:**
   - Streetwear garments with 3M reflective ink, piping, or logos feature paired photos: one taken in ambient light (looks dark/grey) and one with camera flash (glows bright white).
   - The classifier identifies the flash photo as `reflective_flash_macro`.
   - Prevents the pipeline from mistaking the flash photo as a different colorway or corrupted file.

5. **Reversible / 2-in-1 Garments:**
   - Outerwear jackets that can be worn inside out are classified with Side A (Hero) and Side B (Reversible reverse).
   - Both angles are saved into the catalog gallery with custom badges.

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

---

## 7.35 V2 IMAGE CLASSIFICATION PIPELINE (OCTOBER 2026 — NON-NEGOTIABLE)

### 🎯 Purpose
Bulletproof image classification that replaces the unreliable single-model `auto_image_classifier.py`. Every product image gets classified with a multi-model ensemble before being used for AI generation or storefront listing.

### Architecture: 5-Component Pipeline
```
MANUAL_CURATION/<product>/
    └── *.jpg images (from Discord scraper)
              │
              ▼
┌──────────────────────────────────────────┐
│  1. image_classifier_v2.py (CORE)        │
│     Pre-filter (filename/size/aspect)    │
│     → Gemini Flash primary (litellm 433) │
│     → Qwen3-VL validator (OpenRouter)    │
│     → Reconciliation engine              │
│     → Partial JSON recovery + retry      │
│     Output: image_classification.json    │
└──────────────┬───────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│  2. seller_profiler.py                   │
│     Profiles each Yupoo seller's posting │
│     patterns (image order, backgrounds,  │
│     typical categories). Boosts VLM      │
│     confidence using learned patterns.   │
│     Output: data/seller_profiles.json    │
└──────────────┬───────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│  3. storefront_image_selector.py         │
│     Category-specific waterfall:         │
│     Tops/Bottoms: flat_lay → on_model    │
│     Sets: combined_set → flat_lay        │
│     Jewelry: detail → flat_lay           │
│     Shoes: side_profile → on_foot        │
│     Picks 4-5 images per product.        │
│     Output: storefront_selection.json    │
└──────────────┬───────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│  4. background_enhancer.py               │
│     Replaces white/grey Yupoo backgrounds│
│     with premium dark surfaces via Flow: │
│     black_marble, dark_slate, concrete,  │
│     charcoal_linen, matte_black          │
│     Output: enhanced/ subdirectory       │
└──────────────┬───────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│  5. pipeline_orchestrator.py (CLI)       │
│     --classify  Single product           │
│     --select    Run image selection      │
│     --enhance   Run background enhance   │
│     --full      Full pipeline            │
│     --batch-all All MANUAL_CURATION/     │
│     --profile-all Profile all sellers    │
└──────────────────────────────────────────┘
```

### Classification Taxonomy
```json
{
  "type": "front_flat_lay | back_flat_lay | detail_closeup | size_chart | on_model | combined_set | individual_piece | lifestyle | junk",
  "garment_category": "top | bottom | set | shoes | bag | accessory | jewelry | outerwear",
  "quality_score": 1-10,
  "confidence": "high | medium | low",
  "models_agreed": true/false,
  "flags": ["partial_json_recovery", "disagreement", "low_confidence"]
}
```

### Pre-Filter Rules (No API Calls)
- Filename contains `size` + `chart`/`guide` → `size_chart`
- Filename contains `tag_label` or `weight_scale` → `junk`
- File extension not in `.jpg/.jpeg/.png/.webp` → skip
- Pixel count < 10,000 → `junk` (tiny placeholder)
- Aspect ratio > 2.5:1 → `size_chart`
- **⚠️ NO dimension-based browser screenshot filtering** — overlaps with legitimate scraper viewport sizes (1548×1032, 1702×1276)

### Discord Integration
- All 3 save points in `discord_listener.py` trigger `_classify_product_background()` as a non-blocking `asyncio.create_task()`
- Classification runs after metadata.json write and before Discord confirmation reply
- Results saved to `MANUAL_CURATION/<product>/image_classification.json`

### Seller Profiling Rules
- Each Yupoo seller gets profiled on first scrape by analyzing 5-10 random albums
- Profile includes: typical posting order, backgrounds, image count range, categories offered
- Profile stored in `data/seller_profiles.json`, refreshed every 30 days
- When classifying images from a profiled seller, VLM confidence is boosted based on learned patterns (e.g., if seller always puts front flat lay first, the first image gets a confidence boost for `front_flat_lay`)

---

## 7.4 AUTONOMOUS CLOUD PERSISTENT GENERATION & PROMPT ENGINE (SEPTEMBER 2026)

### ☁️ Infrastructure & Authentication (Zero PC Dependency)
- **Host:** Azure VPS (`20.215.232.214`), Ubuntu 24.04 LTS.
- **Service:** `obscura-generator.service` running `cloud_generator_gha.py --daemon` under `xvfb-run`.
- **Permanent Chrome Session:** Persistent user data directory stored at `/home/azureuser/.obscura_chrome_profile`. Cookies, device tokens, and IndexedDB state for Google Flow Pro are permanently on disk, eliminating session expirations.

### 🎯 Key DOM & Extraction Discoveries (Certified Working)
1. **In-Page Authenticated Extraction (`/asb/` Protocol):**
   - Google Flow serves generated images from `https://flow.google.com/asb/...`.
   - Standard HTTP GET requests (`context.request.get(url)`) fail with HTTP 400 because internal assets require the browser page session origin and headers.
   - **Solution:** Extract images via in-page JavaScript `fetch(target.src)` inside `page.evaluate()`, read blob as Data URL, and decode base64 into raw bytes. 100% reliable, zero 400 errors.
2. **Differential Pre-Generation Snapshotting:**
   - When garments (`front_angle.jpg`) are uploaded as media ingredients, Flow adds the ingredient thumbnail to the canvas.
   - To prevent downloading the uploaded flat lay instead of the generated model shot:
     `existing_srcs = set(page.evaluate("() => Array.from(document.querySelectorAll('img')).map(i => i.src)"))`
     The generator only accepts images whose URL was *not* in `existing_srcs` and has model tile dimensions.
3. **Selector Strictness & Cookie Shield:**
   - Flow's top search bar intercepts generic text typing. All generation inputs must strictly target `flow-prompt-box [contenteditable="true"]` with `force=True`.
   - The white Google cookie banner (`OK, got it`) periodically overlays the bottom prompt box and must be programmatically dismissed before focusing.

### 🚫 MULTIMODAL REFERENCE PROMPT RULE: ZERO TEXT COLLISION (STRICT & NON-NEGOTIABLE)
- **The Core Law:** When referencing a garment flat lay image ingredient chip in Google Flow / Nano Banana Pro, **NEVER** write the brand name (`"OBSCURA"`), specific color names (`"blue"`, `"green"`, `"grey"`), or graphic descriptions in the prompt text.
- **Why (The Collision Problem):**
  1. **Text Hallucination / Watermarking:** If you write `"OBSCURA"` in the prompt, the multimodal image model treats it as a directive to render literal text, stamping `"OBSCURA"`, mock brand typography, or hallucinated graphics onto the garment.
  2. **Embedding Collision:** If you write color names (`"grey"`, `"blue"`, `"black"`), the text token conflicts with the high-dimensional visual embedding of the reference image. If the referenced garment is vintage charcoal washed camo, writing `"black"` or `"OBSCURA"` forces the diffusion model to compromise between the text token and the image chip, generating an entirely different synthetic piece rather than faithfully transferring the real item.
  3. **The Image Reference is the Sole Visual Truth:** The attached flat lay chip already contains 100% of the garment's visual information — color tones, fabric weave, drape, distressing, hardware, zippers, and authentic logos.
- **Mandatory Prompt Syntax:**
  - Refer to the item strictly as: `"the exact garment from the referenced image"`, `"the exact trousers from the referenced image"`, `"the complete matched outfit from the referenced image"`, or `"this product"`.
  - **Do NOT** specify color (`"blue"`, `"green"`, etc.).
  - **Do NOT** specify brand (`"OBSCURA"`, etc.).
  - The text prompt's **ONLY** purpose is to describe: **The model, the pose, the environment / architectural scene, camera lens (e.g. 85mm prime), lighting, and shot composition.**

### 🎨 Creative Prompt Engine & Visual Standards
Every product drop automatically generates three distinct high-converting creative formats (with ZERO brand/color text collision):
1. **Vertical Runway / Brutalist Lookbook (9:16):**
   - High-fashion editorial lookbook photo of model in motion wearing "the exact garment from the referenced image".
   - Brutalist architectural concrete pavilion (Tadao Ando inspired), dramatic natural top skylight, soft shadows.
   - 85mm prime lens photography, Vogue/Balenciaga campaign standard, RAW photo, 8k resolution.
2. **Luxury Editorial Feed Post (1:1):**
   - Waist-up medium shot focusing on garment drape, double-layer hood / lapel structure, and heavy fabric weight.
   - Chiaroscuro directional studio strobe lighting, high-end Parisian Haussmannian luxury interior or concrete plinth.
   - SSENSE campaign quality, 8k RAW photo.
3. **Authentic Social GRWM / Fit-Check Selfie (9:16):**
   - Authentic smartphone mirror selfie or front-camera fit check.
   - Fashion creator holding iPhone in a minimalist Scandinavian penthouse dressing suite, soft morning window light.
   - Highly relatable, organic TikTok/Reels aesthetic driving high-converting social engagement.

### 👕 Warehouse Multi-Piece Outfit Assembly (`outfit_warehouse.py`)
- Automatically pairs complementary tops, bottoms, and footwear staged in `MANUAL_CURATION/` by brand and color family.
- Generates complete unified outfit campaigns where the AI model wears both items simultaneously with matching silhouette stacking and footwear.

### 🧠 VLM Intelligence & Classification Architecture
- **Dual-Phase Classification:** Uses LiteLLM Router cascading across Google Gemini Vision with failover.
- **Model Exclusion Rule:** Human model shots from Yupoo are deleted during classification to prevent contaminating AI generation. Only flat lays, ghost mannequins, detail close-ups, and size charts are retained.
- **Temp-File Protection:** Files are protected against recursive rename collisions (`__temp_classify_*` strip filters).



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

---

## 17. STOREFRONT ASSET COMPRESSION & VERIFIED MULTI-CATEGORY CATALOG (2026 UPDATE)

### A. Non-Negotiable Performance & Image Compression Standard
- **Sub-Second Vercel Load Times:** Zero heavy uncompressed images (>500KB) are allowed in `storefront/public/`.
- **Pillow Compression Pipeline:** All product hero photos, hover backs, detail macros, and editorial stills are converted to RGB progressive JPEGs with max dimension 1200px at 78-82 quality (`optimize=True`, `progressive=True`).
- **Benchmark:** Average image size must stay between 80KB–180KB (max 300KB). Reduces bundle load footprint by 85–93%, eliminating mobile page stalls and network lag.
- **Hero Backgrounds:** Main hero backgrounds (`main_hero_bg.jpg`, `editorial_hero.jpg`) strictly compressed to <200KB.

### B. Verified Multi-Category Catalog Deployment
The storefront is populated with 8 fully verified, curated products spanning all luxury streetwear categories:
1. **Sets:**
   - `208-diplomatic-zipset-washed-camo`: Washed Camo Utility Zipset (480 GSM French Terry, Look 01 Hero).
   - `corteiz-athletic-logo-tracksuit-set`: Athletic Logo Double-Knit Tracksuit Set (420 GSM Interlock Fleece).
2. **Bottoms:**
   - `hellstar-vintage-gradient-flare-sweatpants`: Vintage Gradient Graphic Flare Sweatpants (460 GSM French Terry).
3. **Outerwear:**
   - `represent-owners-club-heavyweight-hoodie`: Owners Club Heavyweight Boxy Hoodie (480 GSM Loopback Fleece, Look 02).
   - `jil-sander-tailored-bomber-jacket`: Structural Tailored Minimalist Bomber (High-Density Milled Twill, Look 03).
4. **Tops:**
   - `essential-heavyweight-500gsm-tee`: Heavyweight 500GSM Structural Boxy Tee (Double-Combed Cotton, Look 04).
5. **Accessories & Objects:**
   - `palace-heritage-logo-baseball-cap`: Heritage Logo Six-Panel Baseball Cap (Heavy Washed Cotton Twill).
   - `monogram-denim-slouch-hobo-bag`: Denim Monogram Slouch Hobo Bag (Washed Selvedge Jacquard Denim).

### C. Comprehensive Multi-Angle Asset Bundle per Product
Every product in `storefront/src/data/products.js` has complete assets in `storefront/public/products/<slug>/`:
- **Primary Hero:** Front flat lay (`front.jpg`)
- **Secondary Hover:** Back flat lay (`back.jpg`)
- **Craftsmanship Inspection:** 3 to 5 detail macros (`detail_1.jpg` – `detail_5.jpg`)
- **Sizing Guide Modal:** Official seller measurement table image (`size_chart.jpg` or `size_chart_1.jpg`, `size_chart_2.jpg`)
- **Editorial Lookbook Stills:** 2 Vogue-standard on-model editorial stills (`lookbook_1.jpg`, `lookbook_2.jpg`)

### D. Zero Pretentious Jargon
- Never use words like "atelier" in customer-facing copy or developer prompts. Use clean, direct terms like "studio", "piece", and "collection".






