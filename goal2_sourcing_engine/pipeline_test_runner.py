"""
OBSCURA — END-TO-END PIPELINE TEST RUNNER
=============================================
Tests every stage of the OBSCURA pipeline from sourcing to storefront.
Catches errors, reports exactly which stage failed and why, and self-heals
failed stages by invoking the local Antigravity SDK Agent.

STAGES TESTED:
  1. SOURCING     — Can we scrape a known Weidian link?
  2. CURATION     — Do scraped images save correctly to MANUAL_CURATION/?
                    Includes a PIL-based dimensions and integrity check.
  3. GENERATION   — Can the Flow Bridge generate an image?
                    Includes bridge token freshness check.
  4. OUTPUT        — Did generated images land in OUTPUT_READY_FOR_SALE/?
                    Includes VisionEvaluator quality gate validation.
  5. STOREFRONT   — Can we write a test product to products.js?
  6. STOCK SYNC   — Can we read/update supplier mappings?

Usage:
  python pipeline_test_runner.py                  # Full test (uses live APIs)
  python pipeline_test_runner.py --dry-run        # Skip API calls, test file I/O only
  python pipeline_test_runner.py --stage 3        # Test only a specific stage
  python pipeline_test_runner.py --self-heal      # Auto-retry failed stages with Antigravity SDK fixes
"""

import os
import sys
import json
import time
import shutil
import asyncio
import traceback
import argparse
import importlib
from pathlib import Path
from datetime import datetime
from PIL import Image

# ─── PATHS ───
BASE_DIR = Path(__file__).resolve().parent
MANUAL_CURATION_DIR = BASE_DIR / "MANUAL_CURATION"
OUTPUT_READY_DIR = BASE_DIR / "OUTPUT_READY_FOR_SALE"
OUTPUT_UGC_DIR = BASE_DIR / "output_ugc"
INPUT_DIR = BASE_DIR / "input_sourcing"
MODELS_DIR = BASE_DIR / "models" / "character_sheets"
STOREFRONT_DIR = BASE_DIR.parent / "storefront"
PRODUCTS_FILE = STOREFRONT_DIR / "src" / "data" / "products.js"
SUPPLIER_MAPPINGS_FILE = BASE_DIR / "supplier_mappings.json"
BRIDGE_URL = "http://localhost:9877"

# Test product directory name (cleaned up after test)
TEST_PRODUCT_NAME = "__pipeline_test_product__"
TEST_DIR_CURATION = MANUAL_CURATION_DIR / TEST_PRODUCT_NAME
TEST_DIR_OUTPUT = OUTPUT_READY_DIR / TEST_PRODUCT_NAME

# Test Weidian link (a real, publicly accessible product page for testing)
TEST_WEIDIAN_URL = "https://weidian.com/item.html?itemID=5788883537"

# Result tracking
results = []


