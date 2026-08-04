"""
Self-Improvement Engine — The Brain's Ability to Fix & Upgrade Itself
=====================================================================

This module gives the brain TRUE autonomy by letting it:
1. FIX its own broken code using Gemini CLI
2. DISCOVER new free AI tools by researching the web
3. INTEGRATE new tools into its own codebase
4. ADAPT when websites change their UI

Uses Google Gemini CLI (`gemini -p "..."`) for intelligent code editing
and the Gemini API for quick analysis tasks.

Requirements:
    - npm install -g @google/gemini-cli
    - export GEMINI_API_KEY=<your_key>
"""

import os
import sys
import json
import asyncio
import re
import subprocess
import time
from datetime import datetime
from typing import Optional

import httpx


# ==========================================
# CONFIGURATION
# ==========================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
GEMINI_CLI_TIMEOUT = 120  # seconds
MAX_REPAIR_ATTEMPTS = 3

# Files the brain is allowed to edit
EDITABLE_FILES = [
    "tiktok_trend_scraper.py",
    "agent_product_scraper.py",
    "social_autoposter.py",
    "prompt_library.py",
]

# Files the brain should NEVER edit (safety)
PROTECTED_FILES = [
    "agent_brain.py",  # Don't let it rewrite its own thinking
    "agent_memory.py",  # Don't corrupt memory structure
    ".env",             # Don't leak API keys
    "fashion_agency_graph.py", # SOTA Multi-Agent Graph Base
    "agent_tools.py",   # Core Production Logic
    "flow_bridge.py",   # Deprecated Core Logic
    "fashion_brain.py", # Deprecated Core Logic
]


# ==========================================
# GEMINI CLI INTERFACE
# ==========================================
async def call_gemini_cli(prompt: str, working_dir: str = None) -> dict:
    """
    Call Gemini CLI in non-interactive (headless) mode.
    
    Usage: gemini -p "your prompt here"
    
    The CLI reads files in the working directory, understands context,
    and can edit code directly.
    
    Returns: {"success": bool, "output": str, "error": str}
    """
    if working_dir is None:
        working_dir = PROJECT_DIR

    env = os.environ.copy()
    # Ensure GEMINI_API_KEY is set
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_DIR, ".env"))
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        env["GEMINI_API_KEY"] = api_key

    try:
        # Run gemini CLI in headless mode
        proc = await asyncio.create_subprocess_exec(
            "gemini", "-p", prompt,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), 
            timeout=GEMINI_CLI_TIMEOUT
        )
        
        output = stdout.decode("utf-8", errors="replace").strip()
        error = stderr.decode("utf-8", errors="replace").strip()
        
        return {
            "success": proc.returncode == 0,
            "output": output,
            "error": error,
            "exit_code": proc.returncode,
        }
    except asyncio.TimeoutError:
        return {
            "success": False,
            "output": "",
            "error": f"Gemini CLI timed out after {GEMINI_CLI_TIMEOUT}s",
            "exit_code": -1,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "Gemini CLI not installed. Run: npm install -g @google/gemini-cli",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "exit_code": -1,
        }


