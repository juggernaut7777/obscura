#!/usr/bin/env python3
"""
cloud_generator_gha.py - OBSCURA Autonomous Cloud Lookbook Generator for Azure VPS & GitHub Actions
================================================================================================
Fully autonomous generation engine running on Azure VPS & GitHub Actions cloud runners:
  1. Real Garment Referencing (Rule 36): Scraped flat lays uploaded as Flow media ingredients.
  2. Creative Editorial & Social Suite:
     - 9:16 Vertical Runway / Brutalist Lookbook (Vogue/Balenciaga editorial standard)
     - 1:1 Square Editorial Post (SSENSE / Luxury drape & seam macro craftsmanship)
     - 9:16 Authentic Social GRWM / Fit-Check (Lifestyle influencer mirror selfie / fit check)
  3. Pre-Generation Canvas Snapshotting: Differential detection guarantees only new outputs are downloaded.
  4. In-Page Authenticated Extraction: In-browser fetch() eliminates HTTP 400 errors for /asb/ assets.
  5. Dual-Platform Formatting via Pillow: True 9:16 Vertical (TikTok/Reels) & 1:1 Square (IG Posts).
  6. Omni Flash 10s UGC Video Brief Synthesis (ugc_video_brief.json with native speech script).
  7. Warehouse Outfit Integration: Seamlessly generates multi-piece ensembles (outfit_warehouse.py).
  8. Human-like anti-ban pacing & randomized jitter delays.
  9. Permanent 24/7 Daemon Support (--daemon / --loop).
"""

import os
import sys
import time
import json
import glob
import re
import io
import base64
import random
import shutil
import argparse
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
CURATION_DIR = BASE_DIR / "MANUAL_CURATION"
OUTPUT_DIR = BASE_DIR / "OUTPUT_READY_FOR_SALE"
SESSION_FILE = BASE_DIR / "sessions" / "session_google_account.json"
QUEUE_FILE = BASE_DIR / "queue_pending.json"
DEFAULT_PROFILE = "/home/azureuser/.obscura_chrome_profile"
PROJECT_URL = os.getenv("GFLOW_PROJECT_URL", "https://flow.google.com/project/48c3aa27-e5a0-4630-9f37-595f9a0d9e1e")


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def safe_log(msg):
    t = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{t}] {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)

def sanitize_slug(name):
    clean = re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean[:50] or "product"

def anti_ban_sleep(min_sec=15, max_sec=30, reason="Anti-ban pacing"):
    delay = random.uniform(min_sec, max_sec)
    safe_log(f"    [Pacing] Sleeping {delay:.1f}s ({reason})...")
    time.sleep(delay)

def detect_category(name, meta):
    cat = (meta.get("product_category") or "").lower()
    if cat in ["top", "tops", "hoodie", "tee", "jacket", "shirt", "sweater"]:
        return "tops"
    if cat in ["bottom", "bottoms", "pants", "cargo", "jeans", "shorts", "sweatpants"]:
        return "bottoms"
    if cat in ["shoe", "shoes", "sneakers", "boots", "loafers", "heels", "sandals"]:
        return "shoes"
    if cat in ["bag", "bags", "backpack", "tote", "duffle"]:
        return "bags"
    if cat in ["accessory", "accessories", "hat", "cap", "belt", "necklace", "ring", "glasses"]:
        return "accessories"

    n = (name or "").lower()
    if any(k in n for k in ["hoodie", "jacket", "tee", "shirt", "sweater", "zipset", "coat"]):
        return "tops"
    if any(k in n for k in ["pant", "trouser", "cargo", "jean", "short", "sweatpant"]):
        return "bottoms"
    if any(k in n for k in ["shoe", "sneaker", "boot", "loafer", "dunk", "jordan", "runner", "sandal", "heel"]):
        return "shoes"
    if any(k in n for k in ["bag", "tote", "backpack", "duffle"]):
        return "bags"
    return "tops"

