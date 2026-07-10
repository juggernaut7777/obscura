"""
Flow Bridge v5 — Shadow DOM Piercing + Pro Model
==================================================
Key changes:
1. Finds the prompt box by searching INSIDE shadow DOMs (no coordinates)
2. Switches model to Nano Banana 2 Pro
3. Uses asyncio.sleep everywhere (page-safe)
"""
import os
import asyncio
import random
from typing import List
from playwright.async_api import async_playwright

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
def safe_print(*args, **kwargs):
    msg = " ".join(str(arg) for arg in args)
    try:
        sys.stdout.write(msg + kwargs.get('end', '\n'))
        sys.stdout.flush()
    except UnicodeEncodeError:
        try:
            encoding = sys.stdout.encoding or 'utf-8'
            sys.stdout.write(msg.encode('utf-8', errors='replace').decode(encoding, errors='replace') + kwargs.get('end', '\n'))
            sys.stdout.flush()
        except Exception:
            sys.stdout.write("[Print Error] Unable to encode output print message.\n")
            sys.stdout.flush()

print = safe_print


# JavaScript that recursively searches all shadow DOMs for the prompt input
FIND_PROMPT_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 10) return null;
        
        // Check all elements in this root
        const all = root.querySelectorAll('*');
        for (const el of all) {
            // Check placeholder
            const ph = el.getAttribute('placeholder') || '';
            const ariaLabel = el.getAttribute('aria-label') || '';
            const role = el.getAttribute('role') || '';
            const ce = el.contentEditable;
            
            if (ph.toLowerCase().includes('create') || 
                ph.toLowerCase().includes('want') ||
                ariaLabel.toLowerCase().includes('prompt') ||
                ariaLabel.toLowerCase().includes('create')) {
                return el;
            }
            
            // Check contenteditable divs near bottom of page
            if (ce === 'true' || ce === 'plaintext-only') {
                const rect = el.getBoundingClientRect();
                if (rect.top > window.innerHeight * 0.7 && rect.width > 200) {
                    return el;
                }
            }
            
            // Check textareas and inputs near bottom
            if ((el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && el.type === 'text')) 
                && !el.closest('[role="search"]')) {
                const rect = el.getBoundingClientRect();
                if (rect.top > window.innerHeight * 0.5) {
                    return el;
                }
            }
            
            // Recurse into shadow roots
            if (el.shadowRoot) {
                const found = findInShadow(el.shadowRoot, depth + 1);
                if (found) return found;
            }
        }
        return null;
    }
    
    const el = findInShadow(document, 0);
    if (el) {
        el.focus();
        el.click();
        return {
            found: true,
            tag: el.tagName,
            placeholder: el.getAttribute('placeholder') || '',
            ce: el.contentEditable,
            rect: el.getBoundingClientRect()
        };
    }
    return {found: false};
}"""

# JavaScript to find and click the model selector to switch to Pro
SWITCH_TO_PRO_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 10) return [];
        const results = [];
        const all = root.querySelectorAll('*');
        for (const el of all) {
            const text = (el.textContent || '').trim();
            // Look for the model selector button (has 'Nano Banana' and a dropdown arrow)
            if (text.includes('Nano Banana') && !text.includes('Pro') && el.offsetParent !== null) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && rect.height < 60) {
                    results.push({x: rect.x + rect.width/2, y: rect.y + rect.height/2, text: text.substring(0,40)});
                }
            }
            if (el.shadowRoot) {
                results.push(...findInShadow(el.shadowRoot, depth + 1));
            }
        }
        return results;
    }
    return findInShadow(document, 0);
}"""

# New JS to handle the permission pop-up
ACCEPT_PERMISSIONS_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 10) return null;
        const all = root.querySelectorAll('*');
        for (const el of all) {
            const text = (el.textContent || '').trim();
            if (text === 'Accept permissions' && el.offsetParent !== null) {
                const rect = el.getBoundingClientRect();
                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
            }
            if (el.shadowRoot) {
                const found = findInShadow(el.shadowRoot, depth + 1);
                if (found) return found;
            }
        }
        return null;
    }
    return findInShadow(document, 0);
}"""

FIND_PRO_OPTION_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 10) return [];
        const results = [];
        const all = root.querySelectorAll('*');
        for (const el of all) {
            const text = (el.textContent || '').trim();
            // Look for 'Nano Banana Pro' in any visible element
            if (text === 'Nano Banana Pro' && el.offsetParent !== null) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    results.push({x: rect.x + rect.width/2, y: rect.y + rect.height/2, text: text});
                }
            }
            if (el.shadowRoot) {
                results.push(...findInShadow(el.shadowRoot, depth + 1));
            }
        }
        return results;
    }
    return findInShadow(document, 0);
}"""

# ========================================================================
# AGENT SETTINGS PANEL JS
# ========================================================================
# The Flow UI has an "Agent settings" panel opened by clicking the tune/
# Settings button (aria-label="Settings") in the prompt input toolbar.
# The panel contains:
#   - "Confirm before generating": Always / Never radio buttons
#   - "Image generation default": aspect ratio, multiplier, model dropdown
#   - "Video generation default": aspect ratio, multiplier, model dropdown
#   - "Save" button
# The Flow Agent decides whether to generate image or video based on the
# prompt content. These settings configure the defaults for each mode.
# ========================================================================

# JavaScript to find and click the Settings (tune) button in the prompt toolbar
FIND_SETTINGS_BUTTON_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 15) return null;
        const all = root.querySelectorAll('*');
        for (const el of all) {
            const aria = (el.getAttribute('aria-label') || '').toLowerCase();
            const text = (el.textContent || '').trim();
            const tag = el.tagName;
            // The Settings button has aria-label="Settings" and text contains "tune"
            if ((aria === 'settings' || text === 'tuneSettings') 
                && tag === 'BUTTON' && el.offsetParent !== null) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 20 && rect.height > 20) {
                    return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                }
            }
            if (el.shadowRoot) {
                const found = findInShadow(el.shadowRoot, depth + 1);
                if (found) return found;
            }
        }
        return null;
    }
    return findInShadow(document, 0);
}"""

# JavaScript to check if the Agent Settings panel is currently open
IS_SETTINGS_OPEN_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 15) return false;
        const all = root.querySelectorAll('*');
        for (const el of all) {
            const text = (el.textContent || '').trim();
            if (text === 'Agent settings' && el.offsetParent !== null) {
                return true;
            }
            if (el.shadowRoot) {
                if (findInShadow(el.shadowRoot, depth + 1)) return true;
            }
        }
        return false;
    }
    return findInShadow(document, 0);
}"""

# JavaScript to find a clickable element by exact text inside the settings panel
FIND_SETTINGS_ELEMENT_JS = """(targetText) => {
    function findInShadow(root, depth) {
        if (depth > 15) return null;
        const all = root.querySelectorAll('*');
        for (const el of all) {
            const text = (el.textContent || '').trim();
            if (text === targetText && el.offsetParent !== null) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 5 && rect.height > 5) {
                    return {x: rect.x + rect.width/2, y: rect.y + rect.height/2,
                            tag: el.tagName, text: text.substring(0, 50)};
                }
            }
            if (el.shadowRoot) {
                const found = findInShadow(el.shadowRoot, depth + 1);
                if (found) return found;
            }
        }
        return null;
    }
    return findInShadow(document, 0);
}"""

