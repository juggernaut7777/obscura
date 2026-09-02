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

from agent_memory import AgentMemory
from agent_tools_vps import TOOL_DEFINITIONS, execute_tool
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

# Model cascade — ROUND-ROBIN across 6 separate GCP projects
# Each key is in a DIFFERENT project = each has its OWN quota pool!
# Strategy: spread across models AND keys for maximum throughput
#
# Available models (tested Aug 31 2026):
#   gemini-3.5-flash      ← NEWEST, working, best quality
#   gemini-3.6-flash      ← available 
#   gemini-2.5-flash      ← solid workhorse, may be rate-limited
#   gemini-3.5-flash-lite ← higher RPM (30/min vs 10/min)
#   gemini-3.1-flash-lite ← fallback option

import random
_cascade_start_idx = random.randint(0, 5)  # Round-robin: start from random key each session

LLM_CASCADE = [
    # ── Tier 1A: gemini-3.6-flash (Fast, verified working, independent quota) ──
    {
        "name": "gemini-36-flash-k1",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.6-flash",
        "key_env": "GEMINI_API_KEY",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-36-flash-k2",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.6-flash",
        "key_env": "GEMINI_API_KEY_2",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-36-flash-k3",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.6-flash",
        "key_env": "GEMINI_API_KEY_3",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-36-flash-k4",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.6-flash",
        "key_env": "GEMINI_API_KEY_4",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-36-flash-k5",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.6-flash",
        "key_env": "GEMINI_API_KEY_5",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-36-flash-k6",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.6-flash",
        "key_env": "GEMINI_API_KEY_6",
        "max_tokens": 1024,
    },

    # ── Tier 1B: gemini-3.5-flash (Separate quota pool, high reasoning quality) ──
    {
        "name": "gemini-35-flash-k1",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.5-flash",
        "key_env": "GEMINI_API_KEY",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-35-flash-k2",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.5-flash",
        "key_env": "GEMINI_API_KEY_2",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-35-flash-k3",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.5-flash",
        "key_env": "GEMINI_API_KEY_3",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-35-flash-k4",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.5-flash",
        "key_env": "GEMINI_API_KEY_4",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-35-flash-k5",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.5-flash",
        "key_env": "GEMINI_API_KEY_5",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-35-flash-k6",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.5-flash",
        "key_env": "GEMINI_API_KEY_6",
        "max_tokens": 1024,
    },

    # ── Tier 2: gemini-2.5-flash (fallback if 3.5 quota used up) ──
    {
        "name": "gemini-25-flash-k1",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash",
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
        "name": "gemini-25-flash-k3",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash",
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
        "name": "gemini-25-flash-k5",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash",
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

    # ── Tier 3: gemini-3.5-flash-lite (30 RPM per key! 6×30 = 180 RPM total) ──
    {
        "name": "gemini-35-lite-k1",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.5-flash-lite",
        "key_env": "GEMINI_API_KEY",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-35-lite-k2",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.5-flash-lite",
        "key_env": "GEMINI_API_KEY_2",
        "max_tokens": 1024,
    },
    {
        "name": "gemini-35-lite-k3",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-3.5-flash-lite",
        "key_env": "GEMINI_API_KEY_3",
        "max_tokens": 1024,
    },

    # ── Tier 4: Non-Gemini fallbacks ──
    # Groq
    {
        "name": "groq-qwen-27b",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "qwen/qwen3.6-27b",
        "key_env": "GROQ_API_KEY",
        "max_tokens": 1024,
    },
    # OpenRouter
    {
        "name": "openrouter-free",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openrouter/free",
        "key_env": "OPENROUTER_API_KEY",
        "max_tokens": 1024,
    },
    # xAI Grok
    {
        "name": "xai-grok",
        "url": "https://api.x.ai/v1/chat/completions",
        "model": "grok-3-mini",
        "key_env": "XAI_API_KEY",
        "max_tokens": 1024,
    },
    # NVIDIA NIM
    {
        "name": "nvidia-llama4-maverick",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "meta/llama-4-maverick-17b-128e-instruct",
        "key_env": "NVIDIA_API_KEY",
        "max_tokens": 1024,
    },
    {
        "name": "nvidia-gemma4",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "google/gemma-4-31b-it",
        "key_env": "NVIDIA_API_KEY",
        "max_tokens": 1024,
    },
    # SambaNova
    {
        "name": "sambanova-llama",
        "url": "https://api.sambanova.ai/v1/chat/completions",
        "model": "Meta-Llama-3.3-70B-Instruct",
        "key_env": "SAMBANOVA_API_KEY",
        "max_tokens": 1024,
    },
]

# Round-robin: rotate Tier 1 entries so we don't always hammer key 1 first
_gemini_36 = [c for c in LLM_CASCADE if c["name"].startswith("gemini-36-flash-k")]
_gemini_35 = [c for c in LLM_CASCADE if c["name"].startswith("gemini-35-flash-k")]
_gemini_rest = [c for c in LLM_CASCADE if not (c["name"].startswith("gemini-36-flash-k") or c["name"].startswith("gemini-35-flash-k"))]

_rotated_36 = _gemini_36[_cascade_start_idx:] + _gemini_36[:_cascade_start_idx]
_rotated_35 = _gemini_35[_cascade_start_idx:] + _gemini_35[:_cascade_start_idx]
LLM_CASCADE = _rotated_36 + _rotated_35 + _gemini_rest
print(f"[BRAIN] Cascade starts at key index {_cascade_start_idx + 1} (round-robin across 3.6 & 3.5)")

MAX_ACTIONS_PER_SESSION = 200   # Increased — more work per session
THINK_INTERVAL_SECONDS = 60    # 1 minute between actions (was 5 min!)

# Rate limit backoff tracking
_rate_limit_backoff = {}  # model_name -> (next_retry_time, backoff_seconds)


SYSTEM_PROMPT = """You are an autonomous AI fashion content production agent running 24/7.

MODE: FULLY AUTONOMOUS PRODUCTION — Never wait for human approval. Keep working.

=== YOUR MISSION ===
Run the OBSCURA sourcing + lookbook generation pipeline non-stop.

=== MANDATORY PIPELINE ORDER ===
You MUST follow this priority chain. ALWAYS pick the HIGHEST-PRIORITY tool that has work to do:

PRIORITY 1 — SCRAPE NEW PRODUCTS (if MANUAL_CURATION has < 10 products):
  → scrape_yupoo_catalog with auto_pick=true, max_albums=5
  → Rotate through sellers: deateath, chaosmade, topstoney, goat-official, husky-reps, repsbrothers, topacney, unionkingdom, maden, idlt, pycstudio

PRIORITY 2 — CLASSIFY & TAG (if any product in MANUAL_CURATION lacks classification):
  → classify_product_images for unclassified products
  → tag_product_style for untagged products

PRIORITY 3 — MATCH OUTFITS (if enough tops + bottoms exist):
  → find_ready_outfits to pair matching items

PRIORITY 4 — GENERATE CAMPAIGNS (if any product has generation_status="pending"):
  → generate_ad_image for pending products

PRIORITY 5 — RESEARCH (every 10th action):
  → scrape_meta_ad_library for competitor creatives
  → research_web for trending streetwear

=== CRITICAL RULES ===
- Call ONE tool per response.
- NEVER call the same tool more than 3 times in a row. If you just called find_ready_outfits, switch to scrape_yupoo_catalog or classify_product_images next.
- NEVER stop and wait — always take the next useful action.
- If find_ready_outfits returns the same result, move to scraping or classifying instead.
- Source products from Yupoo sellers using scrape_yupoo_catalog tool.
- Focus on premium streetwear and high-quality blanks.
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
        self._recent_tools = []  # Track last N tool calls to enforce diversity

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
        failure_context_parts = []
        if _blocked_tools:
            blocked_list = "\n".join([
                f"  - {t}: {info['reason'] if isinstance(info, dict) else info}"
                for t, info in _blocked_tools.items()
            ])
            failure_context_parts.append(f"\n⚠️ TEMPORARILY BLOCKED TOOLS (will auto-retry soon):\n{blocked_list}\n")
        if _tool_failure_count:
            failing = {t: c for t, c in _tool_failure_count.items() if c > 0}
            if failing:
                fail_list = "\n".join([f"  - {t}: failed {c} times" for t, c in failing.items()])
                failure_context_parts.append(f"\n⚠️ RECENTLY FAILED TOOLS:\n{fail_list}\n")
        failure_context = "".join(failure_context_parts)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""Here is your current state:

{state_summary}
{failure_context}
{f'Additional context: {extra_context}' if extra_context else ''}

YOUR LAST 5 TOOL CALLS (most recent first): {', '.join(reversed(self._recent_tools[-5:])) if self._recent_tools else 'none yet'}

Decide your next action. Call exactly ONE tool. Think about:
- What's the highest-impact thing to do right now?
- Am I within daily limits?
- What have I learned that should change my approach?

CRITICAL DIVERSITY RULES:
- You MUST NOT call the same tool more than 3 times in a row. Look at your last 5 calls above.
- If your last 3 calls were all the same tool, you MUST pick a DIFFERENT tool now.
- If MANUAL_CURATION has fewer than 10 products, call scrape_yupoo_catalog.
- Rotate sellers: deateath, chaosmade, topstoney, goat-official, repsbrothers, topacney, maden.
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
            
            # ── HARD DIVERSITY ENFORCEMENT ──
            # If the same tool was called 3+ times in a row, force a different tool
            if len(self._recent_tools) >= 3 and all(t == tool_name for t in self._recent_tools[-3:]):
                # Force rotation based on pipeline priority
                forced_alternatives = [
                    ("scrape_yupoo_catalog", {"subdomain": "deateath", "max_albums": 5, "auto_pick": True}),
                    ("classify_product_images", {}),
                    ("tag_product_style", {}),
                    ("scrape_meta_ad_library", {"query": "streetwear fashion ads", "country": "US"}),
                ]
                for alt_name, alt_args in forced_alternatives:
                    if alt_name != tool_name and alt_name not in _blocked_tools:
                        print(f"   🔄 DIVERSITY OVERRIDE: {tool_name} called 3x in a row → forcing {alt_name}")
                        self._recent_tools.append(alt_name)
                        return {
                            "tool_name": alt_name,
                            "arguments": alt_args,
                            "reasoning": f"Forced diversity: {tool_name} was stuck in a loop",
                        }
            
            # Track this tool call
            self._recent_tools.append(tool_name)
            # Keep only last 10
            if len(self._recent_tools) > 10:
                self._recent_tools = self._recent_tools[-10:]
                
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

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
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
                    # Rate limited — cap backoff at 120s (keys share same project quota)
                    old_backoff = _rate_limit_backoff.get(name, (0, 30))[1]
                    new_backoff = min(old_backoff * 2, 120)  # Max 2 minutes (was 3600!)
                    _rate_limit_backoff[name] = (now + new_backoff, new_backoff)
                    print(f"   ⚠️  {name}: rate limited, backing off {new_backoff}s")
                    # Add small delay before trying next key to avoid burst-hitting the shared quota
                    await asyncio.sleep(2)
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