def build_category_prompts(category, name=None, color=None, is_outfit=False, outfit_details=None):
    """
    MULTIMODAL REFERENCE PROMPT ENGINE:
    The garment flat lay is attached as an ingredient chip in Google Flow.
    The multimodal model derives 100% of color, fabric texture, cut, logos,
    and graphics from the reference image chip.
    NEVER include the brand name ('OBSCURA'), specific color names ('grey', 'blue'),
    or text graphics in the prompt, as this causes catastrophic prompt collision,
    hallucinated text watermarks/prints, and degrades reference fidelity.
    Refer strictly to 'the exact garment from the referenced image' or 'this product'.
    """
    prompts = {}

    if is_outfit:
        prompts["tiktok_9_16"] = (
            "Full-length vertical 9:16 high-fashion editorial runway lookbook photo of a female model wearing "
            "the complete matched outfit from the referenced image. Model striding through a massive minimalist "
            "brutalist concrete architectural hall with dramatic natural top skylight and soft architectural shadows. "
            "Highsnobiety and Vogue campaign aesthetic, sharp 85mm prime portrait lens, 8k resolution, raw photo."
        )
        prompts["ig_feed_post"] = (
            "Square 1:1 waist-up luxury editorial lookbook photo of a high-fashion model wearing "
            "the complete matched outfit from the referenced image. Dramatic chiaroscuro studio lighting "
            "highlighting the realistic fabric drape, weight, and tailored seam architecture. "
            "Balenciaga campaign standard, raw photo, 8k resolution."
        )
        prompts["grwm_fit_check"] = (
            "Authentic vertical 9:16 smartphone mirror selfie fit-check photo of a stylish model wearing "
            "the complete matched outfit from the referenced image. Model standing in a chic minimalist Scandinavian "
            "dressing suite, holding smartphone naturally. Warm morning window light, authentic TikTok UGC aesthetic, ultra-realistic."
        )
        return prompts

    if category == "tops":
        prompts["tiktok_9_16"] = (
            "Full-length vertical 9:16 high-fashion editorial lookbook photo of a female model wearing "
            "the exact garment from the referenced image. Model standing in a minimalist brutalist architectural concrete pavilion "
            "with subtle natural daylight. Paired with plain neutral tailored dark trousers and clean chunky boots. "
            "Editorial styling, sharp 85mm prime lens photography, Vogue editorial lighting, raw photo, 8k resolution."
        )
        prompts["ig_feed_post"] = (
            "Medium waist-up high-fashion editorial photo of a model wearing the exact garment from the referenced image. "
            "Cinematic rim lighting emphasizing the heavy fabric drape, structured collar, and seam finishings. "
            "Minimalist concrete gallery setting. Square 1:1 composition, Balenciaga campaign aesthetic, 85mm portrait, raw photo, 8k resolution."
        )
        prompts["grwm_fit_check"] = (
            "Authentic vertical 9:16 smartphone mirror selfie fit-check photo of a stylish model wearing "
            "the exact garment from the referenced image. Model standing in a minimalist bedroom loft with soft golden-hour "
            "natural daylight, holding smartphone casually. Authentic influencer GRWM fit-check aesthetic, raw organic texture, ultra-realistic."
        )
    elif category == "bottoms":
        prompts["tiktok_9_16"] = (
            "Full-body vertical 9:16 street-editorial lookbook photo of a model wearing the exact trousers from the referenced image. "
            "Styled with a minimal plain black boxy cropped tee and clean brutalist boots. Urban architectural concrete setting "
            "with dramatic natural side-lighting. Crisp focus on silhouette, fabric texture, and clean hem stacking. "
            "Vertical 9:16 composition, Highsnobiety aesthetic, raw photo."
        )
        prompts["ig_feed_post"] = (
            "Lower-body 1:1 square editorial shot focusing on the exact trousers from the referenced image in motion. "
            "Subtle dynamic stride in a modern brutalist pavilion. Morning architectural shadows highlighting twill texture and pockets. "
            "Square 1:1 framing, luxury editorial campaign standard, raw photo, 8k."
        )
        prompts["grwm_fit_check"] = (
            "Authentic vertical 9:16 front-camera selfie fit-check video frame of a fashion creator testing the drape and silhouette "
            "of the exact trousers from the referenced image. Creator holding phone angled down to capture trouser break "
            "and clean hem stacking over shoes. Modern aesthetic interior, daylight, authentic UGC style."
        )
    elif category == "shoes":
        prompts["tiktok_9_16"] = (
            "Vertical 9:16 high-fashion on-foot editorial photo of a model wearing the exact shoes from the referenced image. "
            "Paired with wide-leg neutral tailored wool trousers that break cleanly over the shoe silhouette. "
            "Minimalist polished concrete floor with soft studio rim light. Vertical 9:16 angle, SSENSE lookbook quality, raw photo."
        )
        prompts["ig_feed_post"] = (
            "Dynamic close-up on-foot 1:1 editorial photo of the exact shoes from the referenced image stepping forward. "
            "Brutalist stone surface with cinematic soft shadows. Crisp material texture, sculpted sole lines, and meticulous stitching. "
            "Square 1:1 crop, Vogue runway quality, 8k raw photo."
        )
        prompts["grwm_fit_check"] = (
            "Authentic vertical 9:16 smartphone unboxing and on-foot fit-check photo of the exact shoes from the referenced image. "
            "Model standing on a clean light oak hardwood floor in a dressing room, angled top-down mirror view. Natural daylight, clean aesthetic."
        )
    elif category == "bags":
        prompts["tiktok_9_16"] = (
            "Vertical 9:16 high-fashion editorial photo of a model in a minimalist charcoal coat, effortlessly carrying "
            "the exact bag from the referenced image over their arm. Architectural museum gallery setting with ambient soft daylight. "
            "Tactile focus on leather grain, edge finish, and brushed hardware. Vertical 9:16 framing, Vogue editorial, raw photo."
        )
        prompts["ig_feed_post"] = (
            "Luxury editorial still life photo of the exact bag from the referenced image positioned on an Italian travertine marble block. "
            "Clean diffused morning side-light highlighting the supple material drape and brushed hardware. Square 1:1 format, raw photo."
        )
        prompts["grwm_fit_check"] = (
            "Authentic vertical 9:16 mirror selfie of a creator styling the exact bag from the referenced image as part of their daily luxury outfit. "
            "Handheld smartphone aesthetic, aesthetic Paris loft background, natural soft illumination."
        )
    else:
        prompts["tiktok_9_16"] = (
            "Vertical 9:16 high-fashion close-range editorial portrait of a model wearing the exact accessory from the referenced image. "
            "Dramatic cinematic side-lighting with soft shadows. Ultra-sharp focus on the accessory detailing, metallic luster, "
            "and luxury finishing. Vertical 9:16 composition, Vogue editorial standard, raw photo."
        )
        prompts["ig_feed_post"] = (
            "Macro editorial commercial product photo of the exact luxury accessory from the referenced image displayed on a minimalist textured "
            "volcanic stone plinth. Crisp overhead directional strobe emphasizing micro-engravings, brushed metal bevels, and craftsmanship. "
            "Square 1:1 centered composition, SSENSE campaign quality, 8k resolution, raw photo."
        )
        prompts["grwm_fit_check"] = (
            "Authentic vertical 9:16 close-up selfie of a model putting on the exact piece from the referenced image during their morning GRWM routine. "
            "Natural mirror reflection, warm sunlight, authentic creator aesthetic."
        )

    return prompts

