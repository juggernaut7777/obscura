#!/usr/bin/env python3
"""
cloud_generator_gha.py - OBSCURA Autonomous Cloud Lookbook Generator for GitHub Actions (16 GB RAM)
================================================================================================
Fully autonomous generation engine running on GitHub Actions Ubuntu cloud runners:
  1. Multi-Category Prompt Library (Tops, Bottoms, Shoes, Bags, Accessories)
  2. Dual-Platform Formatting via Pillow: True 9:16 Vertical (TikTok/Reels) & 1:1 Square (IG Posts)
  3. Queue Discovery: Reads lightweight queue_pending.json or MANUAL_CURATION directory
  4. Omni Flash 10s UGC Video Brief Synthesis (ugc_video_brief.json)
  5. Human-like anti-ban pacing & randomized jitter delays
  6. Automatic Curation State & Queue Status Synchronization
"""

import os
import sys
import time
import json
import glob
import re
import io
import random
import argparse
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
CURATION_DIR = BASE_DIR / "MANUAL_CURATION"
OUTPUT_DIR = BASE_DIR / "OUTPUT_READY_FOR_SALE"
SESSION_FILE = BASE_DIR / "sessions" / "session_google_account.json"
QUEUE_FILE = BASE_DIR / "queue_pending.json"
PROJECT_URL = os.getenv("GFLOW_PROJECT_URL", "https://flow.google.com/project/4dc53153-d3a1-4c37-aebc-2908e97516e5")

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