# ==========================================
# GEMINI API FALLBACK (when CLI is not available)
# ==========================================
async def call_gemini_api(prompt: str, client: httpx.AsyncClient = None) -> dict:
    """
    Fallback: Use Gemini API directly for code analysis and fixes.
    Works even without Gemini CLI installed.
    """
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_DIR, ".env"))
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return {"success": False, "output": "", "error": "No GEMINI_API_KEY"}

    own_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=60.0)
        own_client = True

    try:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4000},
            },
        )
        
        if resp.status_code == 200:
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"success": True, "output": text, "error": ""}
        else:
            return {"success": False, "output": "", "error": f"API error {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}
    finally:
        if own_client:
            await client.aclose()


# ==========================================
# SELF-REPAIR: Fix broken code
# ==========================================
async def repair_tool(tool_name: str, error_msg: str, source_file: str = None, 
                      client: httpx.AsyncClient = None) -> dict:
    """
    Attempt to fix a broken tool by:
    1. Reading the source code
    2. Sending error + code to Gemini (CLI or API)
    3. Applying the fix
    4. Backing up the original
    
    Returns: {"success": bool, "diagnosis": str, "file_changed": str}
    """
    # Map tool names to source files
    if source_file is None:
        source_map = {
            "generate_model_sheet": "flow_bridge.py",
            "generate_ad": "flow_bridge.py",
            "scrape_trending": "tiktok_trend_scraper.py",
            "scrape_agents": "agent_product_scraper.py",
            "research_web": "agent_tools.py",
            "use_free_ai_generator": "agent_tools.py",
            "auto_post": "social_autoposter.py",
        }
        source_file = source_map.get(tool_name, "agent_tools.py")

    if source_file in PROTECTED_FILES:
        return {"success": False, "diagnosis": f"{source_file} is protected", "file_changed": ""}

    source_path = os.path.join(PROJECT_DIR, source_file)
    if not os.path.exists(source_path):
        return {"success": False, "diagnosis": f"{source_file} not found", "file_changed": ""}

    # Read source
    with open(source_path, "r") as f:
        source_code = f.read()

    # Truncate if too long
    if len(source_code) > 12000:
        source_code = source_code[:12000] + "\n... (truncated)"

    # Build prompt for repair
    repair_prompt = f"""I have a Python tool called '{tool_name}' in file '{source_file}' that is failing.

ERROR MESSAGE:
{error_msg}

SOURCE CODE ({source_file}):
```python
{source_code}
```

Please analyze the error and provide a fix. Output ONLY a JSON object like this:
{{
    "diagnosis": "one line explaining what's wrong",
    "find": "exact code to find (copy from the source above)",
    "replace": "the fixed code to replace it with"
}}

Rules:
- The "find" must exactly match text in the source file
- Minimal fix only — don't rewrite everything
- If it's a Playwright selector issue, update selectors for modern web UIs
- If it's a timeout, increase the timeout value
- If it's a missing library/import, add the import"""

    # Classify error type — don't try to fix code when it's a login/cookie issue
    login_keywords = ["cookie", "login", "auth", "session", "sign in", "403", "401", "not logged"]
    # Compile a regex with word boundaries at the start to prevent matching inside unrelated words,
    # but allowing it as a prefix (e.g., catching 'authentication' with 'auth')
    sorted_keywords = sorted(login_keywords, key=len, reverse=True)
    pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted_keywords)) + r')', re.IGNORECASE)

    if pattern.search(error_msg):
        return {
            "success": False,
            "diagnosis": f"Not a code bug — {tool_name} needs login/cookies. Upload cookies to fix.",
            "file_changed": "",
        }

    # Go straight to Gemini API (CLI always times out on headless VMs)
    print(f"🔧 Attempting repair of {tool_name} in {source_file}...")

    api_result = await call_gemini_api(repair_prompt, client)
    
    if not api_result["success"]:
        return {"success": False, "diagnosis": f"Both CLI and API failed: {api_result['error']}", "file_changed": ""}

    # Parse the JSON fix from Gemini API
    try:
        # Extract JSON from response (may have markdown wrapping)
        text = api_result["output"]
        # Find JSON block
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        fix = json.loads(text.strip())
        diagnosis = fix.get("diagnosis", "Unknown")
        find_block = fix.get("find", "")
        replace_block = fix.get("replace", "")
        
        if not find_block or not replace_block:
            return {"success": False, "diagnosis": f"Incomplete fix: {diagnosis}", "file_changed": ""}

        # Apply the fix
        with open(source_path, "r") as f:
            current_code = f.read()

        if find_block not in current_code:
            return {"success": False, "diagnosis": f"FIND block not in source: {diagnosis}", "file_changed": ""}

        # Backup
        backup_path = source_path + f".bak.{int(time.time())}"
        with open(backup_path, "w") as f:
            f.write(current_code)

        # Patch
        patched = current_code.replace(find_block, replace_block, 1)
        with open(source_path, "w") as f:
            f.write(patched)

        print(f"✅ Patched {source_file}: {diagnosis}")
        print(f"   Backup: {backup_path}")

        # Reload module
        try:
            import importlib
            module_name = source_file.replace(".py", "")
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                print(f"   🔄 Reloaded {module_name}")
        except Exception as e:
            print(f"   ⚠️  Could not reload: {e}")

        return {
            "success": True,
            "diagnosis": diagnosis,
            "file_changed": source_file,
        }
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        return {
            "success": False, 
            "diagnosis": f"Could not parse Gemini fix: {e}. Raw: {api_result['output'][:300]}",
            "file_changed": "",
        }


# ==========================================
# DISCOVER: Find new free AI tools online
# ==========================================
async def discover_free_tools(client: httpx.AsyncClient = None) -> dict:
    """
    Search the web for new free AI image/video generation tools.
    Returns a list of discovered tools with URLs and descriptions.
    """
    search_prompt = """Search your knowledge for the LATEST free AI image generation tools 
    available in 2025-2026 that work WITHOUT login or API keys. 
    I need tools I can automate with Playwright browser automation.
    
    For each tool, provide:
    1. Name
    2. URL
    3. What it generates (images/video/text)
    4. Whether it needs login
    5. How to automate it (what HTML elements to target)
    
    Focus on:
    - Free, no signup required
    - High quality photorealistic output
    - Can be used via browser automation
    - Active and working in 2026
    
    Return as a JSON array."""

    result = await call_gemini_api(search_prompt, client)
    if not result["success"]:
        return {"success": False, "tools": [], "error": result["error"]}

    try:
        text = result["output"]
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        tools = json.loads(text.strip())
        return {"success": True, "tools": tools, "count": len(tools)}
    except:
        return {"success": True, "tools": [], "raw_response": result["output"][:1000]}