def build_ugc_video_brief(category, name=None, color=None):
    scripts = {
        "tops": (
            "Stop buying thin, overpriced blanks. This heavyweight piece just dropped and the drape is unreal. "
            "Double-layer cotton, raw dropped shoulders, perfectly tailored cut. Link in bio to cop the drop."
        ),
        "bottoms": (
            "Finding pants that stack cleanly without bunching is nearly impossible. "
            "These trousers are engineered with structured utility lines and custom heavyweight twill. Link in bio."
        ),
        "shoes": (
            "On-foot check: the new luxury silhouette. Custom sculpted sole, premium materials, and unmatched all-day comfort. Link in bio."
        ),
        "bags": (
            "The everyday luxury piece you've been looking for. Architectural bag in textured leather with heavy brushed hardware. Link in bio."
        ),
        "accessories": (
            "Details make or break an outfit. This custom piece brings instant subtle luxury. Engineered micro-finish, weighted feel. Link in bio."
        )
    }
    script = scripts.get(category, scripts["tops"])
    video_prompt = (
        f"Authentic front-camera 9:16 smartphone fit-check video of a fashion creator showing off the exact {category} item "
        "from the referenced image. Creator speaks naturally to camera, turns 360 degrees to demonstrate fabric drape and tailored fit. "
        "Natural daylight, handheld subtle movement, genuine social media UGC aesthetic, 10s video length with synchronized native speech."
    )
    return {
        "duration_seconds": 10,
        "format": "9:16 vertical",
        "model_engine": "Omni Flash (veo_3_1_i2v_lite)",
        "script": script,
        "video_prompt": video_prompt
    }

