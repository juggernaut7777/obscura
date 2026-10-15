# 📋 COPILOT_BRIEF.md — Handover Brief for GitHub Copilot

> **Date:** October 15, 2026  
> **Target:** GitHub Copilot (New Main Agent Handler)  
> **Repository:** `ai ugc and sales`  
> **Live Storefront (Vercel):** `https://obscura-git-main-davids-projects-e169ae09.vercel.app`  
> **Azure VPS Runner:** `20.215.232.214` (user `azureuser`)

---

## 1. WHAT THIS PROJECT IS

**OBSCURA** is an AI-powered luxury fashion and streetwear brand.
- **Resale Model:** Curate independent streetwear & designer blanks from Chinese suppliers, generate luxury Vogue/Balenciaga editorial lookbook photos using AI, and sell them through a custom Next.js storefront.
- **The Sourcing Pipeline:**
  1. **Yupoo** (`deateath.x.yupoo.com`, etc.) = High-resolution uncensored product showcase. This is where ALL product photos and front flat lays for AI generation come from.
  2. **Weidian / Taobao / 1688** = Private purchase backend. This is where live pricing, inventory, sizing charts, and authentic Chinese colorway strings come from.
  3. **AI Generation** = Front flat lay of the garment is referenced to generate on-model editorial runway and lookbook photography.
  4. **Storefront (`storefront/`)** = Next.js 16 app deployed on Vercel.

---

## 2. STRICT USER REQUIREMENTS & CONSTRAINTS

The project owner has strict preferences that you **must follow at all times**:
1. **NO JARGON / NO "ATELIER"**: Never insert the word "atelier" anywhere in code, copy, titles, or prompt strings. Keep everything concise, modern, and direct luxury streetwear style (e.g., `Studio`, `Archive`, `Editorial`, `Runway`).
2. **STRICT 1-TO-1 COLOR INTEGRITY**: 
   - Every colorway in `storefront/src/data/products.js` MUST contain ONLY photos of that specific color.
   - Example: The Black variant must only contain black garment images. The White variant must only contain white garment images. Never mix them.
3. **NO LOCAL DOWNLOAD POLLUTION**:
   - Do not dump big image scrapes or test files onto the user's local personal folders.
   - Live product assets belong strictly in `storefront/public/products/<slug>/`.
   - Storefront updates must push to `git` $\rightarrow$ GitHub $\rightarrow$ Vercel.
4. **VERIFIED SIZING**:
   - Product sizing and size charts must reflect the actual measurements (shoulder, chest/bust, length, sleeve in cm) from the supplier, translated cleanly into English.

---

## 3. CURRENT PROJECT STATE (OCTOBER 2026)

### What Was Just Completed:
1. **Full Storefront Cleanout:**
   - All 8 stale/pre-wipe test directories were purged from `storefront/public/products/`.
   - Caching headers were added to `next.config.mjs` for fast loading.
   - Next.js link prefetching was optimized to eliminate browser network lag.
   - All legacy "atelier" strings were removed from `storefront/src/app/product/[id]/page.js`.
2. **Fresh Product Ingestion (Deateath):**
   - **Product:** `Inverted Triangle Minimalist Tee` (`deateath-prada-inverted-triangle-tee`).
   - Sourced from Deateath Yupoo (`deateath.x.yupoo.com`) + Weidian ID `7875367148`.
   - Live Weidian price: 88 CNY (~$85 USD retail).
   - Available sizes: `["M", "L", "XL", "2XL", "3XL"]`.
   - Colorways:
     - **Washed Black** (`#141416`): 7 dedicated black photos (hero front, AI lookbook runway still, back, logo macro, neckline tags, on-model front, on-model back).
     - **Chalk White** (`#F5F5F7`): 5 dedicated white photos (hero front, AI lookbook runway still, front angle 2, logo macro, side-by-side overview).
   - Interactive Size Guide modal wired with exact centimeter measurements and the supplier's measurement chart.
3. **Build & Test Verification:**
   - Local `next build` compiled all 17 routes cleanly with Turbopack.
   - Playwright automated browser tests verified that clicking Black shows 100% black images and clicking White shows 100% white images with zero bleed.

---

## 4. KEY REPOSITORY MAP

```
ai ugc and sales/
├── .github/
│   ├── copilot-instructions.md   # Automatic instructions loaded into Copilot
│   └── workflows/                # Cloud lookbook automation workflow
├── storefront/                   # Next.js 16 Storefront app
│   ├── public/products/          # Live product images by slug
│   │   └── deateath-prada-inverted-triangle-tee/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.js           # Home page (split-screen Vogue hero + archive)
│   │   │   ├── shop/page.js      # Filterable catalog & search
│   │   │   ├── product/[id]/     # Product detail page (color swatches, try-on modal)
│   │   │   └── lookbook/page.js  # Runway editorial lookbook & outfit builder
│   │   └── data/
│   │       └── products.js       # Live catalog: DEMO_PRODUCTS, CATEGORIES, COLLECTIONS, DEMO_OUTFITS
│   └── package.json
├── goal2_sourcing_engine/        # Python backend engine
│   ├── MANUAL_CURATION/          # Staged approved products and classification summaries
│   ├── image_classifier_v2.py    # Spatial geometry classifier (Gemini Vision)
│   ├── cloud_generator_gha.py    # Autonomous cloud lookbook generator
│   └── .env                      # API keys (Gemini, LiteLLM, Groq, NVIDIA)
├── AGENTS.md                     # Detailed 1,200-line master architecture file
├── COPILOT_BRIEF.md              # This handover brief
└── verify_storefront_live.py     # Playwright integration verification script
```

---

## 5. HOW TO CONTINUE WORK IN COPILOT

When the user asks you to perform a task:
1. **To add a new product:**
   - Scrape Yupoo album for images $\rightarrow$ place in `storefront/public/products/<slug>/`.
   - Scrape Weidian/1688 for price, available sizes, and color names.
   - Generate AI lookbook stills referencing the front flat lay.
   - Add entry to `DEMO_PRODUCTS` in `storefront/src/data/products.js`.
   - Ensure each color in `colors` has strictly isolated images.
2. **To test changes:**
   - Run `npm run build` inside `storefront` to verify compilation.
   - Run `python verify_storefront_live.py` to confirm visual and colorway integrity.
3. **To deploy:**
   - Commit changes and push to `origin main` to trigger automatic Vercel deployment.
