# GitHub Copilot Instructions — OBSCURA Luxury AI Fashion Pipeline

> **Repository:** `ai ugc and sales`  
> **Brand:** OBSCURA — AI-powered luxury streetwear catalog, lookbook, and resale business.  
> **Last Synchronized:** October 2026

---

## 1. CORE MISSION & ARCHITECTURE

OBSCURA operates a two-platform luxury streetwear pipeline:
1. **Yupoo (Showcase & Images):** Chinese suppliers post uncensored, high-resolution product photos showing visible brand logos and detailed stitching. **ALL product photos and visual references for AI lookbook generation MUST come from Yupoo.**
2. **Weidian / Taobao / 1688 (Transaction Backend):** Marketplace listings contain the actual purchase link, live stock numbers, available sizes, and authentic Chinese colorway strings.
3. **OBSCURA Storefront (`storefront/`):** Next.js 16 app deployed on Vercel (`https://obscura-git-main-davids-projects-e169ae09.vercel.app`). Displays the unified product catalog with segregated colorways, size guides, and high-fashion editorial lookbook photography.
4. **Autonomous Backend (Azure VPS `20.215.232.214`):** Runs the master scraping daemon, image classifier, and AI generation pipeline.

---

## 2. STRICT USER RULES & CONSTRAINTS (NON-NEGOTIABLE)

Whenever you generate code, write descriptions, or assist with this repository, enforce these rules without exception:

### Rule 1: No Hallucinated Jargon ("Atelier")
- **NEVER use the word "atelier"** in user-facing text, UI headers, descriptions, prompts, or commit messages.
- Use clean, premium terms: `Studio`, `Archive`, `Editorial`, `Runway`, `Drop`, `Lookbook`.

### Rule 2: Strict 1-to-1 Color Integrity (Zero Color Mixing)
- When defining products in `storefront/src/data/products.js`, **each colorway in `colors` MUST have its own dedicated array of images showing ONLY that color.**
- **NEVER** put photos of one color (e.g., white) inside another colorway (e.g., black).
- In `ProductPage` (`storefront/src/app/product/[id]/page.js`), clicking a color swatch switches `activeColorImages` to show ONLY that color's photos.

### Rule 3: Yupoo vs. Marketplace Separation
- **Images:** Scraped from Yupoo albums (uncensored).
- **Metadata:** Scraped from Weidian/1688 (sizes, stock, Chinese variant names mapped to English luxury color names like *Washed Black*, *Chalk White*, *Mineral Olive*).
- **Front Flat Lay Only for AI:** When using an image as reference for AI generation, strictly use the **front flat lay** (full uncropped garment). Never use back angles, detail macros, or size charts as generation inputs.

### Rule 4: Zero Local Disk Pollution
- Do not download loose images or huge datasets into local user folders.
- Customer-facing assets belong strictly in `storefront/public/products/<product-slug>/`.
- The live store is deployed via `git push origin main` $\rightarrow$ GitHub $\rightarrow$ Vercel.

---

## 3. FILE MAP & DIRECTORY STRUCTURE

| Path | Purpose |
|------|---------|
| `storefront/src/data/products.js` | Product catalog exports: `DEMO_PRODUCTS`, `CATEGORIES`, `COLLECTIONS`, `DEMO_OUTFITS`. |
| `storefront/public/products/<slug>/` | Static image bundles per product (front, back, details, lookbook, size chart). |
| `storefront/src/app/product/[id]/page.js` | Product detail page with interactive color swatches, size guide modal, and model try-on. |
| `storefront/src/app/lookbook/page.js` | Editorial lookbook page with outfit builder. |
| `storefront/src/app/shop/page.js` | Shop catalog with category filters and instant search. |
| `goal2_sourcing_engine/` | Core Python engine (Yupoo scraper, classifier, token manager, cloud generator). |
| `AGENTS.md` | Comprehensive 1,200-line master architecture file. |

---

## 4. CURRENT CATALOG STATE (OCTOBER 2026)

- All 8 legacy pre-wipe test folders have been purged from `storefront/public/products/`.
- Active fresh drop: **`deateath-prada-inverted-triangle-tee`**
  - Supplier: Deateath Yupoo (`deateath.x.yupoo.com`) + Weidian ID `7875367148`.
  - Colors: **Washed Black** (7 dedicated images) & **Chalk White** (5 dedicated images).
  - Sizes: `M`, `L`, `XL`, `2XL`, `3XL` with real measurement table in the interactive Size Guide modal.
  - Price: $85 (compare at $120).
  - High-fashion runway lookbook stills: `lookbook_black.jpg` and `lookbook_white.jpg`.

---

## 5. ESSENTIAL COMMANDS

```bash
# Test storefront build locally
cd storefront
npm run build

# Run local preview server
npm run start -- -p 3000

# Commit and deploy live to Vercel
git add .
git commit -m "feat: update catalog"
git push origin main
```