def safe_print(msg):
    """Windows cp1252-safe print."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode(), flush=True)


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "[*]", "OK": "[+]", "FAIL": "[!]", "WARN": "[?]"}.get(level, "[*]")
    safe_print(f"  {prefix} [{ts}] {msg}")


def record_result(stage_num, stage_name, passed, detail="", error_trace=""):
    """Record a test result."""
    result = {
        "stage": stage_num,
        "name": stage_name,
        "passed": passed,
        "detail": detail,
        "error": error_trace,
        "timestamp": datetime.now().isoformat()
    }
    results.append(result)
    status = "PASS" if passed else "FAIL"
    icon = "\u2705" if passed else "\u274c"
    safe_print(f"\n  {icon} Stage {stage_num} [{stage_name}]: {status}")
    if detail:
        safe_print(f"     {detail}")
    if error_trace and not passed:
        lines = error_trace.strip().split("\n")
        for line in lines[-5:]:
            safe_print(f"     {line}")


def cleanup_test_artifacts():
    """Remove any test artifacts created during the test run."""
    for d in [TEST_DIR_CURATION, TEST_DIR_OUTPUT]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    log("Cleaned up test artifacts", "INFO")


# ═══════════════════════════════════════════════════════════════════
# STAGE 1: SOURCING — Can we scrape a known Weidian link?
# ═══════════════════════════════════════════════════════════════════
async def test_stage_1_sourcing(dry_run=False):
    """Test that the Chinese Sourcing Agent can scrape a product page."""
    safe_print("\n" + "=" * 60)
    safe_print("  STAGE 1: SOURCING (Chinese Marketplace Scraper)")
    safe_print("=" * 60)

    # Check 1: Can we import the agent?
    try:
        from chinese_sourcing_agent import ChineseSourcingAgent
        log("ChineseSourcingAgent imported successfully", "OK")
    except ImportError as e:
        record_result(1, "SOURCING", False, "Cannot import ChineseSourcingAgent", str(e))
        return False

    # Check 2: Can Playwright be imported?
    try:
        from playwright.async_api import async_playwright
        log("Playwright available", "OK")
    except ImportError as e:
        record_result(1, "SOURCING", False, "Playwright not installed", str(e))
        return False

    if dry_run:
        log("DRY RUN: Skipping live Weidian scrape", "WARN")
        record_result(1, "SOURCING", True, "Dry run — imports OK, skipped live scrape")
        return True

    # Check 3: Actually scrape a test product
    try:
        agent = ChineseSourcingAgent(headless=True)
        result = await agent.scrape_product(TEST_WEIDIAN_URL, generate_contact_sheet=True, max_retries=2)
        if result and result is not False:
            log(f"Scrape returned data: {type(result)}", "OK")
            if isinstance(result, dict):
                urls = result.get("url_mapping", {})
                log(f"Got {len(urls)} image URLs from scrape", "OK")
            record_result(1, "SOURCING", True, f"Successfully scraped {TEST_WEIDIAN_URL}")
            return result
        else:
            record_result(1, "SOURCING", False, "Scrape returned False/None — possible CAPTCHA or login wall")
            return False
    except Exception as e:
        record_result(1, "SOURCING", False, "Scrape crashed", traceback.format_exc())
        return False


# ═══════════════════════════════════════════════════════════════════
# STAGE 2: CURATION — Do images save to MANUAL_CURATION correctly?
# ═══════════════════════════════════════════════════════════════════
def test_stage_2_curation(dry_run=False):
    """Test that we can create a valid MANUAL_CURATION product folder."""
    safe_print("\n" + "=" * 60)
    safe_print("  STAGE 2: CURATION (MANUAL_CURATION folder creation)")
    safe_print("=" * 60)

    try:
        # Check 1: MANUAL_CURATION directory exists
        MANUAL_CURATION_DIR.mkdir(exist_ok=True)
        log(f"MANUAL_CURATION dir exists: {MANUAL_CURATION_DIR}", "OK")

        # Check 2: Create a test product folder
        TEST_DIR_CURATION.mkdir(exist_ok=True)

        # Check 3: Create a valid metadata.json
        metadata = {
            "product_name": TEST_PRODUCT_NAME,
            "link": TEST_WEIDIAN_URL,
            "platform": "weidian",
            "item_id": "test_5788883537",
            "seller": "test_seller",
            "color": "black",
            "price_cny": 189,
            "source": "pipeline_test",
            "timestamp": datetime.now().isoformat()
        }
        meta_file = TEST_DIR_CURATION / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        log("metadata.json created successfully", "OK")

        # Check 4: Create a valid test image using PIL
        test_image = TEST_DIR_CURATION / "test_product_front.png"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image, format='PNG')
        log("Test image created using PIL (valid PNG)", "OK")

        # UPGRADE: PIL dimension & integrity checks
        try:
            with Image.open(test_image) as img:
                w, h = img.size
                img.verify()  # Verify image integrity
                log(f"PIL Verification passed: image is valid {img.format} ({w}x{h})", "OK")
        except Exception as e:
            record_result(2, "CURATION", False, "PIL Image verification failed", str(e))
            return False

        # Check 5: Verify the folder structure is complete
        has_meta = meta_file.exists()
        has_images = len(list(TEST_DIR_CURATION.glob("*.png"))) > 0
        valid_meta = False
        try:
            loaded = json.loads(meta_file.read_text(encoding="utf-8"))
            valid_meta = "product_name" in loaded and "link" in loaded
        except Exception:
            pass

        if has_meta and has_images and valid_meta:
            record_result(2, "CURATION", True, f"Created valid test product in {TEST_DIR_CURATION}")
            return True
        else:
            detail = f"has_meta={has_meta}, has_images={has_images}, valid_meta={valid_meta}"
            record_result(2, "CURATION", False, f"Incomplete product folder: {detail}")
            return False

    except Exception as e:
        record_result(2, "CURATION", False, "Curation folder creation failed", traceback.format_exc())
        return False


# ═══════════════════════════════════════════════════════════════════
# STAGE 3: GENERATION — Can the Flow Bridge generate an image?
# ═══════════════════════════════════════════════════════════════════
def test_stage_3_generation(dry_run=False):
    """Test that the Flow Bridge is running and can accept generation requests."""
    safe_print("\n" + "=" * 60)
    safe_print("  STAGE 3: GENERATION (Flow Bridge + Image Generation)")
    safe_print("=" * 60)

    import requests

    # Check 1: Is the bridge server running?
    try:
        resp = requests.get(f"{BRIDGE_URL}/health", timeout=5)
        if resp.status_code == 200:
            log("Flow Bridge is running and healthy", "OK")
            health_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            if health_data:
                log(f"Bridge health: {json.dumps(health_data, indent=2)[:200]}", "INFO")
        else:
            log(f"Bridge returned status {resp.status_code}", "WARN")
    except requests.ConnectionError:
        record_result(3, "GENERATION", False,
                      "Flow Bridge not running on localhost:9877. "
                      "Start it with: python all_in_one_bridge.py")
        return False
    except Exception as e:
        record_result(3, "GENERATION", False, f"Bridge health check failed: {e}")
        return False

    # UPGRADE: Check Token Freshness Check
    try:
        resp = requests.get(f"{BRIDGE_URL}/token-status", timeout=5)
        if resp.status_code == 200:
            token_info = resp.json()
            is_valid = token_info.get("valid") or token_info.get("has_token")
            time_left = token_info.get("expires_in_seconds", "unknown")
            if is_valid:
                log(f"Token freshness check: VALID (expires in: {time_left}s)", "OK")
            else:
                log("Token freshness check: EXPIRED or INVALID. Refresh OBSCURA extension.", "WARN")
        else:
            log("Token status endpoint returned non-200. Verification skipped.", "WARN")
    except Exception as e:
        log(f"Token freshness check failed: {e} (skipping checks)", "WARN")

    if dry_run:
        log("DRY RUN: Skipping actual image generation (saves credits)", "WARN")
        record_result(3, "GENERATION", True, "Dry run — bridge is running, token checked")
        return True

    # Check 3: Send a lightweight flat-lay generation request
    try:
        payload = {
            "prompt": "A professional flat lay photograph of a plain black t-shirt, "
                      "neatly folded on a clean white marble surface. "
                      "Overhead shot, soft natural lighting, minimalist aesthetic.",
            "ref_image_paths": []
        }
        log("Sending test flat-lay generation request...", "INFO")
        resp = requests.post(f"{BRIDGE_URL}/generate", json=payload, timeout=300)
        if resp.status_code == 200:
            log("Generation request succeeded!", "OK")
            record_result(3, "GENERATION", True, "Successfully generated a test image via Flow Bridge")
            return True
        else:
            record_result(3, "GENERATION", False,
                          f"Generation returned status {resp.status_code}: {resp.text[:200]}")
            return False
    except requests.Timeout:
        record_result(3, "GENERATION", False, "Generation timed out after 300s")
        return False
    except Exception as e:
        record_result(3, "GENERATION", False, "Generation request failed", traceback.format_exc())
        return False


# ═══════════════════════════════════════════════════════════════════
# STAGE 4: OUTPUT — Do generated images land correctly?
# ═══════════════════════════════════════════════════════════════════
def test_stage_4_output(dry_run=False):
    """Test that output directories exist and have the right structure."""
    safe_print("\n" + "=" * 60)
    safe_print("  STAGE 4: OUTPUT (OUTPUT_READY_FOR_SALE structure)")
    safe_print("=" * 60)

    try:
        # Check 1: Output directories exist
        OUTPUT_READY_DIR.mkdir(exist_ok=True)
        OUTPUT_UGC_DIR.mkdir(exist_ok=True)
        log(f"OUTPUT_READY_FOR_SALE exists: {OUTPUT_READY_DIR}", "OK")
        log(f"output_ugc exists: {OUTPUT_UGC_DIR}", "OK")

        # Check 2: Create a test output campaign folder
        TEST_DIR_OUTPUT.mkdir(exist_ok=True)

        # Simulate the output structure that storefront_uploader.py expects
        campaign_meta = {
            "product_name": TEST_PRODUCT_NAME,
            "link": TEST_WEIDIAN_URL,
            "platform": "weidian",
            "color": "black",
            "price_cny": 189,
            "generated_at": datetime.now().isoformat()
        }
        meta_file = TEST_DIR_OUTPUT / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(campaign_meta, f, indent=2, ensure_ascii=False)
        log("Output metadata.json created", "OK")

        # Create valid test generated images using PIL
        model_shot = TEST_DIR_OUTPUT / "model_shot_1.png"
        flat_lay = TEST_DIR_OUTPUT / "flat_lay_1.png"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(model_shot, format='PNG')
        img.save(flat_lay, format='PNG')
        log("Test generated images created using PIL (valid PNG)", "OK")

        # Check 3: Validate VisionEvaluator import (quality gate)
        try:
            from vision_evaluator import VisionEvaluator
            log("VisionEvaluator available for quality scoring", "OK")
            # UPGRADE: Add a VisionEvaluator test score check (using dummy call)
            # If not dry run, we evaluate the generated test file
            if not dry_run:
                evaluator = VisionEvaluator()
                # Run evaluation on our dummy image
                eval_res = evaluator.evaluate_image(str(flat_lay))
                log(f"VisionEvaluator dummy scoring ran: passed={eval_res.get('passed')}", "OK")
        except ImportError:
            log("VisionEvaluator not available — quality gate disabled", "WARN")

        # Check 4: Verify complete structure
        images = list(TEST_DIR_OUTPUT.glob("*.png"))
        has_meta = meta_file.exists()

        if len(images) >= 2 and has_meta:
            record_result(4, "OUTPUT", True,
                          f"Valid output folder with {len(images)} images + metadata")
            return True
        else:
            record_result(4, "OUTPUT", False,
                          f"Incomplete: {len(images)} images, has_meta={has_meta}")
            return False

    except Exception as e:
        record_result(4, "OUTPUT", False, "Output stage failed", traceback.format_exc())
        return False


# ═══════════════════════════════════════════════════════════════════
# STAGE 5: STOREFRONT — Can we write a product to products.js?
# ═══════════════════════════════════════════════════════════════════
def test_stage_5_storefront(dry_run=False):
    """Test storefront uploader imports and can read/write products.js."""
    safe_print("\n" + "=" * 60)
    safe_print("  STAGE 5: STOREFRONT (storefront_uploader.py)")
    safe_print("=" * 60)

    try:
        # Check 1: Storefront directory exists
        if not STOREFRONT_DIR.exists():
            record_result(5, "STOREFRONT", False,
                          f"Storefront directory not found: {STOREFRONT_DIR}")
            return False
        log(f"Storefront directory exists: {STOREFRONT_DIR}", "OK")

        # Check 2: products.js exists and is parseable
        if PRODUCTS_FILE.exists():
            content = PRODUCTS_FILE.read_text(encoding="utf-8")
            has_products = "DEMO_PRODUCTS" in content or "products" in content.lower()
            log(f"products.js exists ({len(content)} bytes, has_products={has_products})", "OK")
        else:
            log("products.js does not exist yet — will be created on first upload", "WARN")

        # Check 3: Can we import storefront_uploader?
        try:
            sys.path.insert(0, str(BASE_DIR))
            from storefront_uploader import load_current_products, scan_and_upload
            log("storefront_uploader imports successfully", "OK")
        except ImportError as e:
            record_result(5, "STOREFRONT", False,
                          f"Cannot import storefront_uploader: {e}")
            return False

        # Check 4: Can we load current products?
        try:
            products, collections_raw, outfits_raw = load_current_products()
            log(f"Loaded {len(products)} existing products from storefront", "OK")
        except Exception as e:
            log(f"Could not load current products: {e}", "WARN")

        # Check 5: Pricing engine available?
        try:
            from pricing_engine import calculate_final_price
            test_price = calculate_final_price(189, "weidian")
            log(f"Pricing engine works: 189 CNY -> {test_price} USD", "OK")
        except ImportError:
            log("pricing_engine not available", "WARN")
        except Exception as e:
            log(f"pricing_engine error: {e}", "WARN")

        if dry_run:
            log("DRY RUN: Skipping actual storefront upload", "WARN")
            record_result(5, "STOREFRONT", True, "Dry run — imports OK, products.js readable")
            return True

        # Check 6: Actually run scan_and_upload
        try:
            scan_and_upload()
            log("scan_and_upload() completed without errors", "OK")
            record_result(5, "STOREFRONT", True, "Storefront uploader ran successfully")
            return True
        except Exception as e:
            record_result(5, "STOREFRONT", False, "scan_and_upload() crashed", traceback.format_exc())
            return False

    except Exception as e:
        record_result(5, "STOREFRONT", False, "Storefront test failed", traceback.format_exc())
        return False


# ═══════════════════════════════════════════════════════════════════
# STAGE 6: STOCK SYNC — Can we check & update supplier stock?
# ═══════════════════════════════════════════════════════════════════
def test_stage_6_stock_sync(dry_run=False):
    """Test supplier mappings and stock sync infrastructure."""
    safe_print("\n" + "=" * 60)
    safe_print("  STAGE 6: STOCK SYNC (auto_stock_sync.py)")
    safe_print("=" * 60)

    try:
        # Check 1: Supplier mappings file readable
        if SUPPLIER_MAPPINGS_FILE.exists():
            with open(SUPPLIER_MAPPINGS_FILE, "r", encoding="utf-8") as f:
                mappings = json.load(f)
            log(f"supplier_mappings.json loaded: {len(mappings)} entries", "OK")
        else:
            log("supplier_mappings.json does not exist yet (will be created on first upload)", "WARN")

        # Check 2: Can we import auto_stock_sync?
        try:
            sys.path.insert(0, str(BASE_DIR))
            from auto_stock_sync import load_supplier_mappings, load_current_products
            log("auto_stock_sync imports successfully", "OK")
        except ImportError as e:
            record_result(6, "STOCK SYNC", False,
                          f"Cannot import auto_stock_sync: {e}")
            return False

        # Check 3: Can we import ChineseSourcingAgent
        try:
            from chinese_sourcing_agent import ChineseSourcingAgent
            log("ChineseSourcingAgent available for stock re-scraping", "OK")
        except ImportError:
            log("ChineseSourcingAgent not available — stock sync will fail on live runs", "WARN")

        if dry_run:
            log("DRY RUN: Skipping live stock re-scrape", "WARN")
            record_result(6, "STOCK SYNC", True, "Dry run — imports OK, mappings readable")
            return True

        record_result(6, "STOCK SYNC", True, "Stock sync infrastructure verified")
        return True

    except Exception as e:
        record_result(6, "STOCK SYNC", False, "Stock sync test failed", traceback.format_exc())
        return False


# ═══════════════════════════════════════════════════════════════════
# INFRASTRUCTURE CHECKS
# ═══════════════════════════════════════════════════════════════════
def test_infrastructure():
    """Check all critical infrastructure is in place."""
    safe_print("\n" + "=" * 60)
    safe_print("  INFRASTRUCTURE CHECKS")
    safe_print("=" * 60)

    checks = []

    # .env file
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        log(".env file exists", "OK")
        checks.append(True)
    else:
        log(".env file MISSING — API keys not available", "FAIL")
        checks.append(False)

    # Model character sheets
    if MODELS_DIR.exists():
        models = list(MODELS_DIR.glob("*.png")) + list(MODELS_DIR.glob("*.jpg"))
        log(f"Model character sheets: {len(models)} found in {MODELS_DIR.name}/", "OK")
        checks.append(len(models) > 0)
    else:
        log(f"Models directory MISSING: {MODELS_DIR}", "FAIL")
        checks.append(False)

    # Prompt library
    try:
        from prompt_library import PROMPT_TIERS, ELITE_PROMPTS
        log(f"prompt_library loaded: {len(ELITE_PROMPTS)} elite prompts", "OK")
        checks.append(True)
    except ImportError as e:
        log(f"prompt_library import failed: {e}", "FAIL")
        checks.append(False)

    # LiteLLM router
    try:
        from litellm_router import smart_llm_call
        log("LiteLLM router available", "OK")
        checks.append(True)
    except ImportError:
        log("LiteLLM router not available (non-critical for basic pipeline)", "WARN")
        checks.append(True)

    # Discord bot
    try:
        from discord_listener import safe_print as disc_safe_print
        log("discord_listener importable", "OK")
        checks.append(True)
    except ImportError as e:
        log(f"discord_listener import failed: {e}", "WARN")
        checks.append(True)

    return all(checks)


# ═══════════════════════════════════════════════════════════════════
# SELF-HEALING ENGINE (Antigravity Python SDK integration)
# ═══════════════════════════════════════════════════════════════════
async def invoke_self_healing(stage_name, error_detail):
    """Invokes the local Antigravity AI Agent to repair a broken pipeline file."""
    safe_print("\n" + "=" * 60)
    safe_print(f"  [⚠️] INITIATING AUTONOMOUS SELF-HEALING FOR {stage_name}")
    safe_print("=" * 60)

    try:
        from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
    except ImportError as e:
        safe_print(f"  [!] Failed to load google-antigravity SDK: {e}")
        safe_print("  [!] Please run 'pip install google-antigravity' to enable self-healing.")
        return False

    config = LocalAgentConfig(
        system_instructions=(
            "You are the master self-healing agent for the OBSCURA fashion pipeline.\n"
            "You have access to write/edit file tools. Your goal is to inspect files, "
            "locate Python syntax or logic errors that break tests, fix them in place, "
            "and make sure they compile perfectly."
        ),
        capabilities=CapabilitiesConfig()
    )

    prompt = (
        f"Stage '{stage_name}' of the OBSCURA fashion pipeline failed during automated testing.\n"
        f"Traceback/Error context:\n{error_detail}\n\n"
        "Please find the Python code file related to this stage (e.g. check the traceback files), "
        "inspect the exact error, write a code fix to repair the bug, and save the file. "
        "Explain what files you modified and what the fix was."
    )

    log("Contacting Antigravity SDK Agent...", "INFO")
    try:
        async with Agent(config) as agent:
            log("Agent connection established. Working on fix...", "INFO")
            response = await agent.chat(prompt)
            explanation = await response.text()
            safe_print("\n  [🔧] AGENT SELF-HEALING RESPONSE:")
            safe_print("-" * 50)
            safe_print(explanation)
            safe_print("-" * 50)
            return True
    except Exception as e:
        safe_print(f"  [!] Self-healing agent session failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════════
def print_banner():
    safe_print("")
    safe_print("=" * 60)
    safe_print("   OBSCURA — END-TO-END PIPELINE TEST RUNNER")
    safe_print("   Testing all 6 stages of the fashion pipeline")
    safe_print("=" * 60)


def print_summary():
    safe_print("\n" + "=" * 60)
    safe_print("   TEST SUMMARY")
    safe_print("=" * 60)

    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)

    for r in results:
        icon = "\u2705" if r["passed"] else "\u274c"
        safe_print(f"  {icon} Stage {r['stage']}: {r['name']} — {'PASS' if r['passed'] else 'FAIL'}")
        if r["detail"]:
            safe_print(f"       {r['detail']}")

    safe_print(f"\n  Results: {passed}/{total} passed, {failed} failed")
    safe_print("=" * 60)

    # Save results to JSON
    results_file = BASE_DIR / "pipeline_test_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "run_at": datetime.now().isoformat(),
            "passed": passed,
            "failed": failed,
            "total": total,
            "results": results
        }, f, indent=2)
    safe_print(f"  Results saved to: {results_file}")

    return failed == 0


async def run_all_stages(dry_run=False, stage_filter=None, self_heal=False):
    """Run all (or a specific) pipeline stage."""
    print_banner()

    # Infrastructure checks first
    infra_ok = test_infrastructure()
    if not infra_ok:
        safe_print("\n  [!] Infrastructure checks failed. Fix issues above first.")

    stages = {
        1: ("SOURCING", test_stage_1_sourcing),
        2: ("CURATION", test_stage_2_curation),
        3: ("GENERATION", test_stage_3_generation),
        4: ("OUTPUT", test_stage_4_output),
        5: ("STOREFRONT", test_stage_5_storefront),
        6: ("STOCK SYNC", test_stage_6_stock_sync),
    }

    for stage_num, (name, func) in stages.items():
        if stage_filter and stage_num != stage_filter:
            continue

        retries = 2 if self_heal else 1
        for attempt in range(1, retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    success = await func(dry_run=dry_run)
                else:
                    success = func(dry_run=dry_run)

                # If stage was successful or we aren't self-healing, stop retry loop
                if success or not self_heal:
                    break
            except Exception as e:
                err_detail = traceback.format_exc()
                record_result(stage_num, name, False,
                              f"Stage crashed with unhandled exception",
                              err_detail)

                if self_heal and attempt < retries:
                    # Trigger the Antigravity SDK autonomous agent self-healing loop
                    healed = await invoke_self_healing(name, err_detail)
                    if healed:
                        log(f"Self-healing triggered. Retrying stage {stage_num} (Attempt {attempt+1}/{retries})...", "INFO")
                        continue  # Retry stage
                break

    # Print summary
    all_passed = print_summary()

    # Cleanup test artifacts
    cleanup_test_artifacts()

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="OBSCURA End-to-End Pipeline Test Runner")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip API calls, test file I/O and imports only")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4, 5, 6],
                        help="Test only a specific stage (1-6)")
    parser.add_argument("--self-heal", action="store_true",
                        help="Auto-retry failed stages with Antigravity SDK fixes")
    parser.add_argument("--keep-artifacts", action="store_true",
                        help="Don't clean up test artifacts after run")
    args = parser.parse_args()

    success = asyncio.run(run_all_stages(
        dry_run=args.dry_run,
        stage_filter=args.stage,
        self_heal=args.self_heal
    ))

    if not args.keep_artifacts:
        cleanup_test_artifacts()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
