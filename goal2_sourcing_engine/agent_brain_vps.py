"""
Agent Brain — The Autonomous AI Money-Making Machine
====================================================
The central intelligence that runs on the VPS 24/7.

Uses Groq API (free tier, Llama 3.3 70B) as the thinking engine.
Has access to all tools via function calling.
Maintains persistent memory of what it's done and learned.

The brain follows a simple loop:
  1. Load state from memory
  2. Ask the LLM: "Given your goal and state, what should you do next?"
  3. Execute the chosen tool
  4. Reflect on the result
  5. Save learnings to memory
  6. Repeat

Usage:
  python agent_brain.py                    # Run autonomously
  python agent_brain.py --dry-run          # Plan without executing
  python agent_brain.py --task "create model sheets"  # Specific task
  python agent_brain.py --run-hours 2      # Run for 2 hours then stop
  python agent_brain.py --status           # Show current state
"""
import os
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Optional

import httpx
from dotenv import load_dotenv

from mem0_memory import Mem0Memory as AgentMemory
from agent_tools import TOOL_DEFINITIONS, execute_tool
from fashion_brain import get_category_knowledge, suggest_ad_format
# self_improve DISABLED — was corrupting source files
# from self_improve import repair_tool, discover_free_tools, run_improvement_cycle, install_gemini_cli

load_dotenv()

# Track consecutive failures per tool for self-repair trigger
_tool_failure_count = {}
# Tools blocked due to repeated failures (tool_name -> reason)
_blocked_tools = {}

# Google Flow rate limit protection — balanced (account is working)
_flow_last_call_time = 0       # timestamp of last Flow call
_flow_call_count = 0           # total Flow calls this session
_flow_cooldown_seconds = 600   # 10 minutes between Flow calls (production safe spacing)
_flow_max_per_session = 20     # max 20 Flow calls per session
_flow_failure_penalty = 300    # 5 minutes after a Flow failure

# ==========================================
# CONFIGURATION
# ==========================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# All 7 Gemini keys — each model slot gets its own key to maximise daily quota
_GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
    os.getenv("GEMINI_API_KEY_6"),
    os.getenv("GEMINI_API_KEY_7"),
]
# Filter out any missing keys
_GEMINI_KEYS = [k for k in _GEMINI_KEYS if k]

