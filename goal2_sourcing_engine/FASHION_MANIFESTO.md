# 👠 AUTONOMOUS FASHION PIPELINE: THE ELITE MANIFESTO

## 1. CORE AESTHETIC PRINCIPLES (NON-NEGOTIABLE)
- **High-End Editorial Only:** Every image must look like it belongs in *Vogue*, *Harper's Bazaar*, or a *Balenciaga* campaign.
- **Sharp Backgrounds (No Amateur Blur):** No heavy bokeh/background blur. The environment is as important as the model. Use deep depth of field (f/8 - f/11).
- **Global Locations:** Exotic, luxury, or high-contrast urban settings (Marrakech architecture, Dubai glass & steel, Fuerteventura volcanic sands, Parisian grand apartments).
- **Cinematic Lighting:** Sculpted, intentional lighting. Use snoots, rim lights, and high-contrast strobes. No flat, boring "natural light" unless it's golden hour in a luxury location.
- **Hyper-Realism:** Visible skin pores, authentic textures. No "plastic" or "AI-smooth" looking skin.

## 2. GENDER & STYLE ACCURACY
- **Strict Gender Matching:** Male products on Male models. Female products on Female models. NO exceptions (e.g., no crop tops on men unless specifically designed as such).
- **Outfit Styling:** If the product is just an accessory or a single piece (shoes, hats, tops), the AI MUST design a complete, complementary high-fashion outfit to match. Do NOT use the model's base reference clothing.
- **Correct References:** The product must match the reference image EXACTLY.

## 3. PIPELINE INTEGRITY
- **Scrape First, Generate Later:** Only generate images for products that have been fresh-scraped and have high-res source images.
- **No Test Products:** Delete all test images immediately after verification. Never use "red_hoodie" or "black_cargo_pants" placeholders in production.
- **Mandatory Review:** All images must be saved to a `review_pending` directory. Nothing goes to the website or socials without explicit user approval.

## 4. IMAGE QUALITY
- **Raw PNG Only:** No compressed JPEGs or WebP. Direct-to-folder raw file management.
- **High Resolution:** Minimum 1024x1024 or higher depending on Flow API limits.