def enter_flow_studio_if_needed(page, project_url=None):
    """If on /about or landing page, click 'Create with Google Flow' or 'Sign in' and enter studio."""
    safe_log(f"    [Studio Gate] Checking page: URL={page.url} | Title={page.title()}")

    # Check if on /about landing page or outside studio
    if "/about" in page.url or "flow.google.com" not in page.url or "/project/" not in page.url:
        btn_clicked = page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('a, button, [role="button"]'));
            const createBtn = btns.find(b => (b.textContent || '').includes('Create with Google Flow'));
            if (createBtn) {
                createBtn.click();
                return 'Create with Google Flow';
            }
            const signinBtn = btns.find(b => (b.textContent || '').trim() === 'Sign in');
            if (signinBtn) {
                signinBtn.click();
                return 'Sign in';
            }
            return null;
        }''')

        if btn_clicked:
            safe_log(f"    [Studio Gate] Clicked '{btn_clicked}', waiting for navigation...")
            page.wait_for_timeout(10000)
            safe_log(f"    [Studio Gate] URL after click: {page.url} | Title={page.title()}")

        # If redirected to Google accounts page (Single Sign-On account chooser)
        if "accounts.google.com" in page.url:
            safe_log("    [Studio Gate] Google Accounts SSO / Chooser detected...")
            try:
                page.screenshot(path=str(OUTPUT_DIR / f"debug_google_sso_{int(time.time())}.png"))
                sso_dump = page.evaluate('''() => {
                    const els = Array.from(document.querySelectorAll('li, div[role="link"], button, a')).map(e => ({
                        tag: e.tagName,
                        role: e.getAttribute('role'),
                        text: (e.textContent || '').trim().slice(0, 60)
                    })).filter(x => x.text.length > 0).slice(0, 20);
                    return els;
                }''')
                safe_log(f"    [SSO Chooser DOM] Elements: {sso_dump}")

                clicked_acc = page.evaluate('''() => {
                    const candidates = Array.from(document.querySelectorAll('li, div[role="link"], div[jsname], div[data-profileidentifier]'));
                    for (const c of candidates) {
                        const t = (c.textContent || '').trim();
                        if (t.includes('@') || t.includes('Signed in') || t.includes('Flow User')) {
                            c.click();
                            return t;
                        }
                    }
                    const first = document.querySelector('ul > li, div[role="list"] > div, div[role="link"]');
                    if (first) {
                        first.click();
                        return 'first_list_item';
                    }
                    return null;
                }''')
                safe_log(f"    [SSO Chooser Clicked] -> {clicked_acc}")
                page.wait_for_timeout(10000)
                safe_log(f"    [SSO Chooser Result] URL={page.url} | Title={page.title()}")
            except Exception as sso_err:
                safe_log(f"    [SSO Error] {sso_err}")

        # If we are now inside flow but not yet on project URL, navigate
        if project_url and ("/about" in page.url or "flow.google.com" in page.url):
            safe_log(f"    [Studio Gate] Navigating to target project workspace: {project_url}...")
            try:
                page.goto(project_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(8000)
                safe_log(f"    [Studio Gate] Project page URL: {page.url} | Title={page.title()}")
            except Exception as pe:
                safe_log(f"    [Studio Gate] Project navigation note: {pe}")

def find_and_focus_editor(page, project_url=None):
    """Find ProseMirror prompt editor and focus it cleanly, dismissing overlays."""
    safe_log(f"    [Editor] Current page URL: {page.url} | Title: {page.title()}")

    # Ensure studio is entered
    enter_flow_studio_if_needed(page, project_url=project_url)

    # 1. Dismiss Google cookie banner, intro modals, tour dialogs
    try:
        page.evaluate('''() => {
            const b = document.getElementById("glue-cookie-notification-bar-1");
            if (b) b.remove();
            const btns = Array.from(document.querySelectorAll('button, a'));
            for (const btn of btns) {
                const txt = (btn.textContent || '').trim();
                const aria = btn.getAttribute('aria-label') || '';
                if (txt.includes('OK, got it') || txt.includes('Accept all') || txt.includes('Close') || aria === 'Close') {
                    btn.click();
                }
            }
            // Dismiss cdk-overlay-backdrop if present
            const bd = document.querySelector('.cdk-overlay-backdrop');
            if (bd) bd.click();
        }''')
    except Exception as ce:
        safe_log(f"    [Editor] Banner clear note: {ce}")

    # 2. Check direct selectors with short timeout
    for sel in ["div.ProseMirror", "[contenteditable='true']", "div[contenteditable]"]:
        loc = page.locator(sel).first
        try:
            if loc.is_visible():
                loc.click(timeout=3000, force=True)
                safe_log(f"    [Editor] Focused via selector: {sel}")
                return loc
        except Exception:
            continue

    # 3. If not found, log DOM info & take debug screenshot
    debug_shot = OUTPUT_DIR / f"debug_flow_page_{int(time.time())}.png"
    try:
        page.screenshot(path=str(debug_shot))
        safe_log(f"    [Editor] Debug screenshot saved to {debug_shot}")
        dom_dump = page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button, a, [role="button"]')).map(el => (el.textContent || el.getAttribute('aria-label') || '').trim()).filter(Boolean).slice(0, 25);
            return { url: window.location.href, title: document.title, buttons: btns };
        }''')
        safe_log(f"    [Editor DOM Dump] URL: {dom_dump['url']} | Buttons: {dom_dump['buttons']}")
    except Exception:
        pass

    # 4. Final attempt with wait_for
    loc = page.locator("div.ProseMirror, [contenteditable='true']").first
    loc.wait_for(state="visible", timeout=20000)
    loc.click(force=True)
    return loc

# ==========================================
# CATEGORY DETECTION & PROMPT EXPANSION
# ==========================================
def detect_category(product_name: str, meta: dict) -> str:
    name = (product_name or "").lower()
    cat = (meta.get("product_category") or "").lower()
    desc = (meta.get("description") or "").lower()
    text = f"{name} {cat} {desc}"

    if any(w in text for w in ("shoe", "sneaker", "boot", "loafer", "dunk", "jordan", "runner", "slide", "vomero")):
        return "shoes"
    if any(w in text for w in ("pant", "cargo", "jean", "denim", "trouser", "sweatpant", "shorts", "bottom")):
        return "bottoms"
    if any(w in text for w in ("bag", "backpack", "tote", "crossbody", "duffle", "wallet", "pouch", "purse")):
        return "bags"
    if any(w in text for w in ("watch", "sunglass", "glasses", "necklace", "chain", "ring", "bracelet", "belt", "hat", "cap", "beanie")):
        return "accessories"
    return "tops"