# Model cascade — tries each in order until one works
# Spread across MAXIMUM providers so we NEVER run out
LLM_CASCADE = [
    # ── Provider 1: OpenRouter (FREE models) ──
    {
        "name": "openrouter-gemini-flash",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "google/gemini-2.5-flash-preview:free",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 1024,
    },
    {
        "name": "openrouter-llama70b",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 1024,
    },
    # ── Provider 2: Groq (3 models, each with separate limits) ──
    {
        "name": "groq-llama70b",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "key_env": "GROQ_API_KEY",
        "max_tokens": 1024,
    },
    {
        "name": "groq-llama8b",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.1-8b-instant",
        "key_env": "GROQ_API_KEY",
        "max_tokens": 512,  # Smaller to avoid 413 on this model
    },
    # ── Provider 2: Google Gemini — 7 keys × 3 models = 21 independent slots ──
    # Each entry uses a DIFFERENT API key so rate limits are independent
    {
        "name": "gemini-25-flash-lite-k1",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash-lite",
        "key_env": "GEMINI_API_KEY",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-25-flash-k2",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash",
        "key_env": "GEMINI_API_KEY_2",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-25-flash-lite-k3",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash-lite",
        "key_env": "GEMINI_API_KEY_3",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-25-flash-k4",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash",
        "key_env": "GEMINI_API_KEY_4",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-25-flash-lite-k5",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash-lite",
        "key_env": "GEMINI_API_KEY_5",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-25-flash-k6",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash",
        "key_env": "GEMINI_API_KEY_6",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-25-pro-k7",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-pro",
        "key_env": "GEMINI_API_KEY_7",
        "max_tokens": 1024,
    },
    # ── Provider 3: xAI Grok ──
    {
        "name": "xai-grok",
        "url": "https://api.x.ai/v1/chat/completions",
        "model": "grok-3-mini",
        "key_env": "XAI_API_KEY",
        "max_tokens": 1024,
    },
    # ── Provider 4: NVIDIA NIM (FREE endpoints, 40 RPM, OpenAI compatible) ──
    # mistral-nemotron: BUILT for agentic workflows + function calling
    {
        "name": "nvidia-mistral-nemotron",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "mistralai/mistral-nemotron",
        "key_env": "NVIDIA_API_KEY",
        "max_tokens": 1024,
    },
    # deepseek-v3.1-terminus: REMOVED — returned 404, model unavailable on NVIDIA NIM
    # mistral-large: state-of-the-art general purpose
    {
        "name": "nvidia-mistral-large",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "mistralai/mistral-large-3-675b-instruct-2512",
        "key_env": "NVIDIA_API_KEY",
        "max_tokens": 1024,
    },
    # llama-4-maverick: Meta's latest
    {
        "name": "nvidia-llama4-maverick",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "meta/llama-4-maverick-17b-128e-instruct",
        "key_env": "NVIDIA_API_KEY",
        "max_tokens": 1024,
    },
    # deepseek-v3.2: 685B reasoning powerhouse
    {
        "name": "nvidia-deepseek-v32",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "deepseek-ai/deepseek-v3.2",
        "key_env": "NVIDIA_API_KEY",
        "max_tokens": 1024,
    },
    # qwen3-coder: agentic coding specialist
    {
        "name": "nvidia-qwen3-coder",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "qwen/qwen3-coder-480b-a35b-instruct",
        "key_env": "NVIDIA_API_KEY",
        "max_tokens": 1024,
    },

    # ── Provider 6: Cerebras (if key provided) ──
    {
        "name": "cerebras-llama",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "model": "llama-3.3-70b",
        "key_env": "CEREBRAS_API_KEY",
        "max_tokens": 1024,
    },
    # ── Provider 7: SambaNova (if key provided) ──
    {
        "name": "sambanova-llama",
        "url": "https://api.sambanova.ai/v1/chat/completions",
        "model": "Meta-Llama-3.3-70B-Instruct",
        "key_env": "SAMBANOVA_API_KEY",
        "max_tokens": 1024,
    },
]

MAX_ACTIONS_PER_SESSION = 50   # Reduced — quality over quantity
THINK_INTERVAL_SECONDS = 300   # Slowed down to save API quota

# Rate limit backoff tracking
_rate_limit_backoff = {}  # model_name -> (next_retry_time, backoff_seconds)


SYSTEM_PROMPT = """You are an autonomous AI fashion content production agent running 24/7.

MODE: FULLY AUTONOMOUS PRODUCTION — Never wait for human approval. Keep working.

=== YOUR MISSION ===
Run the lookbook generation pipeline non-stop:
1. MONITOR input_sourcing/ for new imported product details and staged images (automatically scraped and populated from user drops on Discord).
2. GENERATE high-end editorial fashion lookbook images (4-shot campaigns per product) using the dynamic VTON presets.
3. RESEARCH competitor ad creatives (Meta Ad Library) and trends (TikTok) to keep marketing copy fresh.
4. PREPARE premium captions, style tags, and carousels for each completed product.

=== WORKFLOW PRIORITY ===

1. DETECT AND VALIDATE PRODUCTS IN WAREHOUSE
   - Check if any new product directories have been populated in input_sourcing/.
   - Each staged product must have product images and a metadata.json.

2. GENERATE AD CAMPAIGNS for any products already in input_sourcing/
   - Use generate_ad_image for each product.
   - Each product gets 4 high-end shots: editorial, lifestyle, flat lay, ghost mannequin.
   - If product_image_path is unknown, the system auto-picks one.

3. RESEARCH BETWEEN GENERATIONS
   - scrape_meta_ad_library → find winning hooks and creative formats.
   - research_web → trending streetwear aesthetics and colorways.

4. PREPARE CONTENT
   - generate_caption for each completed image set.
   - Build carousel-ready packages.

=== KEY RULES ===
- Call ONE tool per response.
- NEVER stop and wait — always take the next useful action.
- Sourcing replicas, replica platforms, and Yupoo links are completely DEACTIVATED. Do not attempt to scrape them.
- Focus strictly on unbranded streetwear basics and legitimate Chinese designer blanks.
"""