# ==========================================
# INTEGRATE: Add discovered tools to codebase
# ==========================================

# URLs that should NEVER be used for tool generation
BLOCKED_URLS = [
    "example.com", "placeholder", "localhost", "127.0.0.1",
    "test.com", "foo.com", "bar.com", "httpbin.org",
]

# Max number of auto-generated tools allowed (prevents bloat)
MAX_AUTO_TOOLS = 5

def _validate_tool_url(url: str) -> bool:
    """Check if a URL is real and not a placeholder."""
    if not url or len(url) < 10:
        return False
    for blocked in BLOCKED_URLS:
        if blocked in url.lower():
            return False
    if not url.startswith("https://"):
        return False
    return True

def _count_auto_tools() -> int:
    """Count how many auto-generated tools exist in agent_tools.py."""
    tools_path = os.path.join(PROJECT_DIR, "agent_tools.py")
    try:
        with open(tools_path, "r") as f:
            return f.read().count("# AUTO-GENERATED:")
    except:
        return 0

async def integrate_new_tool(tool_info: dict, client: httpx.AsyncClient = None) -> dict:
    """
    Given info about a new AI tool, generate Playwright automation code
    and add it to agent_tools.py.
    
    Args:
        tool_info: {"name": "...", "url": "...", "type": "image", "selectors": {...}}
    """
    tool_name = tool_info.get("name", "unknown").lower().replace(" ", "_")
    tool_url = tool_info.get("url", "")
    
    if not tool_url:
        return {"success": False, "error": "No URL provided"}

    # ── GUARDRAIL: Validate URL ──
    if not _validate_tool_url(tool_url):
        return {"success": False, "error": f"URL blocked/invalid: {tool_url}"}
    
    # ── GUARDRAIL: Limit auto-generated tools ──
    if _count_auto_tools() >= MAX_AUTO_TOOLS:
        return {"success": False, "error": f"Max {MAX_AUTO_TOOLS} auto-tools reached. Remove old ones first."}

    # First try Gemini CLI (it can read the existing code and add to it)
    cli_result = await call_gemini_cli(
        f"Read agent_tools.py and add a new tool function called 'tool_{tool_name}' "
        f"that automates the website at {tool_url} using Playwright to generate AI images. "
        f"Also add it to the execute_tool dispatcher at the bottom. "
        f"The function should: navigate to the URL, find the prompt input, enter the prompt, "
        f"click generate, wait for results, and download the images. "
        f"Follow the same pattern as the existing tool_use_free_ai function."
    )
    
    if cli_result["success"]:
        return {
            "success": True,
            "tool_name": tool_name,
            "file_changed": "agent_tools.py",
            "output": cli_result["output"][:500],
        }

    # Fallback: generate the code via API and append it
    generate_prompt = f"""Generate a Python async function for Playwright browser automation.
    
Tool name: tool_{tool_name}
Website URL: {tool_url}
Purpose: Generate AI images from text prompts

Follow this exact pattern:
```python
async def tool_{tool_name}(prompt: str, output_name: str = "generated", memory=None) -> dict:
    \"\"\"Generate images using {tool_info.get('name', tool_name)}.\"\"\"
    try:
        from playwright.async_api import async_playwright
        output_dir = os.path.join(os.getcwd(), "output", "free_ai")
        os.makedirs(output_dir, exist_ok=True)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("{tool_url}", timeout=30000)
            await asyncio.sleep(5)
            
            # Find and fill prompt input
            textarea = page.locator("textarea").or_(page.locator("input[type='text']")).first
            await textarea.fill(prompt)
            
            # Click generate
            gen_btn = page.locator("button:has-text('Generate')").or_(page.locator("button:has-text('Create')")).first
            await gen_btn.click()
            await asyncio.sleep(30)
            
            # Download results
            images = page.locator("img[src*='blob:']").or_(page.locator("img[src*='generated']"))
            saved = []
            for i in range(await images.count()):
                path = os.path.join(output_dir, f"{{output_name}}_{{i}}.png")
                await images.nth(i).screenshot(path=path)
                saved.append(path)
            
            await browser.close()
        
        if memory:
            memory.log_action("{tool_name}", f"Generated {{len(saved)}} images")
        return {{"success": True, "images": saved, "count": len(saved)}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}
```

Return ONLY the Python function code, nothing else."""

    api_result = await call_gemini_api(generate_prompt, client)
    if not api_result["success"]:
        return {"success": False, "error": f"Could not generate code: {api_result['error']}"}

    # Extract code and append to agent_tools.py
    code = api_result["output"]
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0]
    elif "```" in code:
        code = code.split("```")[1].split("```")[0]

    tools_path = os.path.join(PROJECT_DIR, "agent_tools.py")
    try:
        with open(tools_path, "r") as f:
            current = f.read()

        # Add before the TOOL DISPATCHER section
        insertion_point = "# TOOL DISPATCHER"
        if insertion_point in current:
            new_code = current.replace(
                f"# {insertion_point[2:]}",
                f"\n# AUTO-GENERATED: {tool_name} ({datetime.now().isoformat()})\n{code}\n\n# {insertion_point[2:]}"
            )
            with open(tools_path, "w") as f:
                f.write(new_code)
            
            print(f"✅ Added tool_{tool_name} to agent_tools.py")
            return {
                "success": True,
                "tool_name": tool_name,
                "file_changed": "agent_tools.py",
            }
        else:
            return {"success": False, "error": "Could not find insertion point in agent_tools.py"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==========================================
# UPGRADE: Full self-improvement cycle
# ==========================================
async def run_improvement_cycle(memory=None, client: httpx.AsyncClient = None) -> dict:
    """
    Full self-improvement cycle:
    1. Check what's broken (from memory/learnings)
    2. Try to repair broken tools
    3. Discover new free AI tools
    4. Integrate the best ones
    5. Return a summary of improvements
    """
    improvements = []
    
    # Step 1: Check for broken tools from memory
    broken_tools = []
    if memory:
        for learning in memory.data.get("learnings", []):
            text = learning.get("text", "")
            if "broken" in text.lower() or "blocked" in text.lower() or "failed" in text.lower():
                # Extract tool name
                for tname in ["generate_model_sheet", "generate_ad", "research_web", "scrape_trending"]:
                    if tname in text:
                        broken_tools.append((tname, text))
                        break

    # Step 2: Repair broken tools
    for tool_name, error in broken_tools[:3]:
        print(f"\n🔧 Repairing: {tool_name}")
        result = await repair_tool(tool_name, error, client=client)
        if result["success"]:
            improvements.append(f"Fixed {tool_name}: {result['diagnosis']}")
        else:
            improvements.append(f"Could not fix {tool_name}: {result['diagnosis']}")

    # Step 3: Discover new tools
    print("\n🔍 Discovering new free AI tools...")
    discover_result = await discover_free_tools(client)
    if discover_result.get("tools"):
        print(f"   Found {len(discover_result['tools'])} tools")
        for tool in discover_result["tools"][:2]:
            name = tool.get("name", "unknown")
            needs_login = tool.get("needs_login", True)
            if not needs_login:
                print(f"   🆕 Integrating: {name}")
                integrate_result = await integrate_new_tool(tool, client)
                if integrate_result["success"]:
                    improvements.append(f"Added new tool: {name}")

    return {
        "success": True,
        "improvements": improvements,
        "repairs_attempted": len(broken_tools),
        "tools_discovered": len(discover_result.get("tools", [])),
    }


# ==========================================
# INSTALL GEMINI CLI (one-time setup)
# ==========================================
async def install_gemini_cli() -> dict:
    """Install Gemini CLI on the system."""
    try:
        # Check if already installed
        proc = await asyncio.create_subprocess_exec(
            "gemini", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        if proc.returncode == 0:
            return {"success": True, "status": "already_installed", "version": stdout.decode().strip()}
    except:
        pass

    # Check if npm is available
    try:
        proc = await asyncio.create_subprocess_exec(
            "npm", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        if proc.returncode != 0:
            return {"success": False, "error": "npm not installed. Install Node.js first: sudo apt install nodejs npm"}
    except:
        return {"success": False, "error": "npm not found. Install Node.js first: sudo apt install nodejs npm"}

    # Install Gemini CLI
    print("📦 Installing Gemini CLI...")
    proc = await asyncio.create_subprocess_exec(
        "npm", "install", "-g", "@google/gemini-cli",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    
    if proc.returncode == 0:
        print("✅ Gemini CLI installed")
        return {"success": True, "status": "installed"}
    else:
        return {"success": False, "error": f"Install failed: {stderr.decode()[:200]}"}