def build_category_prompts(category: str, name: str, color: str) -> dict:
    c = color.strip() if color else "luxury"
    prompts = {}

    if category == "tops":
        prompts["tiktok_9_16"] = (
            f"Full-length vertical 9:16 high-fashion editorial lookbook photo of a model wearing an OBSCURA {c} top garment, "
            f"standing with natural runway posture in an industrial brutalist concrete studio. Paired with relaxed tailored black trousers "
            f"and luxury chunky sneakers. Soft sculptural studio rim lighting, authentic heavy cotton fabric drape, deep seam contrast, "
            f"vertical 9:16 framing, RAW photograph, 8k Vogue runway standard, ultra-sharp textile details."
        )
        prompts["ig_feed_post"] = (
            f"Waist-up medium portrait editorial photo of a high-fashion model wearing this OBSCURA {c} top garment. "
            f"Minimalist off-white studio cyclorama backdrop. Shot on 85mm prime lens with crisp key strobe lighting, "
            f"highlighting structural collar construction, drop-shoulder tailoring, and visible fabric grain. "
            f"Square 1:1 centered composition, Vogue Hommes standard, 8k resolution, RAW photo."
        )
    elif category == "bottoms":
        prompts["tiktok_9_16"] = (
            f"Full-body vertical 9:16 editorial streetwear photo of a model wearing these exact OBSCURA {c} trousers. "
            f"Walking through a modern minimalist brutalist courtyard, showing how the pants stack effortlessly over luxury high-top sneakers. "
            f"Focus on deep utility cargo pockets, relaxed straight-leg silhouette, and durable twill grain. "
            f"Vertical 9:16 composition, RAW photograph, SSENSE editorial lookbook quality."
        )
        prompts["ig_feed_post"] = (
            f"Luxury architectural flat lay photo of these exact OBSCURA {c} trousers arranged with intentional organic folds "
            f"on a massive slab of raw textured dark slate rock. Dramatic 45-degree directional studio strobe casting sculpted micro-shadows "
            f"along the seams, pocket edges, and hardware toggles. Centered square 1:1 format, ultra-crisp detail, RAW photograph."
        )
    elif category == "shoes":
        prompts["tiktok_9_16"] = (
            f"Low-angle vertical 9:16 street-level editorial shot of a model wearing these exact OBSCURA {c} luxury sneakers on-foot. "
            f"Stepping down onto a clean textured concrete sidewalk during golden hour, tailored dark trousers breaking perfectly over the collar. "
            f"Dynamic candid walking motion, sharp focus on sneaker paneling and premium leather grain, vertical 9:16 orientation, RAW photo."
        )
        prompts["ig_feed_post"] = (
            f"High-end luxury commercial product photograph of these exact OBSCURA {c} sneakers displayed on an elevated matte black "
            f"monolithic pedestal. Overhead softbox lighting with subtle silver fill, accentuating pristine stitch lines and sole architecture. "
            f"Square 1:1 centered crop, ultra-clean studio background, Hypebeast Footwear editorial standard, RAW photo."
        )
    elif category == "bags":
        prompts["tiktok_9_16"] = (
            f"Vertical 9:16 high-fashion editorial photo of a model in a minimalist charcoal coat, effortlessly carrying this "
            f"OBSCURA {c} luxury leather bag over their arm. Architectural museum gallery setting with ambient soft daylight. "
            f"Tactile focus on pebbled leather grain, edge paint, and brushed metal hardware. Vertical 9:16 framing, Vogue editorial, RAW photo."
        )
        prompts["ig_feed_post"] = (
            f"Luxury editorial still life photo of this exact OBSCURA {c} bag positioned on an Italian travertine marble block. "
            f"Clean diffused morning side-light highlighting the supple leather drape and luxury hardware. Square 1:1 format, RAW photo."
        )
    else:  # accessories
        prompts["tiktok_9_16"] = (
            f"Vertical 9:16 high-fashion close-range editorial portrait of a model wearing this OBSCURA {c} accessory. "
            f"Dramatic cinematic side-lighting with soft shadows. Ultra-sharp focus on the accessory detailing, metallic luster, "
            f"and luxury finishing. Vertical 9:16 composition, Vogue editorial standard, RAW photo."
        )
        prompts["ig_feed_post"] = (
            f"Macro editorial commercial product photo of this OBSCURA {c} luxury accessory displayed on a minimalist textured "
            f"volcanic stone plinth. Crisp overhead directional strobe emphasizing micro-engravings, brushed metal bevels, and craftsmanship. "
            f"Square 1:1 centered composition, SSENSE campaign quality, 8k resolution, RAW photo."
        )

    return prompts