# ==========================================
# THE BRAIN
# ==========================================
class AgentBrain:
    """The autonomous thinking engine."""

    def __init__(self, dry_run: bool = False):
        self.memory = AgentMemory()
        self.dry_run = dry_run
        self.actions_taken = 0
        self.session_start = datetime.now()
        self.client = httpx.AsyncClient(timeout=30.0)  # 30s per LLM call (was 120)

    async def think(self, extra_context: str = "") -> Optional[dict]:
        """
        Ask the LLM to decide the next action based on current state.
        Includes failure memory so it doesn't repeat broken tools.
        Returns the tool call decision.
        """
        global _blocked_tools, _tool_failure_count
        state_summary = self.memory.get_state_summary()

        # Auto-unblock tools after 10-minute cooldown
        now = time.time()
        expired = [t for t, info in _blocked_tools.items()
                   if isinstance(info, dict) and now - info.get("blocked_at", 0) > 600]
        for t in expired:
            print(f"   🔓 Auto-unblocked: {t} (cooldown expired)")
            _blocked_tools.pop(t)
            _tool_failure_count.pop(t, None)  # Reset failure count too

        # Build failure context so the LLM knows what's broken
        failure_context = ""
        if _blocked_tools:
            blocked_list = "\n".join([
                f"  - {t}: {info['reason'] if isinstance(info, dict) else info}"
                for t, info in _blocked_tools.items()
            ])
            failure_context += f"\n⚠️ TEMPORARILY BLOCKED TOOLS (will auto-retry soon):\n{blocked_list}\n"
        if _tool_failure_count:
            failing = {t: c for t, c in _tool_failure_count.items() if c > 0}
            if failing:
                fail_list = "\n".join([f"  - {t}: failed {c} times" for t, c in failing.items()])
                failure_context += f"\n⚠️ RECENTLY FAILED TOOLS:\n{fail_list}\n"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""Here is your current state:

{state_summary}
{failure_context}
{f'Additional context: {extra_context}' if extra_context else ''}

Decide your next action. Call exactly ONE tool. Think about:
- What's the highest-impact thing to do right now?
- Am I within daily limits?
- What have I learned that should change my approach?