# JavaScript to find the video model dropdown in the Agent Settings panel.
# The panel has "Video generation default" section with a model dropdown below it.
# We need to find the dropdown UNDER the "Video generation default" heading.
FIND_VIDEO_MODEL_DROPDOWN_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 15) return null;
        const all = root.querySelectorAll('*');
        let foundVideoSection = false;
        for (const el of all) {
            const text = (el.textContent || '').trim();
            // Mark when we pass the video section heading
            if (text === 'Video generation default') {
                foundVideoSection = true;
                continue;
            }
            // After finding the video section, look for the model dropdown
            // It's typically a div/button with a dropdown arrow containing the model name
            if (foundVideoSection && el.offsetParent !== null) {
                const tag = el.tagName;
                const rect = el.getBoundingClientRect();
                // The dropdown is wide (>150px) and has the model name + arrow
                if ((text.includes('Omni') || text.includes('Veo') || text.includes('Flash'))
                    && rect.width > 100 && rect.height > 20 && rect.height < 60
                    && (tag === 'DIV' || tag === 'BUTTON' || tag === 'SPAN')) {
                    return {x: rect.x + rect.width/2, y: rect.y + rect.height/2,
                            text: text.substring(0, 50)};
                }
            }
            if (el.shadowRoot) {
                const found = findInShadow(el.shadowRoot, depth + 1);
                if (found) return found;
            }
        }
        return null;
    }
    return findInShadow(document, 0);
}"""

# JavaScript to dump all visible elements in the settings panel for debugging
DUMP_SETTINGS_PANEL_JS = """() => {
    function findInShadow(root, depth) {
        if (depth > 15) return [];
        const results = [];
        const all = root.querySelectorAll('*');
        for (const el of all) {
            const text = (el.textContent || '').trim();
            const aria = el.getAttribute('aria-label') || '';
            const role = el.getAttribute('role') || '';
            const tag = el.tagName;
            const rect = el.getBoundingClientRect();
            // Only include visible elements with some text
            if (rect.width > 5 && rect.height > 5 && el.offsetParent !== null
                && text.length > 0 && text.length < 60) {
                results.push({
                    tag, text: text.substring(0, 50), aria, role,
                    x: Math.round(rect.x + rect.width/2),
                    y: Math.round(rect.y + rect.height/2),
                    w: Math.round(rect.width), h: Math.round(rect.height)
                });
            }
            if (el.shadowRoot) {
                results.push(...findInShadow(el.shadowRoot, depth + 1));
            }
        }
        return results;
    }
    return findInShadow(document, 0);
}"""


class FlowBridge:
    def __init__(self, headless: bool = False, profile_dir: str = "playwright_profile"):
        self.headless = headless
        self.profile_dir = os.path.abspath(profile_dir)
        self.playwright = None
        self.context = None
        self.page = None
        self.pages = [] # Pool of active worker pages
        self.captured_images = {} # Map page -> list of image binaries
        self.captured_videos = {} # Map page -> list of video binaries/URLs
        self.is_generating = {} # Map page -> bool
        self.warmed_up = False # Track if cookie warmer has run

    async def start(self):
        print("Starting Flow UI Bridge...")
        self.playwright = await async_playwright().start()
        
        # Load proxy config from environment if present
        proxy_server = os.getenv("RESIDENTIAL_PROXY_SERVER")
        proxy_user = os.getenv("RESIDENTIAL_PROXY_USERNAME")
        proxy_pass = os.getenv("RESIDENTIAL_PROXY_PASSWORD")
        
        proxy_args = {}
        if proxy_server:
            proxy_args["proxy"] = {
                "server": proxy_server
            }
            if proxy_user:
                proxy_args["proxy"]["username"] = proxy_user
            if proxy_pass:
                proxy_args["proxy"]["password"] = proxy_pass
            print(f"   [PROXY] Routing browser through: {proxy_server}")
            
        import browser_helper
        self.browser_session = await browser_helper.get_browser_context(
            self.playwright,
            headless=self.headless,
            profile_dir=self.profile_dir
        )
        self.context = self.browser_session.context
        # We'll create pages as needed in the batch runner
        print("   Bridge Ready!")

    async def warm_up(self):
        """Surf Google/News to create human-like cookie history (Anti-Ban)."""
        if self.warmed_up: return
        print("\n   [WARM-UP] Mimicking human browsing to warm up cookies...")
        page = await self.context.new_page()
        try:
            await page.goto("https://www.google.com/search?q=latest+fashion+trends+2026", timeout=60000)
            await asyncio.sleep(3)
            await page.goto("https://news.google.com", timeout=60000)
            await asyncio.sleep(3)
            self.warmed_up = True
            print("   [WARM-UP] Cookies warmed up!")
        except Exception as e:
            print(f"   [WARM-UP] Warning: {e}")
        finally:
            await page.close()

    async def _setup_page(self, capture_video: bool = False):
        """Create and configure a new worker page with interception.
        
        Args:
            capture_video: If True, also capture video/mp4 responses from the network.
        """
        page = await self.context.new_page()
        try:
            await page.set_viewport_size({"width": 1280, "height": 720})
        except Exception as e:
            print(f"   [!] Page viewport resize warning: {e}")
        self.captured_images[page] = []
        self.captured_videos[page] = []
        self.is_generating[page] = False

        async def _on_response(response):
            if not self.is_generating.get(page): return
            try:
                content_type = response.headers.get("content-type", "")
                
                # Capture images (existing logic)
                if response.request.resource_type == "image":
                    body = await response.body()
                    if len(body) > 250 * 1024: # > 250KB
                        self.captured_images[page].append({
                            "data": body,
                            "url": response.url,
                            "size": len(body)
                        })
                
                # Capture video responses
                if capture_video:
                    url = response.url
                    is_video_content = (
                        "video/" in content_type
                        or url.endswith(".mp4")
                        or "googleusercontent.com" in url and "video" in url.lower()
                    )
                    if is_video_content and response.status == 200:
                        try:
                            body = await response.body()
                            if len(body) > 50 * 1024: # > 50KB (videos are large)
                                print(f"   [VIDEO-CAPTURE] Intercepted video: {url[:80]}... ({len(body)//1024}KB)")
                                self.captured_videos[page].append({
                                    "data": body,
                                    "url": url,
                                    "size": len(body),
                                    "content_type": content_type
                                })
                        except Exception:
                            # Video might be too large to buffer - save URL for later download
                            print(f"   [VIDEO-CAPTURE] Video too large to buffer, saving URL: {url[:80]}")
                            self.captured_videos[page].append({
                                "data": None,
                                "url": url,
                                "size": 0,
                                "content_type": content_type
                            })
                    
                    # Also capture video download URLs from JSON API responses
                    if ("googleapis.com" in url and response.status == 200 
                        and "application/json" in content_type):
                        try:
                            body_text = await response.text()
                            if '"done":true' in body_text or 'googleusercontent.com' in body_text:
                                import json as _json
                                data = _json.loads(body_text)
                                # Recursively find video URLs
                                def _extract_video_urls(obj):
                                    urls = []
                                    if isinstance(obj, dict):
                                        for k, v in obj.items():
                                            if isinstance(v, str) and (
                                                v.endswith('.mp4') or
                                                ('googleusercontent.com' in v and 'video' in v.lower()) or
                                                ('googlevideo.com' in v)
                                            ):
                                                urls.append(v)
                                            else:
                                                urls.extend(_extract_video_urls(v))
                                    elif isinstance(obj, list):
                                        for item in obj:
                                            urls.extend(_extract_video_urls(item))
                                    return urls
                                video_urls = _extract_video_urls(data)
                                for vu in video_urls:
                                    print(f"   [VIDEO-CAPTURE] Found video URL in API response: {vu[:80]}...")
                                    self.captured_videos[page].append({
                                        "data": None,
                                        "url": vu,
                                        "size": 0,
                                        "content_type": "video/mp4"
                                    })
                        except Exception:
                            pass
            except: pass

        async def _on_request(request):
            import json as _json
            # Spy on ALL POST requests to Google APIs
            if request.method == "POST" and ("googleapis.com" in request.url or "labs.google" in request.url):
                url_lower = request.url.lower()
                if "generate" in url_lower:
                    label = "GENERATE"
                elif "upload" in url_lower or "media" in url_lower or "asset" in url_lower or "image" in url_lower:
                    label = "UPLOAD/MEDIA"
                elif "project" in url_lower:
                    label = "PROJECT"
                else:
                    label = "OTHER"
                print(f"\n   [SPY-{label}] POST {request.url[:120]}")
                try:
                    post_data = request.post_data
                    headers = request.headers
                    if "generate" in url_lower and post_data:
                        with open("spy_payload.json", "w") as f:
                            f.write(post_data)
                        if headers:
                            with open("spy_headers.json", "w") as f:
                                f.write(_json.dumps(dict(headers), indent=2))
                    entry = {
                        "label": label, "url": request.url,
                        "headers": dict(headers) if headers else {},
                        "post_data_preview": (post_data[:2000] if post_data else None),
                        "post_data_length": len(post_data) if post_data else 0,
                    }
                    with open("spy_all_requests.jsonl", "a") as f:
                        f.write(_json.dumps(entry) + "\n")
                except Exception as e:
                    print(f"   [SPY] Error: {e}")

        page.on("request", _on_request)
        page.on("response", _on_response)
        return page

    def _find_active_page(self):
        """Helper to ensure we are using the correct page object."""
        # In this multi-page version, we just ensure self.page is set.
        # If it's already set (by worker_job), we just return.
        if self.page:
            return True
        
        if self.context and self.context.pages:
            self.page = self.context.pages[-1]
            return True
        return False

    async def _create_new_project(self):
        """Navigate to Flow and create a new project automatically."""
        print("\n   AUTO-NAV: Creating new Flow project...")
        self._find_active_page()
        
        # Navigate to the Flow tool page
        try:
            await self.page.goto("https://labs.google/fx/tools/flow", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"   Nav warning (may be OK): {e}")
        
        # Wait for the page to fully load
        print("   Waiting for page to fully load...")
        await asyncio.sleep(15)
        self._find_active_page()
        
        # Click "+ New project"
        print("   Looking for 'New project' button...")
        try:
            loc = self.page.get_by_text("New project", exact=False)
            count = await loc.count()
            if count > 0:
                print(f"   Found 'New project' ({count} matches)")
                await loc.first.click()
                print("   Clicked 'New project'!")
            else:
                print("   Could not find 'New project' button.")
        except Exception as e:
            print(f"   New project click error: {e}")
        
        # Wait for the new project page to load
        print("   Waiting for new project to load...")
        await asyncio.sleep(8)
        self._find_active_page()
        print(f"   Project URL: {self.page.url}")
        
        # Close the right sidebar if open to reveal the bottom toolbar
        await self._close_sidebar_if_open()

    async def _close_sidebar_if_open(self):
        """Close the right sidebar (Flow Creation Agent) if open to reveal bottom toolbar."""
        print("   Checking if right sidebar is open...")
        self._find_active_page()
        
        closed = await self.page.evaluate("""() => {
            function findAndClickClose(root, depth = 0) {
                if (depth > 15) return false;
                const all = root.querySelectorAll('*');
                for (const el of all) {
                    const tag = el.tagName;
                    const aria = el.getAttribute('aria-label') || '';
                    const text = (el.textContent || '').trim();
                    
                    if (tag === 'BUTTON' && (text === 'closeClose' || text.toLowerCase() === 'close' || aria.toLowerCase().includes('close') || aria === 'Close session')) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            el.click();
                            return true;
                        }
                    }
                    if (el.shadowRoot) {
                        if (findAndClickClose(el.shadowRoot, depth + 1)) return true;
                    }
                }
                return false;
            }
            return findAndClickClose(document);
        }""")
        if closed:
            print("   Closed right sidebar successfully.")
            await asyncio.sleep(2)
        else:
            print("   Right sidebar was not open or close button not found.")

    def _find_active_page(self):
        """Find the active Flow page from all open pages."""
        for p in self.context.pages:
            if "labs.google" in p.url:
                self.page = p
                return True
        return False

    async def switch_to_pro(self):
        """Handle the switch to Nano Banana Pro."""
        print("\n   Checking for permissions and switching to Nano Banana Pro...")
        self._find_active_page()
        try:
            # Step 0: Check for "Accept permissions" pop-up
            perm_btn = await self.page.evaluate(ACCEPT_PERMISSIONS_JS)
            if perm_btn:
                print("    Found Permission Pop-up. Clicking Accept...")
                await self.page.mouse.click(perm_btn['x'], perm_btn['y'])
                await asyncio.sleep(2)

            # Turn Agent OFF to expose manual controls
            await self._turn_off_agent()
            
            # Open manual controls popup
            await self._open_manual_controls_popup()
            
            # Select "Nano Banana Pro" image model
            success = await self._select_image_model("Nano Banana Pro")
            
            # Close the popup by pressing Escape
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(1)
            
            return success
        except Exception as e:
            print(f"   Switch to Pro error: {e}")
            return False

    async def _focus_prompt_box(self):
        """Use shadow DOM piercing to find and focus the prompt input."""
        try:
            # Prioritize native Playwright locator for role="textbox" (Shadow DOM piercing)
            locator = self.page.locator('div[role="textbox"]')
            if await locator.is_visible():
                await locator.click(force=True)
                await locator.focus()
                print("    Found prompt: <DIV> role='textbox' using Playwright locator.")
                return True
        except Exception as e:
            print(f"    Playwright locator focus error: {e}")

        result = await self.page.evaluate(FIND_PROMPT_JS)
        if result.get('found'):
            print(f"    Found prompt: <{result['tag']}> placeholder='{result.get('placeholder','')}'")
            return True
        else:
            print("    Shadow DOM search found nothing. Trying Tab key fallback...")
            # Fallback: press Tab repeatedly to cycle through focusable elements
            for i in range(15):
                await self.page.keyboard.press("Tab")
                await asyncio.sleep(0.3)
                # Check if we landed on something at the bottom
                check = await self.page.evaluate("""() => {
                    const el = document.activeElement;
                    if (!el) return null;
                    const rect = el.getBoundingClientRect();
                    return {
                        tag: el.tagName,
                        y: rect.y,
                        h: window.innerHeight,
                        ce: el.contentEditable,
                        ph: el.getAttribute('placeholder') || ''
                    };
                }""")
                if check and check['y'] > check['h'] * 0.7:
                    print(f"    Tab landed on bottom element: <{check['tag']}> at y={int(check['y'])}")
                    return True
            print("    Tab fallback failed too.")
            return False

    async def generate_image(
        self,
        prompt: str,
        reference_images: List[str] = None,
        output_prefix: str = "out",
        page=None # Use provided page or fallback to self.page
    ) -> List[str]:
        if page: self.page = page
        if not self.page:
            return []

        output_dir = os.path.join("output", "vton")
        os.makedirs(output_dir, exist_ok=True)

        await self._create_new_project()

        # ====== STEP 0: Switch to Pro model ======
        await self.switch_to_pro()

        # ====== STEP 1: Upload images ======
        if reference_images:
            abs_paths = [os.path.abspath(p) for p in reference_images if os.path.exists(p)]
            if abs_paths:
                print(f"\n   STEP 1: Uploading {len(abs_paths)} images...")
                try:
                    file_input = self.page.locator("input[type='file']").first
                    await file_input.set_input_files(abs_paths)
                    print("    Images uploaded!")
                except Exception as e:
                    print(f"   Upload failed: {e}")
                    return []

                print("   Waiting 40s for upload to process...")
                for s in range(4):
                    await asyncio.sleep(10)
                    print(f"   ... {(s+1)*10}s")
                
                self._find_active_page()
                print("   Upload to library complete!")

                # ====== STEP 1.5: Attach images to prompt ======
                print("\n   STEP 1.5: Attaching images to prompt...")
                
                # Get the prompt box location so we can find the "+" to its left
                prompt_rect = await self.page.evaluate(FIND_PROMPT_JS)
                if not (prompt_rect.get('found') and prompt_rect.get('rect')):
                    print("    Could not find prompt box. Please attach images manually.")
                else:
                    r = prompt_rect['rect']
                    
                    # Find the actual "+" button - it's BELOW the prompt box, not to the left
                    plus_btn = await self.page.evaluate("""() => {
                        function findInShadow(root, depth) {
                            if (depth > 15) return null;
                            const all = root.querySelectorAll('*');
                            for (const el of all) {
                                const text = (el.textContent || '').trim();
                                const aria = el.getAttribute('aria-label') || '';
                                const tag = el.tagName;
                                
                                // Look for a small clickable element with "+" text near the bottom
                                if ((text === '+' || text === 'add' || aria.toLowerCase().includes('add') || 
                                     aria.toLowerCase().includes('attach') || aria.toLowerCase().includes('image'))
                                    && (tag === 'BUTTON' || tag === 'A' || tag === 'DIV' || tag === 'SPAN')
                                    && el.offsetParent !== null) {
                                    const rect = el.getBoundingClientRect();
                                    // The + button is small (around 30-50px) and near the bottom of the viewport
                                    if (rect.width > 15 && rect.width < 80 && rect.height > 15 && rect.height < 80 
                                        && rect.top > window.innerHeight * 0.7) {
                                        return {x: rect.x + rect.width/2, y: rect.y + rect.height/2, 
                                                info: tag + ' text=' + text + ' aria=' + aria};
                                    }
                                }
                                if (el.shadowRoot) {
                                    const found = findInShadow(el.shadowRoot, depth + 1);
                                    if (found) return found;
                                }
                            }
                            return null;
                        }
                        return findInShadow(document, 0);
                    }""")
                    
                    if plus_btn:
                        plus_x = plus_btn['x']
                        plus_y = plus_btn['y']
                        print(f"   Found '+' button at ({int(plus_x)}, {int(plus_y)}) [{plus_btn.get('info','')}]")
                    else:
                        # Fallback: the + is below the left edge of the prompt box
                        plus_x = r['x'] + 20
                        plus_y = r['y'] + r['height'] + 30
                        print(f"   '+' button not found, guessing at ({int(plus_x)}, {int(plus_y)})")
                    
                    # Get the filenames we need to click in the picker
                    filenames = [os.path.basename(p) for p in abs_paths]
                    
                    for idx, fname in enumerate(filenames):
                        print(f"\n   Attaching image {idx+1}/{len(filenames)}: {fname}")
                        
                        # Click "+" to open the picker panel
                        print(f"   Clicking '+' at ({int(plus_x)}, {int(plus_y)})")
                        await self.page.mouse.click(plus_x, plus_y)
                        await asyncio.sleep(3)
                        
                        # METHOD 1: Use Playwright's native text locator (handles some shadow DOM)
                        clicked = False
                        try:
                            loc = self.page.get_by_text(fname, exact=False)
                            count = await loc.count()
                            print(f"   Playwright found {count} elements matching '{fname}'")
                            if count > 0:
                                await loc.first.click()
                                clicked = True
                                print(f"   Clicked '{fname}' via Playwright locator!")
                        except Exception as e:
                            print(f"   Playwright locator error: {e}")
                        
                        if not clicked:
                            # METHOD 2: Try without extension
                            name_no_ext = os.path.splitext(fname)[0]
                            try:
                                loc2 = self.page.get_by_text(name_no_ext, exact=False)
                                count2 = await loc2.count()
                                print(f"   Playwright found {count2} elements matching '{name_no_ext}'")
                                if count2 > 0:
                                    await loc2.first.click()
                                    clicked = True
                                    print(f"   Clicked '{name_no_ext}' via Playwright locator!")
                            except Exception as e:
                                print(f"   Playwright locator error: {e}")
                        
                        if not clicked:
                            # METHOD 3: JS shadow DOM piercing text search
                            result = await self.page.evaluate("""(targetName) => {
                                function findInShadow(root, depth) {
                                    if (depth > 15) return null;
                                    const all = root.querySelectorAll('*');
                                    for (const el of all) {
                                        // Check direct text content (not children's text)
                                        const directText = Array.from(el.childNodes)
                                            .filter(n => n.nodeType === 3)
                                            .map(n => n.textContent.trim())
                                            .join('');
                                        const fullText = (el.textContent || '').trim();
                                        
                                        if ((directText.includes(targetName) || fullText === targetName) 
                                            && el.offsetParent !== null) {
                                            const rect = el.getBoundingClientRect();
                                            if (rect.width > 30 && rect.height > 15 && rect.height < 80) {
                                                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                                            }
                                        }
                                        if (el.shadowRoot) {
                                            const found = findInShadow(el.shadowRoot, depth + 1);
                                            if (found) return found;
                                        }
                                    }
                                    return null;
                                }
                                return findInShadow(document, 0);
                            }""", fname)
                            
                            if result:
                                print(f"   Found '{fname}' via JS at ({int(result['x'])}, {int(result['y'])})")
                                await self.page.mouse.click(result['x'], result['y'])
                                clicked = True
                        
                        if not clicked:
                            print(f"   FAILED to find '{fname}'. Attach manually.")
                        
                        await asyncio.sleep(2)
                    
                    print("    Image attachment complete!")

                
                await asyncio.sleep(2)

        # ====== STEP 2: Find and type in prompt box ======
        print("\n   Waiting for page to settle...")
        await asyncio.sleep(3)
        self._find_active_page()

        print("\n   STEP 2: Searching for prompt box (shadow DOM piercing)...")
        
        try:
            found = await self._focus_prompt_box()
        except Exception as e:
            print(f"   Page reference stale, re-acquiring... ({e})")
            self._find_active_page()
            found = await self._focus_prompt_box()
        
        if found:
            try:
                await asyncio.sleep(0.5)
                await self.page.keyboard.press("Control+a")
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(0.3)
                await self.page.keyboard.type(prompt, delay=10)
                print("    Prompt typed!")
            except Exception as e:
                print(f"   Typing failed ({e}), re-acquiring page...")
                self._find_active_page()
                found2 = await self._focus_prompt_box()
                if found2:
                    await asyncio.sleep(0.3)
                    await self.page.keyboard.type(prompt, delay=10)
                    print("    Prompt typed (retry)!")
                else:
                    print("    Could not re-focus prompt box after retry.")
        else:
            print("    Could not find prompt box. Retrying after delay...")
            await asyncio.sleep(5)
            self._find_active_page()
            found3 = await self._focus_prompt_box()
            if found3:
                await self.page.keyboard.type(prompt, delay=10)
                print("    Prompt typed (late retry)!")
            else:
                print("    FAILED: Could not find prompt box after all retries.")


        await asyncio.sleep(2)

        # ====== STEP 3: Generate ======
        await asyncio.sleep(2)
        self._find_active_page()

        print(f"\n   [{output_prefix}] Pressing Enter to generate...")
        self.captured_images[self.page] = [] # Reset for this job
        self.is_generating[self.page] = True
        await self.page.keyboard.press("Enter")

        # Upgrade 3: Smart Waiting
        print(f"   [{output_prefix}] Generating (Smart Polling)...")
        max_wait = 180 # 3 min max timeout
        start_gen = asyncio.get_event_loop().time()
        
        # Give it a few seconds to start showing "99%"
        await asyncio.sleep(5)
        
        while (asyncio.get_event_loop().time() - start_gen) < max_wait:
            elapsed = int(asyncio.get_event_loop().time() - start_gen)
            
            # Check for "99%" or "Generating" text in the DOM
            status = await self.page.evaluate("""() => {
                const text = document.body.innerText;
                const hasLoading = text.includes('99%') || text.includes('Generating...');
                const hasResults = document.querySelectorAll('img').length > 5; // Rough check
                return { hasLoading, hasResults };
            }""")
            
            if not status['hasLoading'] and elapsed > 40:
                print(f"    [{output_prefix}] Settle detected at {elapsed}s.")
                break
            
            if elapsed % 20 == 0:
                print(f"    [{output_prefix}] ... {elapsed}s (99% still visible)")
            
            await asyncio.sleep(5)
        
        self.is_generating[self.page] = False
        # Extra buffer for page to stabilize
        await asyncio.sleep(5)

        # ====== STEP 4: Save results ======
        self._find_active_page()
        print(f"\n   [{output_prefix}] Saving results...")
        
        saved = []
        
        # First priority: Use captured network responses
        captured = self.captured_images.get(self.page, [])
        if captured:
            print(f"   [{output_prefix}] Found {len(captured)} network images")
            seen_sizes = set()
            res_idx = 1
            for img in captured:
                if img['size'] in seen_sizes: continue
                seen_sizes.add(img['size'])
                
                path = os.path.join(output_dir, f"{output_prefix}_{res_idx}.png")
                with open(path, "wb") as f:
                    f.write(img['data'])
                print(f"    Saved (Network): {path} ({img['size']//1024}KB)")
                saved.append(path)
                res_idx += 1
        
        # Fallback: DOM scraping if network interception missed them
        if not saved:
            print("   No images from network, falling back to DOM scraping...")
            try:
                # [Previous DOM scraping logic here...]
                images_data = await self.page.evaluate("""() => {
                    function findInShadow(root, depth) {
                        if (depth > 15) return [];
                        const results = [];
                        const all = root.querySelectorAll('*');
                        for (const el of all) {
                            if (el.tagName === 'IMG' && el.src && el.offsetParent !== null) {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 150 && rect.height > 150 && rect.top < window.innerHeight * 0.7
                                    && !el.src.includes('avatar') && !el.src.includes('icon')) {
                                    results.push({ src: el.src, size: rect.width * rect.height });
                                }
                            }
                            if (el.shadowRoot) results.push(...findInShadow(el.shadowRoot, depth + 1));
                        }
                        return results;
                    }
                    return findInShadow(document, 0);
                }""")
                
                for idx, img_info in enumerate(images_data):
                    path = os.path.join(output_dir, f"{output_prefix}_fallback_{idx+1}.png")
                    await self.page.locator(f'img[src="{img_info["src"]}"]').first.screenshot(path=path)
                    saved.append(path)
                    print(f"    Saved (DOM Fallback): {path}")
            except Exception as e:
                print(f"   DOM Fallback failed: {e}")
                
        if not saved:
            path = os.path.join(output_dir, f"{output_prefix}_final_page.png")
            await self.page.screenshot(path=path)
            saved.append(path)
            print(f"    Saved (Page Screenshot Fallback): {path}")
        
        return saved

    async def generate_batch(self, jobs: list, max_workers: int = 1) -> list:
        """Run multiple generations with parallel page workers."""
        all_results = []
        
        # Upgrade 2: Cookie Warmup
        await self.warm_up()

        # Create worker pages
        print(f"\nLaunching {max_workers} worker tabs...")
        workers = []
        for _ in range(max_workers):
            p = await self._setup_page()
            workers.append(p)

        # Semaphore to limit concurrent workers
        sem = asyncio.Semaphore(max_workers)

        async def worker_job(job, page):
            async with sem:
                try:
                    return await self.generate_image(
                        prompt=job['prompt'],
                        reference_images=job.get('reference_images', []),
                        output_prefix=job.get('output_prefix', 'batch'),
                        page=page
                    )
                except Exception as e:
                    print(f"   Worker Error: {e}")
                    return []

        # Process jobs in chunks of max_workers
        for i in range(0, len(jobs), max_workers):
            chunk = jobs[i : i + max_workers]
            tasks = []
            for j, job in enumerate(chunk):
                tasks.append(worker_job(job, workers[j]))
            
            print(f"\nRunning batch of {len(tasks)} workers...")
            results = await asyncio.gather(*tasks)
            for r in results:
                all_results.extend(r)

        # Cleanup worker pages
        for p in workers: await p.close()
        
        return all_results

    async def _turn_off_agent(self):
        """Turn off the Agent toggle so manual Image/Video controls appear.
        
        The Agent button is a pill toggle under the prompt input.
        When pressed=true (Agent ON), no manual controls are visible.
        When pressed=false (Agent OFF), Image/Video tabs, ratio, model appear.
        """
        print("\n   Checking Agent toggle state...")
        self._find_active_page()
        
        # Poll for up to 30 seconds
        for attempt in range(15):
            agent_info = await self.page.evaluate("""() => {
                function findInShadow(root, depth) {
                    if (depth > 15) return null;
                    const all = root.querySelectorAll('*');
                    for (const el of all) {
                        const text = (el.textContent || '').trim();
                        const pressed = el.getAttribute('aria-pressed');
                        const tag = el.tagName;
                        if (text === 'Agent' && tag === 'BUTTON') {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 30 && rect.height > 15 && rect.height < 60) {
                                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2,
                                        pressed: pressed};
                            }
                        }
                        if (el.shadowRoot) {
                            const found = findInShadow(el.shadowRoot, depth + 1);
                            if (found) return found;
                        }
                    }
                    return null;
                }
                return findInShadow(document, 0);
            }""")
            
            if agent_info:
                if agent_info.get('pressed') == 'true':
                    print(f"   Agent is ON (pressed=true). Clicking to turn OFF...")
                    await self.page.mouse.click(agent_info['x'], agent_info['y'])
                    await asyncio.sleep(2.5)
                    print("   Agent turned OFF. Manual controls should now be available.")
                    return True
                else:
                    print("   Agent is already OFF (pressed=false).")
                    return True
            
            await asyncio.sleep(2)
            
        print("   Agent button not found after 30 seconds. Trying fallback coordinates (420, 663)...")
        try:
            await self.page.mouse.click(420, 663)
            await asyncio.sleep(2.5)
            return True
        except Exception as e:
            print(f"   Fallback click failed: {e}")
        return False

    async def _open_manual_controls_popup(self):
        """Open the manual controls popup by clicking the model summary button.
        
        When Agent is OFF, the bottom toolbar shows a compact summary like:
          '🍌 Nano Banana 2 crop_16_9 x2'
        Clicking it opens a popup with Image/Video tabs, ratio tabs, multiplier, model dropdown.
        """
        print("\n   Opening manual controls popup...")
        self._find_active_page()
        
        # Poll for up to 30 seconds
        for attempt in range(15):
            # Check if popup is already open (look for Image/Video tabs with role="tab")
            is_open = await self.page.evaluate("""() => {
                function findInShadow(root, depth) {
                    if (depth > 15) return false;
                    const all = root.querySelectorAll('*');
                    for (const el of all) {
                        const role = el.getAttribute('role') || '';
                        const text = (el.textContent || '').trim();
                        if (role === 'tab' && (text === 'imageImage' || text === 'play_circleVideo')) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                return true;
                            }
                        }
                        if (el.shadowRoot) {
                            if (findInShadow(el.shadowRoot, depth + 1)) return true;
                        }
                    }
                    return false;
                }
                return findInShadow(document, 0);
            }""")
            
            if is_open:
                print("   Popup already open.")
                return True
            
            # Find and click the model summary button in the toolbar
            summary_btn = await self.page.evaluate("""() => {
                function findInShadow(root, depth) {
                    if (depth > 15) return null;
                    const all = root.querySelectorAll('*');
                    for (const el of all) {
                        const text = (el.textContent || '').trim();
                        const tag = el.tagName;
                        if (tag === 'BUTTON'
                            && (text.includes('Nano Banana') || text.includes('Omni') 
                                || text.includes('Veo') || text.includes('crop_'))
                            && text.length < 80) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 80 && rect.height > 20 && rect.height < 60) {
                                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2,
                                        text: text.substring(0, 50)};
                            }
                        }
                        if (el.shadowRoot) {
                            const found = findInShadow(el.shadowRoot, depth + 1);
                            if (found) return found;
                        }
                    }
                    return null;
                }
                return findInShadow(document, 0);
            }""")
            
            if summary_btn:
                print(f"   Found model summary button: '{summary_btn['text']}'. Clicking...")
                await self.page.mouse.click(summary_btn['x'], summary_btn['y'])
                await asyncio.sleep(2.5)
                return True
                
            await asyncio.sleep(2)
            
        print("   Could not find model summary button to open popup after 30 seconds. Trying fallback coordinates (817, 663)...")
        try:
            await self.page.mouse.click(817, 663)
            await asyncio.sleep(2.5)
            return True
        except Exception as e:
            print(f"   Fallback click failed: {e}")
        return False

    async def _switch_to_video_mode(self):
        """Switch to Video mode using the manual controls popup.
        
        Flow (June 2026): Agent toggle OFF → click model summary → popup shows
        Image/Video tabs. Click the Video tab to switch to video generation.
        """
        print("\n   STEP: Switching to Video mode...")
        self._find_active_page()
        
        # 1. Turn Agent OFF
        await self._turn_off_agent()
        
        # 2. Open the manual controls popup
        popup_opened = await self._open_manual_controls_popup()
        if not popup_opened:
            print("   WARNING: Could not open manual controls popup.")
            return False
        
        # 3. Click the Video tab with polling
        for attempt in range(15):
            video_btn = await self.page.evaluate("""() => {
                function findInShadow(root, depth) {
                    if (depth > 15) return null;
                    const all = root.querySelectorAll('*');
                    for (const el of all) {
                        const text = (el.textContent || '').trim();
                        const role = el.getAttribute('role') || '';
                        if ((text === 'play_circleVideo' || text === 'Video') 
                            && (role === 'tab' || el.tagName === 'BUTTON')) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 50 && rect.height > 20) {
                                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
                            }
                        }
                        if (el.shadowRoot) {
                            const found = findInShadow(el.shadowRoot, depth + 1);
                            if (found) return found;
                        }
                    }
                    return null;
                }
                return findInShadow(document, 0);
            }""")
            
            if video_btn:
                print("   Found Video tab. Clicking...")
                await self.page.mouse.click(video_btn['x'], video_btn['y'])
                await asyncio.sleep(2)
                print("   Switched to Video mode!")
                return True
                
            await asyncio.sleep(2)
            
        print("   WARNING: Could not find Video tab after 30 seconds. Trying fallback coordinates (829, 427)...")
        try:
            await self.page.mouse.click(829, 427)
            await asyncio.sleep(2)
            print("   Clicked fallback coordinates for Video tab.")
            return True
        except Exception as e:
            print(f"   Fallback click failed: {e}")
        return False

    async def _select_aspect_ratio(self, ratio: str = "16:9"):
        """Select an aspect ratio from the manual controls popup.
        
        Args:
            ratio: "16:9", "4:3", "1:1", "3:4", or "9:16"
        """
        print(f"   Selecting aspect ratio: {ratio}...")
        try:
            # The ratio tabs have text like "crop_16_916:9" but role="tab"
            # Use Playwright's get_by_role with the ratio text
            ratio_tab = self.page.get_by_role("tab", name=ratio)
            count = await ratio_tab.count()
            if count > 0:
                await ratio_tab.first.click()
                await asyncio.sleep(1)
                print(f"   Aspect ratio {ratio} selected!")
                return True
        except Exception as e:
            print(f"   Ratio selection error: {e}")
        
        print(f"   Could not find {ratio} tab. Using default.")
        return False

    async def _select_image_model(self, model_name: str = "Nano Banana Pro"):
        """Select an image model from the model dropdown in the manual controls popup.
        
        Args:
            model_name: Model name like "Nano Banana Pro", "Nano Banana 2", etc.
        """
        print(f"\n   Selecting image model: {model_name}...")
        self._find_active_page()
        
        # Switch to Image mode tab first
        try:
            image_tab = self.page.get_by_role("tab", name="Image")
            count = await image_tab.count()
            if count > 0:
                await image_tab.first.click()
                await asyncio.sleep(1.5)
                print("   Switched to Image mode tab!")
        except Exception as e:
            print(f"   Image tab click error: {e}")
            
        # Fallback tab click using JS
        switched_js = await self.page.evaluate("""() => {
            function findInShadow(root, depth) {
                if (depth > 15) return false;
                const all = root.querySelectorAll('*');
                for (const el of all) {
                    const text = (el.textContent || '').trim();
                    const role = el.getAttribute('role') || '';
                    if ((text === 'imageImage' || text === 'Image')
                        && (role === 'tab' || el.tagName === 'BUTTON')) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            el.click();
                            return true;
                        }
                    }
                    if (el.shadowRoot) {
                        if (findInShadow(el.shadowRoot, depth + 1)) return true;
                    }
                }
                return false;
            }
            return findInShadow(document, 0);
        }""")
        
        if not switched_js:
            print("   Image tab not found via JS. Trying fallback coordinates (697, 427)...")
            try:
                await self.page.mouse.click(697, 427)
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"   Fallback click failed: {e}")
        await asyncio.sleep(1)

        # Find the model dropdown button (contains arrow_drop_down icon)
        dropdown = await self.page.evaluate("""() => {
            function findInShadow(root, depth) {
                if (depth > 15) return null;
                const all = root.querySelectorAll('*');
                for (const el of all) {
                    const text = (el.textContent || '').trim();
                    const tag = el.tagName;
                    if (tag === 'BUTTON' && text.includes('arrow_drop_down')
                        && (text.includes('Banana') || text.includes('Nano') 
                            || text.includes('Omni') || text.includes('Veo') 
                            || text.includes('Flash'))) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            return {x: rect.x + rect.width/2, y: rect.y + rect.height/2,
                                    text: text.substring(0, 50)};
                        }
                    }
                    if (el.shadowRoot) {
                        const found = findInShadow(el.shadowRoot, depth + 1);
                        if (found) return found;
                    }
                }
                return null;
            }
            return findInShadow(document, 0);
        }""")
        
        if not dropdown:
            print(f"   Model dropdown not found via JS. Trying fallback coordinates (763, 560)...")
            dropdown = {'x': 763, 'y': 560, 'text': 'Fallback Dropdown'}
            
        current_model = dropdown.get('text', '')
        # Clean both for robust alphanumeric comparison
        clean_current = "".join([c for c in current_model.lower() if c.isalnum()])
        clean_target = "".join([c for c in model_name.lower() if c.isalnum()])
        
        if clean_target in clean_current and dropdown.get('text') != 'Fallback Dropdown':
            print(f"   Already using model: {current_model}")
            return True
            
        # Click dropdown to open model list
        print(f"   Opening model dropdown (current: '{current_model}')...")
        await self.page.mouse.click(dropdown['x'], dropdown['y'])
        await asyncio.sleep(2)
        
        # Find and click the target model in the dropdown list with a polling loop
        model_option = None
        for poll_attempt in range(10):
            model_option = await self.page.evaluate("""(targetModel) => {
                function findInShadow(root, depth) {
                    if (depth > 15) return null;
                    const all = root.querySelectorAll('*');
                    const cleanTarget = targetModel.toLowerCase().replace(/[^a-z0-9]/g, '');
                    for (const el of all) {
                        const text = (el.textContent || '').trim();
                        const cleanText = text.toLowerCase().replace(/[^a-z0-9]/g, '');
                        if (cleanText.includes(cleanTarget)
                            && !text.includes('arrow_drop_down')) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 50 && rect.height > 15 && rect.height < 60) {
                                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2,
                                        text: text.substring(0, 50)};
                            }
                        }
                        if (el.shadowRoot) {
                            const found = findInShadow(el.shadowRoot, depth + 1);
                            if (found) return found;
                        }
                    }
                    return null;
                }
                return findInShadow(document, 0);
            }""", model_name)
            if model_option:
                break
            print(f"      ... waiting for model option '{model_name}' to appear (attempt {poll_attempt+1}/10)...")
            await asyncio.sleep(1)
        
        if model_option:
            print(f"   Found model option: '{model_option['text']}'")
            await self.page.mouse.click(model_option['x'], model_option['y'])
            await asyncio.sleep(1.5)
            print(f"   Model '{model_name}' selected!")
            return True
            
        print(f"   Model '{model_name}' not found in dropdown. Using default.")
        # Close dropdown by clicking elsewhere
        await self.page.mouse.click(10, 10)
        await asyncio.sleep(1)
        return False

    async def _select_video_model(self, model_name: str = "Veo 3.1 - Lite"):
        """Select a video model from the model dropdown in the manual controls popup.
        
        Args:
            model_name: Model name like "Veo 3.1 - Lite", "Veo 3.1 - Fast", etc.
        """
        print(f"\n   Selecting video model: {model_name}...")
        self._find_active_page()
        
        # Find the model dropdown button in the popup (contains arrow_drop_down icon)
        dropdown = await self.page.evaluate("""() => {
            function findInShadow(root, depth) {
                if (depth > 15) return null;
                const all = root.querySelectorAll('*');
                for (const el of all) {
                    const text = (el.textContent || '').trim();
                    const tag = el.tagName;
                    // Model dropdown has model name + arrow_drop_down, and is wide
                    if (tag === 'BUTTON' && text.includes('arrow_drop_down')
                        && (text.includes('Omni') || text.includes('Veo') 
                            || text.includes('Nano') || text.includes('Banana')
                            || text.includes('Flash'))) {
                        const rect = el.getBoundingClientRect();
                        // The popup dropdown has width > 150
                        if (rect.width > 150 && rect.height > 20 && rect.height < 60) {
                            return {x: rect.x + rect.width/2, y: rect.y + rect.height/2,
                                    text: text.substring(0, 50)};
                        }
                    }
                    if (el.shadowRoot) {
                        const found = findInShadow(el.shadowRoot, depth + 1);
                        if (found) return found;
                    }
                }
                return null;
            }
            return findInShadow(document, 0);
        }""")
        
        if not dropdown:
            print(f"   Model dropdown not found via JS. Trying fallback coordinates (763, 560)...")
            dropdown = {'x': 763, 'y': 560, 'text': 'Fallback Dropdown'}
        
        current_model = dropdown.get('text', '')
        # Clean both for robust alphanumeric comparison
        clean_current = "".join([c for c in current_model.lower() if c.isalnum()])
        clean_target = "".join([c for c in model_name.lower() if c.isalnum()])
        
        if clean_target in clean_current and dropdown.get('text') != 'Fallback Dropdown':
            print(f"   Already using model: {current_model}")
            return True
        
        # Click dropdown to open model list
        print(f"   Opening model dropdown (current: '{current_model}')...")
        await self.page.mouse.click(dropdown['x'], dropdown['y'])
        await asyncio.sleep(2)
        
        # Find and click the target model in the dropdown list with a polling loop
        model_option = None
        for poll_attempt in range(10):
            model_option = await self.page.evaluate("""(targetModel) => {
                function findInShadow(root, depth) {
                    if (depth > 15) return null;
                    const all = root.querySelectorAll('*');
                    const cleanTarget = targetModel.toLowerCase().replace(/[^a-z0-9]/g, '');
                    for (const el of all) {
                        const text = (el.textContent || '').trim();
                        const cleanText = text.toLowerCase().replace(/[^a-z0-9]/g, '');
                        if (cleanText.includes(cleanTarget)
                            && !text.includes('arrow_drop_down')) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 50 && rect.height > 15 && rect.height < 60) {
                                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2,
                                        text: text.substring(0, 50)};
                            }
                        }
                        if (el.shadowRoot) {
                            const found = findInShadow(el.shadowRoot, depth + 1);
                            if (found) return found;
                        }
                    }
                    return null;
                }
                return findInShadow(document, 0);
            }""", model_name)
            if model_option:
                break
            print(f"      ... waiting for model option '{model_name}' to appear (attempt {poll_attempt+1}/10)...")
            await asyncio.sleep(1)
        
        if model_option:
            print(f"   Found model option: '{model_option['text']}'")
            await self.page.mouse.click(model_option['x'], model_option['y'])
            await asyncio.sleep(1.5)
            print(f"   Model '{model_name}' selected!")
            return True
        
        print(f"   Model '{model_name}' not found in dropdown. Using default.")
        # Close dropdown by clicking elsewhere
        await self.page.mouse.click(10, 10)
        await asyncio.sleep(1)
        return False

    async def generate_video(
        self,
        prompt: str,
        reference_images: List[str] = None,
        output_prefix: str = "video",
        model: str = "Veo 3.1 - Lite",
        aspect_ratio: str = "16:9",
        page=None
    ) -> List[str]:
        """Generate a video using Google Flow via Playwright UI scraping.
        
        Flow (June 2026) approach:
        1. Create new project
        2. Turn Agent OFF → manual controls appear
        3. Open popup → select Video tab → set ratio → select model
        4. Close popup → type prompt → generate
        5. Wait for video → capture from network/DOM
        
        Args:
            prompt: The video description/motion prompt.
            reference_images: Optional list of image paths for start_image mode.
            output_prefix: Prefix for saved video filenames.
            model: Video model name (e.g., "Omni Flash", "Omni", "Veo 3").
            aspect_ratio: "16:9" or "9:16".
            page: Specific Playwright page to use (or uses self.page).
        
        Returns:
            List of saved video file paths.
        """
        if page: self.page = page
        if not self.page:
            return []

        import time as _time
        output_dir = os.path.join("output", "ugc")
        os.makedirs(output_dir, exist_ok=True)

        # ====== STEP 0: Create new project ======
        await self._create_new_project()

        # ====== STEP 1: Switch to Video mode ======
        print("\n   STEP 1: Switching to Video mode...")
        switched = await self._switch_to_video_mode()
        if not switched:
            print("   WARNING: Failed to switch to Video mode. Attempting generation anyway.")

        # ====== STEP 1.5: Select aspect ratio and model ======
        await self._select_aspect_ratio(aspect_ratio)
        await self._select_video_model(model)
        
        # Close the popup by pressing Escape
        await self.page.keyboard.press("Escape")
        await asyncio.sleep(1)

        # ====== STEP 2: Upload reference images if provided ======
        if reference_images:
            abs_paths = [os.path.abspath(p) for p in reference_images if os.path.exists(p)]
            if abs_paths:
                print(f"\n   STEP 2: Uploading {len(abs_paths)} reference images...")
                try:
                    file_input = self.page.locator("input[type='file']").first
                    await file_input.set_input_files(abs_paths)
                    print("   Reference images uploaded!")
                except Exception as e:
                    print(f"   Upload failed: {e}")

                print("   Waiting 20s for upload to process...")
                await asyncio.sleep(20)
                self._find_active_page()

        # ====== STEP 3: Type prompt ======
        print("\n   STEP 3: Typing video prompt...")
        await asyncio.sleep(3)
        self._find_active_page()

        try:
            found = await self._focus_prompt_box()
        except Exception as e:
            print(f"   Page reference stale, re-acquiring... ({e})")
            self._find_active_page()
            found = await self._focus_prompt_box()

        if found:
            try:
                await asyncio.sleep(0.5)
                await self.page.keyboard.press("Control+a")
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(0.3)
                await self.page.keyboard.type(prompt, delay=10)
                print("   Prompt typed!")
            except Exception as e:
                print(f"   Typing failed ({e}), re-acquiring page...")
                self._find_active_page()
                found2 = await self._focus_prompt_box()
                if found2:
                    await asyncio.sleep(0.3)
                    await self.page.keyboard.type(prompt, delay=10)
                    print("   Prompt typed (retry)!")
        else:
            print("   Could not find prompt box for video.")
            return []

        await asyncio.sleep(2)

        # ====== STEP 4: Generate video ======
        print(f"\n   [{output_prefix}] Pressing Enter to generate video...")
        self.captured_videos[self.page] = [] # Reset
        self.captured_images[self.page] = [] # Reset (may capture thumbnail)
        self.is_generating[self.page] = True
        await self.page.keyboard.press("Enter")

        # ====== STEP 5: Wait for video generation (much longer than images) ======
        print(f"   [{output_prefix}] Generating video (this may take 2-5 minutes)...")
        max_wait = 360 # 6 min max timeout for video
        start_gen = asyncio.get_event_loop().time()

        await asyncio.sleep(10) # Initial wait

        while (asyncio.get_event_loop().time() - start_gen) < max_wait:
            elapsed = int(asyncio.get_event_loop().time() - start_gen)

            # Check if we captured a video already
            if self.captured_videos.get(self.page):
                print(f"   [{output_prefix}] Video captured from network at {elapsed}s!")
                break

            # Check DOM for generation status
            status = await self.page.evaluate("""() => {
                const text = document.body.innerText || '';
                const hasLoading = text.includes('99%') || text.includes('Generating') 
                    || text.includes('Creating') || text.includes('Processing');
                return { hasLoading };
            }""")

            if not status['hasLoading'] and elapsed > 60:
                print(f"   [{output_prefix}] Loading indicators gone at {elapsed}s. Checking for result...")
                # Wait a bit more for the video to load
                await asyncio.sleep(10)
                break

            if elapsed % 30 == 0:
                print(f"   [{output_prefix}] ... {elapsed}s elapsed (still generating)")

            await asyncio.sleep(5)

        self.is_generating[self.page] = False
        await asyncio.sleep(5) # Extra buffer

        # ====== STEP 6: Save results ======
        self._find_active_page()
        print(f"\n   [{output_prefix}] Saving video results...")

        saved = []

        # Priority 1: Use captured video from network interception
        captured_vids = self.captured_videos.get(self.page, [])
        if captured_vids:
            print(f"   [{output_prefix}] Found {len(captured_vids)} captured video(s)")
            for idx, vid in enumerate(captured_vids):
                filepath = os.path.join(output_dir, f"{output_prefix}_{int(_time.time())}_{idx+1}.mp4")
                if vid.get('data'):
                    # Direct binary data
                    with open(filepath, "wb") as f:
                        f.write(vid['data'])
                    print(f"   Saved (Network): {filepath} ({vid['size']//1024}KB)")
                    saved.append(filepath)
                elif vid.get('url'):
                    # Download from URL
                    print(f"   Downloading video from: {vid['url'][:80]}...")
                    try:
                        import httpx
                        async with httpx.AsyncClient() as client:
                            resp = await client.get(vid['url'], timeout=120.0)
                            resp.raise_for_status()
                            with open(filepath, "wb") as f:
                                f.write(resp.content)
                            print(f"   Saved (Downloaded): {filepath} ({len(resp.content)//1024}KB)")
                            saved.append(filepath)
                    except Exception as dl_err:
                        print(f"   Download failed: {dl_err}")

        # Priority 2: Try to find video element in the DOM and extract its src or blob data
        if not saved:
            print("   No videos from network. Trying DOM scraping...")
            try:
                scraped_vids = await self.page.evaluate("""async () => {
                    function findVideos(root, depth = 0) {
                        if (depth > 15) return [];
                        let results = [];
                        const all = root.querySelectorAll('*');
                        for (const el of all) {
                            if (el.tagName === 'VIDEO') {
                                let src = el.src || el.currentSrc || '';
                                if (!src) {
                                    const sources = el.querySelectorAll('source');
                                    for (const s of sources) {
                                        if (s.src) { src = s.src; break; }
                                    }
                                }
                                if (src) {
                                    results.push({
                                        src: src,
                                        width: el.videoWidth || el.clientWidth,
                                        height: el.videoHeight || el.clientHeight
                                    });
                                }
                            }
                            if (el.shadowRoot) {
                                results.push(...findVideos(el.shadowRoot, depth + 1));
                            }
                        }
                        return results;
                    }
                    
                    const vids = findVideos(document);
                    const uniqueVids = [];
                    const seen = new Set();
                    for (const v of vids) {
                        if (!seen.has(v.src)) {
                            seen.add(v.src);
                            uniqueVids.push(v);
                        }
                    }
                    
                    const finalVids = [];
                    for (const v of uniqueVids) {
                        try {
                            const resp = await fetch(v.src);
                            const blob = await resp.blob();
                            const base64 = await new Promise((resolve, reject) => {
                                const reader = new FileReader();
                                reader.onloadend = () => {
                                    const res = reader.result;
                                    if (res) {
                                        resolve(res.split(',')[1]);
                                    } else {
                                        reject(new Error("Empty read"));
                                    }
                                };
                                reader.onerror = () => reject(reader.error);
                                reader.readAsDataURL(blob);
                            });
                            finalVids.push({ src: v.src, type: 'blob', data: base64 });
                        } catch (e) {
                            if (v.src.startsWith('blob:')) {
                                finalVids.push({ src: v.src, type: 'blob_error', error: e.toString() });
                            } else {
                                finalVids.push({ src: v.src, type: 'url' });
                            }
                        }
                    }
                    return finalVids;
                }""")
                
                if scraped_vids:
                    print(f"   Found {len(scraped_vids)} video source(s) in DOM")
                    import base64 as _base64
                    for idx, vid in enumerate(scraped_vids):
                        filepath = os.path.join(output_dir, f"{output_prefix}_{int(_time.time())}_{idx+1}.mp4")
                        if vid.get('type') == 'blob' and vid.get('data'):
                            # Save base64-encoded blob data
                            with open(filepath, "wb") as f:
                                f.write(_base64.b64decode(vid['data']))
                            print(f"   Saved (DOM Blob): {filepath} ({os.path.getsize(filepath)//1024}KB)")
                            saved.append(filepath)
                        elif vid.get('type') == 'url' and vid.get('src'):
                            # Download direct URL
                            print(f"   Downloading: {vid['src'][:80]}...")
                            try:
                                import httpx
                                async with httpx.AsyncClient() as client:
                                    resp = await client.get(vid['src'], timeout=120.0)
                                    resp.raise_for_status()
                                    with open(filepath, "wb") as f:
                                        f.write(resp.content)
                                    print(f"   Saved (DOM URL): {filepath} ({len(resp.content)//1024}KB)")
                                    saved.append(filepath)
                            except Exception as dl_err:
                                print(f"   Download failed: {dl_err}")
                        elif vid.get('type') == 'blob_error':
                            print(f"   [!] Failed to extract blob inside browser: {vid.get('error')}")
            except Exception as e:
                print(f"   DOM video scraping failed: {e}")

        if not saved:
            print(f"   [{output_prefix}] No video captured. Saving page screenshot for debugging.")
            path = os.path.join(output_dir, f"{output_prefix}_debug_screenshot.png")
            await self.page.screenshot(path=path)
            print(f"   Debug screenshot: {path}")

        return saved

    async def close(self):
        print("Closing bridge...")
        if hasattr(self, "browser_session") and self.browser_session:
            await self.browser_session.close()
        elif self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