def build_ugc_video_brief(category, name, color):
    c = color.strip() if color else "luxury"
    scripts = {
        "tops": (
            f"Stop buying overpriced blanks. OBSCURA just dropped this {c} heavyweight top and the drape is unreal. "
            f"500GSM french terry, raw dropped shoulders, perfectly tailored collar. Link in bio to cop."
        ),
        "bottoms": (
            f"Finding pants that stack cleanly on footwear without bunching is nearly impossible. "
            f"OBSCURA engineered these {c} trousers with structured utility lines and custom heavyweight twill. Link in bio."
        ),
        "shoes": (
            f"On-foot check: the new OBSCURA {c} luxury silhouette. Italian calfskin paneling, custom sculpted sole, "
            f"and unmatched all-day comfort. Limited release, link in bio."
        ),
        "bags": (
            f"The everyday luxury piece you've been looking for. OBSCURA {c} architectural bag in full-grain textured leather. "
            f"Heavy brushed hardware, structured silhouette. Link in bio."
        ),
        "accessories": (
            f"Details make or break an outfit. This OBSCURA {c} custom piece brings instant subtle luxury. "
            f"Engineered micro-finish, weighted feel. Available now in bio."
        )
    }
    script = scripts.get(category, scripts["tops"])
    video_prompt = (
        f"Authentic front-camera 9:16 smartphone fit-check video of a fashion influencer showing off an OBSCURA {c} {category} piece. "
        f"Influencer speaks naturally to camera, turns 360 degrees to demonstrate fabric drape and tailored fit. "
        f"Natural daylight, handheld subtle movement, genuine social media UGC aesthetic, 10s video length with synchronized native speech."
    )
    return {
        "duration_seconds": 10,
        "format": "9:16 vertical",
        "model_engine": "Omni Flash (veo_3_1_i2v_lite)",
        "script": script,
        "video_prompt": video_prompt
    }

# ==========================================
# IMAGE AUDIT & PILLOW ASPECT RATIO PROCESSOR
# ==========================================
def process_and_audit_image(data: bytes, format_key: str, out_path: Path) -> tuple[bool, str]:
    """
    Validates image binary with PIL, guarantees file integrity,
    and applies smart aspect ratio formatting:
      - 'tiktok_9_16': true 9:16 vertical aspect ratio
      - 'ig_feed_post': true 1:1 square aspect ratio
    Saves as optimized high-quality WebP.
    """
    if len(data) < 20000:
        return False, f"File size too small ({len(data)} bytes) - likely blank or error"
    if b"<html" in data[:100].lower() or b"<!doctype" in data[:100].lower():
        return False, "Received HTML error page instead of binary image"

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        w, h = img.size
        if w < 200 or h < 200:
            return False, f"Image dimensions too small ({w}x{h})"

        # Convert palette or RGBA to RGB cleanly
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
        target_ratio = (9.0 / 16.0) if "tiktok" in format_key else 1.0
        current_ratio = w / h

        # Smart center-crop if ratio deviates
        if abs(current_ratio - target_ratio) > 0.02:
            if current_ratio > target_ratio:
                # Too wide: crop horizontal edges
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                img = img.crop((left, 0, left + new_w, h))
            else:
                # Too tall: crop vertical top/bottom (preserve 35% top headroom)
                new_h = int(w / target_ratio)
                top = int((h - new_h) * 0.35)
                img = img.crop((0, top, w, top + new_h))

        # Save to destination as high-quality WebP
        img.save(out_path, format="WEBP", quality=95, method=6)
        final_w, final_h = img.size
        ratio_str = "9:16 vertical" if "tiktok" in format_key else "1:1 square"
        return True, f"Saved {final_w}x{final_h} ({ratio_str})"
    except Exception as e:
        return False, f"Pillow processing failed: {e}"

def anti_ban_sleep(min_sec=20, max_sec=40, reason="Anti-ban jitter"):
    delay = random.uniform(min_sec, max_sec)
    safe_log(f"🛡️  {reason}: Pausing for {delay:.1f}s to maintain human-like pacing...")
    time.sleep(delay)