IMPORTANT:
- generate_model_sheet uses FlowBridge (Google AI Studio). TRY IT FIRST for model sheets.
- If it fails, try use_free_ai_generator or generate_with_huggingface as alternatives.
- You can also create_digital_product, scrape_meta_ad_library, or research_web.
- ALWAYS try something DIFFERENT from your last failed action.
"""}
        ]

        # Filter out blocked tools from TOOL_DEFINITIONS
        active_tools = [t for t in TOOL_DEFINITIONS 
                        if t["function"]["name"] not in _blocked_tools]

        response = await self._call_llm(messages, tools=active_tools)

        if response and response.get("tool_calls"):
            tool_call = response["tool_calls"][0]
            tool_name = tool_call["function"]["name"]
            
            # Double-check: reject if tool is blocked
            if tool_name in _blocked_tools:
                print(f"   🚫 LLM tried blocked tool {tool_name}, skipping")
                return None
                
            return {
                "tool_name": tool_name,
                "arguments": json.loads(tool_call["function"]["arguments"]),
                "reasoning": response.get("content", ""),
            }
        elif response and response.get("content"):
            print(f"\n💭 Brain thinking: {response['content'][:200]}")
            return None

        return None

    async def _call_llm(self, messages: list, tools: list = None) -> Optional[dict]:
        """Call LLM with cascading fallback across 5 models and 3 providers."""
        if tools is None:
            tools = TOOL_DEFINITIONS
        global _rate_limit_backoff
        now = time.time()

        for provider in LLM_CASCADE:
            name = provider["name"]
            api_key = os.getenv(provider["key_env"])
            if not api_key:
                continue

            # Check if this model is in backoff
            if name in _rate_limit_backoff:
                next_retry, backoff = _rate_limit_backoff[name]
                if now < next_retry:
                    remaining = int(next_retry - now)
                    print(f"   ⏸️  {name}: rate limited, skip (retry in {remaining}s)")
                    continue

            try:
                headers = {
                    "Content-Type": "application/json",
                }
                # ALL providers use Bearer auth (including Gemini OpenAI-compatible endpoint)
                url = provider["url"]
                headers["Authorization"] = f"Bearer {api_key}"

                resp = await self.client.post(
                    url,
                    headers=headers,
                    json={
                        "model": provider["model"],
                        "messages": messages,
                        "tools": tools,
                        "tool_choice": "auto",
                        "temperature": 0.7,
                        "max_tokens": provider["max_tokens"],
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    choice = data["choices"][0]["message"]
                    # Clear backoff on success
                    _rate_limit_backoff.pop(name, None)
                    print(f"   ✅ Using {name} ({provider['model']})")
                    
                    tool_calls = choice.get("tool_calls", [])
                    content = choice.get("content", "")
                    
                    # If no tool_calls but content has JSON, try to extract tool call
                    if not tool_calls and content:
                        extracted = self._extract_tool_from_text(content)
                        if extracted:
                            tool_calls = extracted
                    
                    return {
                        "content": content,
                        "tool_calls": tool_calls,
                    }
                elif resp.status_code == 429:
                    # Rate limited — exponential backoff
                    old_backoff = _rate_limit_backoff.get(name, (0, 30))[1]
                    new_backoff = min(old_backoff * 2, 3600)  # Max 1 hour
                    _rate_limit_backoff[name] = (now + new_backoff, new_backoff)
                    print(f"   ⚠️  {name}: rate limited, backing off {new_backoff}s")
                elif resp.status_code == 403:
                    # Auth error — disable for this session
                    _rate_limit_backoff[name] = (now + 86400, 86400)  # Skip for 24h
                    print(f"   ❌ {name}: auth failed, disabled for 24h")
                elif resp.status_code == 413:
                    # Request too large for this model — skip for 6 hours
                    _rate_limit_backoff[name] = (now + 21600, 21600)
                    print(f"   ⚠️  {name}: request too large, skipped for 6h")
                else:
                    print(f"   ⚠️  {name}: error {resp.status_code}: {resp.text[:150]}")
            except Exception as e:
                print(f"   ⚠️  {name}: exception: {str(e)[:100]}")

        # ALL providers failed
        print("❌ All LLM providers exhausted")
        wait = min(60, 15 * (1 + len([k for k, v in _rate_limit_backoff.items() if now < v[0]])))
        print(f"   💤 Waiting {wait}s before retrying...")
        await asyncio.sleep(wait)
        return None

    def _extract_tool_from_text(self, text: str) -> list:
        """
        Extract tool calls from LLM text output when models don't use proper tool_calls.
        Handles patterns like:
        - function_name({"key": "value"})
        - {"name": "function_name", "arguments": {...}}
        - ```json\n{"name": "...", ...}\n```
        """
        import re
        
        # Get valid tool names
        valid_tools = {t["function"]["name"] for t in TOOL_DEFINITIONS}
        
        # Pattern 1: tool_name({"arg": "val"}) — most common in NVIDIA models
        for tool_name in valid_tools:
            pattern = rf'{tool_name}\s*\(\s*(\{{.*?\}})\s*\)'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    args = json.loads(match.group(1))
                    print(f"   🔧 Extracted tool call from text: {tool_name}")
                    return [{
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(args),
                        }
                    }]
                except:
                    continue
        
        # Pattern 2: JSON object with "name" field
        json_blocks = re.findall(r'\{[^{}]*"name"\s*:\s*"(\w+)"[^{}]*"arguments"\s*:\s*(\{[^{}]*\})[^{}]*\}', text, re.DOTALL)
        for name, args_str in json_blocks:
            if name in valid_tools:
                try:
                    args = json.loads(args_str)
                    print(f"   🔧 Extracted JSON tool call: {name}")
                    return [{
                        "function": {
                            "name": name,
                            "arguments": json.dumps(args),
                        }
                    }]
                except:
                    continue
        
        # Pattern 3: Look for any tool name followed by a JSON block
        for tool_name in valid_tools:
            pattern = rf'{tool_name}.*?(\{{[^{{}}]*\}})'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    args = json.loads(match.group(1))
                    # Only accept if it's a dictionary
                    if isinstance(args, dict):
                        print(f"   🔧 Extracted nearby tool call: {tool_name}")
                        return [{
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(args),
                            }
                        }]
                except:
                    continue
        
        return []

    async def act(self, decision: dict) -> dict:
        """Execute the brain's decision with Google Flow rate limiting."""
        global _flow_last_call_time, _flow_call_count
        tool_name = decision["tool_name"]
        arguments = decision["arguments"]

        if self.dry_run:
            print(f"\n🏜️  [DRY RUN] Would execute: {tool_name}")
            print(f"   Arguments: {json.dumps(arguments, indent=2)[:300]}")
            return {"success": True, "dry_run": True}

        # Google Flow rate limiting for generate_model_sheet and generate_ad_image
        flow_tools = {"generate_model_sheet", "generate_ad_image"}
        if tool_name in flow_tools:
            now = time.time()
            
            # Check if we've hit the max Flow calls for this session
            if _flow_call_count >= _flow_max_per_session:
                print(f"   🛑 Google Flow limit reached ({_flow_call_count}/{_flow_max_per_session})")
                print(f"   → Switching to non-Flow tasks for this session")
                _blocked_tools[tool_name] = {
                    "reason": f"Flow limit reached ({_flow_call_count})",
                    "blocked_at": now,
                    "unblock_at": now + 99999,  # Block for rest of session
                }
                return {"success": False, "error": "Flow session limit reached — do other tasks"}
            
            # Check cooldown since last Flow call
            time_since_last = now - _flow_last_call_time
            if time_since_last < _flow_cooldown_seconds:
                wait_time = int(_flow_cooldown_seconds - time_since_last)
                print(f"   ⏸️  Google Flow cooldown: {wait_time}s remaining")
                print(f"   → Waiting to prevent rate limit...")
                await asyncio.sleep(wait_time)
            
            _flow_last_call_time = time.time()
            _flow_call_count += 1
            print(f"   🎨 Flow call {_flow_call_count}/{_flow_max_per_session}")

        result = await execute_tool(tool_name, arguments, self.memory)
        self.actions_taken += 1
        
        # If a Flow call failed, add extra penalty cooldown
        if tool_name in flow_tools and not result.get("success", False):
            _flow_last_call_time = time.time() + _flow_failure_penalty - _flow_cooldown_seconds
            print(f"   ⏸️  Flow failure → 10 minute cooldown before next attempt")
        
        return result

    async def reflect(self, decision: dict, result: dict):
        """Learn from the action's result. Trigger self-repair on repeated failures."""
        global _tool_failure_count
        tool_name = decision["tool_name"]
        success = result.get("success", False)

        if success:
            print(f"   ✅ {tool_name} succeeded")
            _tool_failure_count[tool_name] = 0  # Reset failure counter
        else:
            error = result.get("error", "Unknown error")
            print(f"   ❌ {tool_name} failed: {error}")

            # Track failures
            _tool_failure_count[tool_name] = _tool_failure_count.get(tool_name, 0) + 1
            failures = _tool_failure_count[tool_name]

            # Auto-learn from failures
            if "not found" in error.lower():
                self.memory.add_learning(f"{tool_name} failed because a required resource was missing: {error}")
            elif "timeout" in error.lower():
                self.memory.add_learning(f"{tool_name} timed out — might need more wait time or the service is down")
            elif "limit" in error.lower():
                self.memory.add_learning(f"{tool_name} hit a rate limit — need to slow down")

            # BLOCK tool after 10 consecutive failures — but only temporarily
            # Tools auto-unblock after 10 minutes (600s) to allow retries
            if failures >= 10:
                import time as _t
                _blocked_tools[tool_name] = {
                    "reason": f"Failed {failures} times: {error[:100]}",
                    "blocked_at": _t.time(),
                }
                print(f"   🚫 TEMP BLOCKED: {tool_name} — will auto-retry in 10 minutes")
                # DO NOT add to persistent learnings — this is temporary

            # Log the failure
            if failures == 5:
                print(f"   ⚠️ {tool_name} failed {failures}x — consider alternatives")

    async def run(self, max_hours: float = 24, specific_task: str = ""):
        """
        Main autonomous loop.

        Args:
            max_hours: Maximum hours to run before stopping
            specific_task: If provided, focus on this specific task
        """
        max_time = max_hours * 3600
        start = time.time()

        print("\n" + "=" * 60)
        print(f"  [BRAIN] AGENT BRAIN v1.0 - {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"  🎯 Goal: Make money with AI fashion & sneaker ads")
        print(f"  ⏱️  Max runtime: {max_hours}h")
        print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)

        # Reset daily counters if new day
        last_active = self.memory.data.get("last_active", "")
        if not last_active.startswith(datetime.now().strftime("%Y-%m-%d")):
            self.memory.reset_daily_counters()
            print("📆 New day — daily counters reset")

        while self.actions_taken < MAX_ACTIONS_PER_SESSION:
            elapsed = time.time() - start
            if elapsed > max_time:
                print(f"\n⏱️  Time limit reached ({max_hours}h)")
                break

            print(f"\n{'─' * 60}")
            print(f"  🔄 Action {self.actions_taken + 1}/{MAX_ACTIONS_PER_SESSION} "
                  f"| {elapsed/60:.0f}m elapsed")
            print(f"{'─' * 60}")

            # Think & Act via LangGraph Multi-Agent Graph
            print("   🤖 Running LangGraph agentic step...")
            try:
                from langgraph_brain import run_agentic_workflow
                graph_run = await run_agentic_workflow()
                if graph_run:
                    self.actions_taken += 1
                    await asyncio.sleep(THINK_INTERVAL_SECONDS)
                    continue
            except Exception as ge:
                print(f"   [!] LangGraph run encountered an error, falling back to legacy: {ge}")

            # Think
            decision = await self.think(extra_context=specific_task)

            if not decision:
                print("   🤷 Brain couldn't decide. Waiting 60s...")
                await asyncio.sleep(60)
                continue

            print(f"\n   🧠 Decision: {decision['tool_name']}")
            if decision.get("reasoning"):
                print(f"   💭 Reasoning: {decision['reasoning'][:150]}")

            # Act
            result = await self.act(decision)

            # Reflect
            await self.reflect(decision, result)

            # Self-improvement cycle DISABLED — was corrupting source files

            # Pause between actions (Flow rate limiting handled in act())
            await asyncio.sleep(THINK_INTERVAL_SECONDS)

        # Session summary
        elapsed = time.time() - start
        print("\n" + "=" * 60)
        print(f"  🏁 SESSION COMPLETE")
        print(f"  Actions taken: {self.actions_taken}")
        print(f"  Runtime: {elapsed/60:.1f} minutes")
        print(f"  Models: {self.memory.model_count}")
        print(f"  Products scraped: {len(self.memory.data.get('products_scraped', []))}")
        print(f"  Ads generated: {len(self.memory.data.get('products_processed', []))}")
        print(f"  Posts made: {self.memory.data['performance']['total_posts']}")
        print(f"  Brands contacted: {len(self.memory.data.get('brands_contacted', []))}")
        print(f"  Learnings: {len(self.memory.data.get('learnings', []))}")
        print("=" * 60)

        await self.client.aclose()

    def show_status(self):
        """Print the current state of the agent."""
        print(self.memory.get_state_summary())


# ==========================================
# CLI
# ==========================================
async def main():
    dry_run = "--dry-run" in sys.argv
    status_only = "--status" in sys.argv
    max_hours = 24

    # Parse --run-hours
    for i, arg in enumerate(sys.argv):
        if arg == "--run-hours" and i + 1 < len(sys.argv):
            max_hours = float(sys.argv[i + 1])

    # Parse --task
    specific_task = ""
    for i, arg in enumerate(sys.argv):
        if arg == "--task" and i + 1 < len(sys.argv):
            specific_task = sys.argv[i + 1]

    brain = AgentBrain(dry_run=dry_run)

    if status_only:
        brain.show_status()
        return

    await brain.run(max_hours=max_hours, specific_task=specific_task)


if __name__ == "__main__":
    asyncio.run(main())