def process_and_audit_image(data: bytes, format_key: str, out_path: Path) -> tuple[bool, str]:
    if len(data) < 20000:
        return False, f"File size too small ({len(data)} bytes)"
    if b"<html" in data[:100].lower() or b"<!doctype" in data[:100].lower():
        return False, "HTML error page received"

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        w, h = img.size
        if w < 200 or h < 200:
            return False, f"Image dimensions too small ({w}x{h})"

        if img.mode in ("RGBA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size
        target_ratio = (9.0 / 16.0) if ("tiktok" in format_key or "grwm" in format_key) else 1.0
        current_ratio = w / h

        if abs(current_ratio - target_ratio) > 0.02:
            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                img = img.crop((left, 0, left + new_w, h))
            else:
                new_h = int(w / target_ratio)
                top = (h - new_h) // 2
                img = img.crop((0, top, w, top + new_h))

        img.save(str(out_path), "WEBP", quality=95, method=6)
        final_w, final_h = img.size
        return True, f"Formatted {final_w}x{final_h} WebP (Ratio: {final_w/final_h:.3f})"
    except Exception as e:
        return False, f"Pillow processing error: {e}"

def find_pending_products(limit=5):
    pending = []

    # Check for warehouse matched outfits first (Track 2)
    try:
        from outfit_warehouse import find_ready_outfits
        ready_outfits = find_ready_outfits()
        for o in ready_outfits:
            if not o.get("generated"):
                pending.append((None, {
                    "is_outfit": True,
                    "product_name": o.get("name", "Warehouse Complete Outfit"),
                    "outfit_details": o,
                    "product_category": "outfit"
                }))
                if len(pending) >= limit:
                    return pending
    except Exception:
        pass

    if QUEUE_FILE.exists():
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue_data = json.load(f)
            for item in queue_data:
                dname = item.get("dir_name") or item.get("product_name")
                pdir = CURATION_DIR / dname
                if pdir.exists():
                    meta_file = pdir / "metadata.json"
                    meta = {}
                    if meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as mf:
                                meta = json.load(mf)
                        except Exception:
                            pass
                    if meta.get("generation_status") != "complete":
                        pending.append((pdir, meta))
                        if len(pending) >= limit:
                            return pending
        except Exception as e:
            safe_log(f"[!] Error reading queue_pending.json: {e}")

    dirs = glob.glob(str(CURATION_DIR / "*"))
    for d in sorted(dirs):
        pdir = Path(d)
        if not pdir.is_dir() or pdir.name.startswith(("_", ".")):
            continue
        meta_file = pdir / "metadata.json"
        meta = {}
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
            except Exception:
                pass
        if meta.get("generation_status") != "complete":
            # Avoid duplicate folders already in queue
            if not any(item[0] and item[0].name == pdir.name for item in pending):
                pending.append((pdir, meta))
                if len(pending) >= limit:
                    return pending

    return pending

def enter_flow_studio_if_needed(page, project_url=None):
    safe_log(f"    [Studio Gate] Checking page: URL={page.url} | Title={page.title()}")

    # Dismiss Google cookie banner
    try:
        page.evaluate('''() => {
            const b = document.getElementById("glue-cookie-notification-bar-1");
            if (b) b.remove();
            const btns = Array.from(document.querySelectorAll('button, a'));
            for (const btn of btns) {
                const txt = (btn.textContent || '').trim();
                if (txt.includes('OK, got it') || txt.includes('Accept all') || txt.includes('Close')) {
                    btn.click();
                }
            }
        }''')
    except Exception:
        pass

    if "/about" in page.url or "flow.google.com" not in page.url or "/project/" not in page.url:
        page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('a, button, [role="button"]'));
            const createBtn = btns.find(b => (b.textContent || '').includes('Create with Google Flow'));
            if (createBtn) createBtn.click();
        }''')
        page.wait_for_timeout(6000)

        if project_url and ("/about" in page.url or "flow.google.com" in page.url):
            try:
                page.goto(project_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(6000)
            except Exception:
                pass

def generate_product_campaign(context, page, product_dir, meta):
    is_outfit = meta.get("is_outfit", False)
    name = meta.get("product_name") or (product_dir.name if product_dir else "OBSCURA Drop")
    color = meta.get("classified_summary", {}).get("primary_color") or meta.get("color") or ""
    category = "outfit" if is_outfit else detect_category(name, meta)

    slug = f"{int(time.time())}_{sanitize_slug(name)}"
    campaign_dir = OUTPUT_DIR / slug
    campaign_dir.mkdir(parents=True, exist_ok=True)

    safe_log(f"\n========================================================")
    safe_log(f"🎯 STARTING REFERENCED CAMPAIGN: {name}")
    safe_log(f"   Category: {category} | Color: {color} | Slug: {slug}")
    safe_log(f"========================================================")

    # 1. Resolve flat lay reference image
    ref_image = None
    if product_dir:
        for pref in ["front_angle.jpg", "front.jpg", "flat_lay_1.jpg", "flat_lay.jpg"]:
            cand = product_dir / pref
            if cand.exists():
                ref_image = str(cand)
                break
        if not ref_image:
            jpgs = list(product_dir.glob("*.jpg"))
            if jpgs:
                ref_image = str(jpgs[0])

    # 2. Upload garment reference as ingredient if available
    if ref_image and os.path.exists(ref_image):
        safe_log(f"[*] Attaching garment reference ingredient: {Path(ref_image).name}...")
        try:
            # Clear old chips in prompt box
            page.evaluate('''() => {
                const closeBtns = Array.from(document.querySelectorAll('.cdk-overlay-container button, [aria-label*="Remove"], [aria-label*="Clear"], [aria-label*="close"]'));
                for (const b of closeBtns) b.click();
            }''')
            page.wait_for_timeout(500)

            # Open ingredients menu
            ing_btn = page.locator('button[aria-label="Add ingredients to the prompt box"]').first
            if ing_btn.is_visible():
                ing_btn.click()
                page.wait_for_timeout(1500)

                upload_btn = page.locator('button:has-text("Upload media"), div:has-text("Upload media"), span:has-text("Upload media")').last
                with page.expect_file_chooser(timeout=15000) as fc_info:
                    upload_btn.click()
                file_chooser = fc_info.value
                file_chooser.set_files(ref_image)
                safe_log(f"    [+] Reference file set. Waiting 12s for ingestion...")
                page.wait_for_timeout(12000)

                # Select the uploaded item in the ingredients modal
                page.evaluate('''() => {
                    const els = Array.from(document.querySelectorAll('div, li, button'));
                    const target = els.find(e => (e.textContent || '').trim().startsWith('front_angle.jpg'));
                    if (target) target.click();
                }''')
                page.wait_for_timeout(1000)

                add_btn = page.locator('button:has-text("Add to prompt")').first
                if add_btn.is_visible():
                    add_btn.click()
                    safe_log("    [+] Garment ingredient attached to prompt box!")
                    page.wait_for_timeout(1500)
        except Exception as ue:
            safe_log(f"    [!] Note on ingredient upload: {ue}")

    prompts_by_format = build_category_prompts(
        category, name, color,
        is_outfit=is_outfit,
        outfit_details=meta.get("outfit_details")
    )
    ugc_brief = build_ugc_video_brief(category, name, color)
    saved_images = []

    for format_key, prompt in prompts_by_format.items():
        if "tiktok" in format_key:
            format_label = "TikTok/Reels Runway Lookbook (9:16)"
        elif "grwm" in format_key:
            format_label = "Social GRWM / Fit-Check Selfie (9:16)"
        else:
            format_label = "Instagram Luxury Feed Post (1:1)"

        safe_log(f"\n[*] Generating format: {format_label}...")
        safe_log(f"    Prompt: {prompt[:90]}...")

        # Step A: Pre-generation snapshot of existing /asb/ canvas image URLs
        existing_srcs = set(page.evaluate('''() => {
            return Array.from(document.querySelectorAll('img'))
                .map(i => i.src)
                .filter(s => s && s.includes('/asb/'));
        }'''))
        safe_log(f"    [Snapshot] Recorded {len(existing_srcs)} existing canvas tiles.")

        # Dismiss cookie banner if it reappeared
        try:
            page.evaluate('''() => {
                const ok = Array.from(document.querySelectorAll('button')).find(btn => (btn.textContent || '').includes('OK, got it'));
                if (ok) ok.click();
            }''')
        except Exception:
            pass

        # Step B: Focus ProseMirror editor and type prompt (preserving any attached chips)
        try:
            page.evaluate('''() => {
                const box = document.querySelector('flow-prompt-box, flow-rich-text-editor');
                if (box) {
                    const edit = box.querySelector('[contenteditable="true"], .prosemirror-editor');
                    if (edit) {
                        edit.focus();
                        const p = edit.querySelector('p') || edit;
                        const sel = window.getSelection();
                        const range = document.createRange();
                        range.selectNodeContents(p);
                        range.collapse(false);
                        sel.removeAllRanges();
                        sel.addRange(range);
                    }
                }
            }''')
            page.wait_for_timeout(400)
            page.keyboard.type(" " + prompt, delay=10)
            page.wait_for_timeout(600)
        except Exception as ee:
            safe_log(f"    [!] Editor note: {ee}")

        # Step C: Submit generation
        safe_log("    Submitting generation request...")
        try:
            gen_btn = page.locator("flow-prompt-box button[aria-label='Start generation'], flow-prompt-box button:has-text('arrow_forward')").first
            if gen_btn.is_visible() and gen_btn.is_enabled():
                gen_btn.click(force=True, no_wait_after=True, timeout=3000)
            else:
                page.keyboard.press("Enter")
        except Exception:
            pass

        # Step D: Poll for the NEW generated image on canvas (up to 65s)
        safe_log("    Waiting for Nano Banana Pro generation...")
        new_img_src = None
        for s in range(1, 65):
            time.sleep(1.0)
            if s % 10 == 0:
                safe_log(f"    ... {s}s elapsed")

            # Check if a new /asb/ image has appeared on the canvas that was NOT in existing_srcs
            found_src = page.evaluate('''((existing) => {
                const imgs = Array.from(document.querySelectorAll('img')).filter(i => (i.src || '').includes('/asb/'));
                for (const img of imgs) {
                    if (!existing.includes(img.src) && (img.naturalWidth > 400 || img.naturalHeight > 400)) {
                        return img.src;
                    }
                }
                return null;
            })''', list(existing_srcs))

            if found_src:
                new_img_src = found_src
                safe_log(f"    🎉 New generated look detected on canvas after {s}s!")
                break

        # Fallback if diff did not detect: strictly ONLY inspect images NOT in existing_srcs
        if not new_img_src:
            safe_log("    [!] Differential scan pending, checking latest new canvas tile...")
            new_img_src = page.evaluate('''((existing) => {
                const imgs = Array.from(document.querySelectorAll('img')).filter(i => (i.src || '').includes('/asb/'));
                const newImgs = imgs.filter(i => !existing.includes(i.src));
                if (newImgs.length > 0) {
                    return newImgs[newImgs.length - 1].src;
                }
                return null;
            })''', list(existing_srcs))

        # Step E: Extract image bytes via in-page authenticated fetch()
        if new_img_src:
            try:
                b64_res = page.evaluate('''async (url) => {
                    try {
                        const resp = await fetch(url);
                        if (resp.status !== 200) return { error: `HTTP ${resp.status}` };
                        const blob = await resp.blob();
                        const reader = new FileReader();
                        const dataUrl = await new Promise(resolve => {
                            reader.onloadend = () => resolve(reader.result);
                            reader.readAsDataURL(blob);
                        });
                        return { dataUrl: dataUrl, size: blob.size };
                    } catch(err) {
                        return { error: err.toString() };
                    }
                }''', new_img_src)

                if b64_res and b64_res.get("dataUrl"):
                    header, b64data = b64_res["dataUrl"].split(",", 1)
                    body = base64.b64decode(b64data)
                    filename = f"{format_key}_1.webp"
                    out_path = campaign_dir / filename
                    is_valid, reason = process_and_audit_image(body, format_key, out_path)
                    if is_valid:
                        safe_log(f"    ✅ [AUDIT PASSED] {filename} — {reason}")
                        saved_images.append({
                            "filename": filename,
                            "format": format_key,
                            "bytes": len(body),
                            "audit_status": "certified_pass"
                        })
                    else:
                        safe_log(f"    ❌ [AUDIT FAILED] {reason}")
                else:
                    safe_log(f"    ❌ [DOWNLOAD FAILED] in-page fetch: {b64_res.get('error') if b64_res else 'No data'}")
            except Exception as de:
                safe_log(f"    [!] Extraction error: {de}")
        else:
            safe_log(f"    ❌ Generation timed out for {format_label}.")

        anti_ban_sleep(min_sec=10, max_sec=20, reason="Format pacing")

    if ref_image and os.path.exists(ref_image):
        try:
            shutil.copy2(ref_image, str(campaign_dir / "source_flat_lay.jpg"))
        except Exception:
            pass

    brief_file = campaign_dir / "ugc_video_brief.json"
    with open(brief_file, "w", encoding="utf-8") as bf:
        json.dump(ugc_brief, bf, indent=2, ensure_ascii=False)
    safe_log(f"    🎬 Saved Omni Flash 10s UGC Video Brief: {brief_file.name}")

    if saved_images:
        campaign_info = {
            "campaign_slug": slug,
            "product_name": name,
            "category": category,
            "color": color,
            "is_outfit": is_outfit,
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "images": saved_images
        }
        with open(campaign_dir / "campaign_info.json", "w", encoding="utf-8") as f:
            json.dump(campaign_info, f, indent=2, ensure_ascii=False)

        meta["generation_status"] = "complete"
        meta["campaign_folder"] = slug
        meta["generated_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
        meta["generated_images"] = [img["filename"] for img in saved_images]

        if is_outfit:
            try:
                from outfit_warehouse import mark_outfit_generated
                mark_outfit_generated(name)
            except Exception:
                pass

        if product_dir and product_dir.exists():
            meta_target = product_dir / "metadata.json"
            try:
                with open(meta_target, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        if QUEUE_FILE.exists():
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    q_data = json.load(f)
                for item in q_data:
                    if item.get("product_name") == name or (product_dir and item.get("dir_name") == product_dir.name):
                        item["generation_status"] = "complete"
                        item["completed_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
                        item["campaign_folder"] = slug
                with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                    json.dump(q_data, f, indent=2, ensure_ascii=False)
            except Exception as qe:
                safe_log(f"    [!] Error updating queue_pending.json: {qe}")

        safe_log(f"🏆 CAMPAIGN COMPLETE: {len(saved_images)} certified lookbook ads saved for {name}!")
        return True
    else:
        safe_log(f"⚠️ Failed to generate certified images for {name}.")
        return False

def main():
    parser = argparse.ArgumentParser(description="OBSCURA Cloud Lookbook Generator")
    parser.add_argument("--count", type=int, default=5, help="Number of products to generate")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in 24/7 loop")
    parser.add_argument("--loop", action="store_true", help="Run continuously in 24/7 loop")
    parser.add_argument("--dry-run", action="store_true", help="Simulate queue discovery")
    args = parser.parse_args()

    is_loop = args.daemon or args.loop

    profile_dir = os.getenv("OBSCURA_CHROME_PROFILE", DEFAULT_PROFILE)
    safe_log(f"[*] Starting OBSCURA Cloud Generator | Mode: {'24/7 Daemon' if is_loop else 'Batch (count=' + str(args.count) + ')'}")
    safe_log(f"[*] Using Chrome Profile: {profile_dir} (Exists: {os.path.exists(profile_dir)})")

    while True:
        pending = find_pending_products(limit=args.count)
        safe_log(f"[*] Queue Scan: Found {len(pending)} pending product(s) in queue.")

        if not pending:
            if is_loop:
                safe_log("[*] Queue is clear. Sleeping 120s before next scan...")
                time.sleep(120)
                continue
            else:
                safe_log("Queue is clear. No generation required.")
                return

        with sync_playwright() as p:
            if os.path.exists(profile_dir):
                context = p.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    headless=False,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-blink-features=AutomationControlled"
                    ],
                    viewport={"width": 1920, "height": 1080}
                )
            else:
                # GHA fallback
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    sess = json.load(f)
                browser = p.chromium.launch(
                    headless=False,
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-blink-features=AutomationControlled"]
                )
                context = browser.new_context(storage_state=sess.get("storage_state"), viewport={"width": 1920, "height": 1080})

            page = context.pages[0] if context.pages else context.new_page()

            safe_log(f"[*] Navigating to Flow workspace: {PROJECT_URL}...")
            page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(6000)
            enter_flow_studio_if_needed(page, project_url=PROJECT_URL)

            completed = 0
            failed = 0

            for i, (pdir, meta) in enumerate(pending):
                pname = meta.get("product_name") or (pdir.name if pdir else "Drop")
                safe_log(f"\n[JOB {i+1}/{len(pending)}] Processing: {pname}")

                try:
                    success = generate_product_campaign(context, page, pdir, meta)
                    if success:
                        completed += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    safe_log(f"[ERROR] Campaign failure for {pname}: {e}")

                if i < len(pending) - 1:
                    anti_ban_sleep(min_sec=20, max_sec=40, reason="Inter-product cooldown")

            context.close()

        safe_log(f"\n========================================================")
        safe_log(f"🏁 BATCH FINISHED: {completed} Succeeded | {failed} Failed")
        safe_log(f"========================================================")

        if not is_loop:
            break
        safe_log("[*] Cooldown before next queue cycle (60s)...")
        time.sleep(60)

if __name__ == "__main__":
    main()