# ==========================================
# QUEUE DISCOVERY
# ==========================================
def find_pending_products(limit=5):
    pending = []

    # 1. Check queue_pending.json first (cloud queue)
    if QUEUE_FILE.exists():
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
            for item in queue:
                if item.get("generation_status") != "complete":
                    pdir = BASE_DIR / "OUTPUT_READY_FOR_SALE" / sanitize_slug(item.get("product_name", "product"))
                    pending.append((pdir, item))
                    if len(pending) >= limit:
                        return pending
        except Exception as e:
            safe_log(f"[!] Error reading queue_pending.json: {e}")

    # 2. Fallback to MANUAL_CURATION directory if present
    dirs = glob.glob(str(CURATION_DIR / "*"))
    for d in sorted(dirs):
        meta_file = Path(d) / "metadata.json"
        if not meta_file.exists():
            continue
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("generation_status") != "complete":
                pending.append((Path(d), meta))
                if len(pending) >= limit:
                    break
        except Exception:
            continue

    return pending

# ==========================================
# GENERATION DISPATCH
# ==========================================
def generate_product_campaign(context, page, product_dir, meta):
    name = meta.get("product_name") or product_dir.name
    color = meta.get("classified_summary", {}).get("primary_color") or meta.get("color") or ""
    category = detect_category(name, meta)

    slug = f"{int(time.time())}_{sanitize_slug(name)}"
    campaign_dir = OUTPUT_DIR / slug
    campaign_dir.mkdir(parents=True, exist_ok=True)

    safe_log(f"\n========================================================")
    safe_log(f"🎯 STARTING CAMPAIGN: {name}")
    safe_log(f"   Category: {category} | Color: {color} | Slug: {slug}")
    safe_log(f"========================================================")

    prompts_by_format = build_category_prompts(category, name, color)
    ugc_brief = build_ugc_video_brief(category, name, color)
    saved_images = []

    for format_key, prompt in prompts_by_format.items():
        format_label = "TikTok/Reels (9:16)" if "tiktok" in format_key else "Instagram Feed Post (1:1)"
        safe_log(f"\n[*] Generating format: {format_label}...")
        safe_log(f"    Prompt: {prompt[:90]}...")

        # Measure pre-existing images
        pre_images = page.evaluate('() => Array.from(document.querySelectorAll("img.image")).map(i => i.src)')

        # Focus ProseMirror editor with overlay dismissal
        editor = find_and_focus_editor(page, project_url=PROJECT_URL)
        page.wait_for_timeout(random.randint(300, 500))
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        
        # Human-like typing
        page.keyboard.type(prompt, delay=random.randint(10, 18))
        page.wait_for_timeout(random.randint(400, 700))

        # Submit generation via Enter + Click
        safe_log("    Submitting generation request...")
        try:
            page.keyboard.press("Enter")
            page.wait_for_timeout(300)
            gen_btn = page.locator("button[aria-label='Start generation']").first
            if gen_btn.is_visible():
                gen_btn.click(force=True, no_wait_after=True, timeout=3000)
        except Exception:
            pass

        # Poll for new images with safety timeout
        new_urls = []
        for sec in range(1, 45):
            time.sleep(1.0)
            current = page.evaluate('() => Array.from(document.querySelectorAll("img.image")).map(i => i.src)')
            diff = [u for u in current if u not in pre_images and "flow.google.com/asb/" in u]
            if diff:
                new_urls = diff
                safe_log(f"    🎉 Received {len(diff)} generated image(s) after {sec}s!")
                break
            if sec % 10 == 0:
                safe_log(f"    ... generating ({sec}s) | DOM count: {len(current)}")

        if not new_urls:
            # Fallback: grab latest images from DOM
            current = page.evaluate('() => Array.from(document.querySelectorAll("img.image")).map(i => i.src)')
            new_urls = [u for u in current if "flow.google.com/asb/" in u][-2:]

        # Download, format aspect ratio with Pillow, and audit each image
        for i, url in enumerate(new_urls[:2]):
            try:
                resp = context.request.get(url, timeout=30000)
                if resp.status == 200:
                    body = resp.body()
                    filename = f"{format_key}_{i+1}.webp"
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
            except Exception as e:
                safe_log(f"    [!] Download/Audit error: {e}")

        # Anti-ban sleep between format generations
        anti_ban_sleep(min_sec=15, max_sec=30, reason="Format pacing")

    # Save Omni Flash UGC video brief
    brief_file = campaign_dir / "ugc_video_brief.json"
    with open(brief_file, "w", encoding="utf-8") as bf:
        json.dump(ugc_brief, bf, indent=2, ensure_ascii=False)
    safe_log(f"    🎬 Saved Omni Flash 10s UGC Video Brief: {brief_file.name}")

    if saved_images:
        # Write campaign metadata
        campaign_info = {
            "campaign_slug": slug,
            "product_name": name,
            "category": category,
            "color": color,
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "images": saved_images
        }
        with open(campaign_dir / "campaign_info.json", "w", encoding="utf-8") as f:
            json.dump(campaign_info, f, indent=2, ensure_ascii=False)

        # Update metadata.json if product_dir exists
        meta["generation_status"] = "complete"
        meta["campaign_folder"] = slug
        meta["generated_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
        meta["generated_images"] = [img["filename"] for img in saved_images]
        if product_dir.exists():
            meta_target = product_dir / "metadata.json"
            try:
                with open(meta_target, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        # Update queue_pending.json
        if QUEUE_FILE.exists():
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    q_data = json.load(f)
                for item in q_data:
                    if item.get("product_name") == name or item.get("dir_name") == product_dir.name:
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

# ==========================================
# MAIN RUNNER
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="OBSCURA Cloud Lookbook Generator")
    parser.add_argument("--count", type=int, default=5, help="Number of products to generate")
    parser.add_argument("--dry-run", action="store_true", help="Simulate queue discovery and prompt synthesis")
    args = parser.parse_args()

    pending = find_pending_products(limit=args.count)
    safe_log(f"[*] Queue Scan: Found {len(pending)} pending product(s) in queue.")

    if not pending:
        safe_log("Queue is clear. No generation required.")
        return

    if args.dry_run:
        safe_log("=== DRY RUN MODE: Testing Prompt Synthesis & Category Mapping ===")
        for pdir, meta in pending:
            pname = meta.get("product_name") or pdir.name
            pcolor = meta.get("classified_summary", {}).get("primary_color") or meta.get("color") or ""
            pcat = detect_category(pname, meta)
            prompts = build_category_prompts(pcat, pname, pcolor)
            brief = build_ugc_video_brief(pcat, pname, pcolor)
            safe_log(f"Product: {pname} | Cat: {pcat} | Color: {pcolor}")
            safe_log(f"  TikTok: {prompts['tiktok_9_16'][:60]}...")
            safe_log(f"  IG: {prompts['ig_feed_post'][:60]}...")
            safe_log(f"  UGC Script: {brief['script'][:60]}...")
        return

    if not SESSION_FILE.exists():
        safe_log(f"❌ FATAL: Session file not found at {SESSION_FILE}")
        sys.exit(1)

    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        sess = json.load(f)
    storage_state = sess.get("storage_state")

    global PROJECT_URL
    if not os.getenv("GFLOW_PROJECT_URL") and sess.get("project_id"):
        PROJECT_URL = f"https://flow.google.com/project/{sess['project_id']}"
    safe_log(f"[*] Target Flow Project URL: {PROJECT_URL}")

    completed = 0
    failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = browser.new_context(
            storage_state=storage_state,
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        safe_log(f"Loading Flow project: {PROJECT_URL}...")
        page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)
        safe_log(f"[*] Initial load URL: {page.url} | Title: {page.title()}")

        enter_flow_studio_if_needed(page, project_url=PROJECT_URL)

        for i, (pdir, meta) in enumerate(pending):
            pname = meta.get("product_name") or pdir.name
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
                anti_ban_sleep(min_sec=30, max_sec=60, reason="Inter-product cooldown")

        browser.close()

    safe_log(f"\n========================================================")
    safe_log(f"🏁 RUN COMPLETE: {completed} Succeeded | {failed} Failed")
    safe_log(f"========================================================")

if __name__ == "__main__":
    main()
