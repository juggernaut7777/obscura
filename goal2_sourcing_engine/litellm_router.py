"""
LiteLLM Resilient Router Wrapper
=================================
Manages all free-tier API keys, rate limit handling, key rotation,
and provider-to-provider cascading fallback logic in one unified class.
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Set logging level for litellm to suppress redundant info
logging.getLogger('litellm').setLevel(logging.WARNING)

load_dotenv(override=True)

class LiteLLMRouter:
    def __init__(self):
        self.router = None
        self._setup_router()

    def _setup_router(self):
        """Initialise LiteLLM Router with all free keys and fallback configs."""
        try:
            from litellm import Router
        except ImportError:
            print("[!] litellm not installed yet, placeholder initialised.")
            return

        model_list = []

        # ─── 1. GOOGLE GEMINI KEYS (Multiplexed) ───
        # Gather all Gemini keys from environment variables matching GEMINI_API_KEY*
        gemini_keys = [
            val for key, val in os.environ.items() 
            if key.startswith("GEMINI_API_KEY")
        ]
        # Filter out duplicates and empty keys
        seen_keys = set()
        unique_gemini_keys = []
        for k in gemini_keys:
            if k and k.strip() and k not in seen_keys:
                seen_keys.add(k)
                unique_gemini_keys.append(k)

        # Register each Gemini key with MULTIPLE models to maximize total RPM throughput
        for i, api_key in enumerate(unique_gemini_keys):
            # --- 1a. Generic Aliases (for load-balancing across generations) ---
            # gemini-lite maps to both 2.5-lite and 3.1-lite
            model_list.append({
                "model_name": "gemini-lite",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-flash-lite",
                    "api_key": api_key,
                    "rpm": 10
                }
            })
            model_list.append({
                "model_name": "gemini-lite",
                "litellm_params": {
                    "model": "gemini/gemini-3.1-flash-lite",
                    "api_key": api_key,
                    "rpm": 15
                }
            })
            # gemini-flash maps to 2.5, 3.5, and 3-preview
            model_list.append({
                "model_name": "gemini-flash",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-flash",
                    "api_key": api_key,
                    "rpm": 5
                }
            })
            model_list.append({
                "model_name": "gemini-flash",
                "litellm_params": {
                    "model": "gemini/gemini-3.5-flash",
                    "api_key": api_key,
                    "rpm": 5
                }
            })
            model_list.append({
                "model_name": "gemini-flash",
                "litellm_params": {
                    "model": "gemini/gemini-3-flash-preview",
                    "api_key": api_key,
                    "rpm": 5
                }
            })

            # --- 1b. Specific Model Targets (for direct or fallback routing) ---
            model_list.append({
                "model_name": "gemini-3.1-flash-lite",
                "litellm_params": {
                    "model": "gemini/gemini-3.1-flash-lite",
                    "api_key": api_key,
                    "rpm": 15
                }
            })
            model_list.append({
                "model_name": "gemini-2.5-flash-lite",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-flash-lite",
                    "api_key": api_key,
                    "rpm": 10
                }
            })
            model_list.append({
                "model_name": "gemini-3.5-flash",
                "litellm_params": {
                    "model": "gemini/gemini-3.5-flash",
                    "api_key": api_key,
                    "rpm": 5
                }
            })
            model_list.append({
                "model_name": "gemini-3-flash-preview",
                "litellm_params": {
                    "model": "gemini/gemini-3-flash-preview",
                    "api_key": api_key,
                    "rpm": 5
                }
            })
            model_list.append({
                "model_name": "gemini-2.5-flash",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-flash",
                    "api_key": api_key,
                    "rpm": 5
                }
            })
            model_list.append({
                "model_name": "gemma-4-31b",
                "litellm_params": {
                    "model": "gemini/gemma-4-31b-it",
                    "api_key": api_key,
                    "rpm": 15
                }
            })
            model_list.append({
                "model_name": "gemma-4-26b",
                "litellm_params": {
                    "model": "gemini/gemma-4-26b-a4b-it",
                    "api_key": api_key,
                    "rpm": 15
                }
            })

        # ─── 2. GROQ KEYS ───
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            model_list.append({
                "model_name": "groq-llama-70b",
                "litellm_params": {
                    "model": "groq/llama-3.3-70b-versatile",
                    "api_key": groq_key,
                    "rpm": 30
                }
            })
            model_list.append({
                "model_name": "groq-llama-8b",
                "litellm_params": {
                    "model": "groq/llama-3.1-8b-instant",
                    "api_key": groq_key,
                    "rpm": 30
                }
            })
            model_list.append({
                "model_name": "groq-llama-4-scout",
                "litellm_params": {
                    "model": "groq/meta-llama/llama-4-scout-17b-16e-instruct",
                    "api_key": groq_key,
                    "rpm": 30
                }
            })

        # ─── 2b. CEREBRAS KEYS (Highest priority for free limits) ───
        cerebras_key = os.getenv("CEREBRAS_API_KEY")
        if cerebras_key:
            model_list.append({
                "model_name": "cerebras-gpt-oss-120b",
                "litellm_params": {
                    "model": "cerebras/gpt-oss-120b",
                    "api_key": cerebras_key,
                    "rpm": 30
                }
            })
            model_list.append({
                "model_name": "cerebras-zai-glm-4.7",
                "litellm_params": {
                    "model": "cerebras/zai-glm-4.7",
                    "api_key": cerebras_key,
                    "rpm": 30
                }
            })

        # ─── 3. OPENROUTER FREE KEYS ───
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            model_list.append({
                "model_name": "openrouter-gemini-free",
                "litellm_params": {
                    "model": "openrouter/google/gemini-2.5-flash-preview:free",
                    "api_key": openrouter_key
                }
            })
            model_list.append({
                "model_name": "openrouter-llama-free",
                "litellm_params": {
                    "model": "openrouter/meta-llama/llama-3.3-70b-instruct:free",
                    "api_key": openrouter_key
                }
            })

        # ─── 4. NVIDIA NIM FREE KEYS (OpenAI-compatible integration) ───
        nvidia_key = os.getenv("NVIDIA_API_KEY") or os.getenv("NVAPI_KEY")
        if nvidia_key:
            model_list.append({
                "model_name": "nvidia-nemotron",
                "litellm_params": {
                    "model": "openai/mistralai/mistral-nemotron",
                    "api_base": "https://integrate.api.nvidia.com/v1",
                    "api_key": nvidia_key,
                    "rpm": 40
                }
            })
            model_list.append({
                "model_name": "nvidia-llama-vision",
                "litellm_params": {
                    "model": "openai/meta/llama-3.2-11b-vision-instruct",
                    "api_base": "https://integrate.api.nvidia.com/v1",
                    "api_key": nvidia_key,
                    "rpm": 40
                }
            })
            model_list.append({
                "model_name": "nvidia-llama-maverick",
                "litellm_params": {
                    "model": "openai/meta/llama-4-maverick-17b-128e-instruct",
                    "api_base": "https://integrate.api.nvidia.com/v1",
                    "api_key": nvidia_key,
                    "rpm": 40
                }
            })

        # ─── 5. xAI GROK FREE KEYS ───
        xai_key = os.getenv("XAI_API_KEY")
        if xai_key:
            model_list.append({
                "model_name": "grok-2",
                "litellm_params": {
                    "model": "xai/grok-2",
                    "api_key": xai_key,
                    "rpm": 10
                }
            })

        # ─── 6. DEEPSEEK KEYS (High concurrency & reasoning fallback) ───
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            model_list.append({
                "model_name": "deepseek-chat",
                "litellm_params": {
                    "model": "deepseek/deepseek-chat",
                    "api_key": deepseek_key,
                    "rpm": 100
                }
            })

        # Configure LiteLLM Router with load balancing, 429 retries, and cooldown tracking
        # Collect registered model names so we can filter the fallback chain
        registered_models = set(m["model_name"] for m in model_list)

        self.router = Router(
            model_list=model_list,
            routing_strategy="simple-shuffle",  # Lightweight key rotation without background ping loops
            num_retries=3,
            cooldown_time=60,  # Put endpoint on cooldown for 60s if it fails or rates limit
            set_verbose=False
        )

        # Print startup summary of active providers
        provider_counts = {}
        for m in model_list:
            provider = m["model_name"].split("-")[0] if "-" in m["model_name"] else m["model_name"]
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        provider_str = ", ".join(f"{k}({v})" for k, v in sorted(provider_counts.items()))
        print(f"[LITELLM] Router active with {len(model_list)} endpoints: {provider_str}")

        # Warn about missing providers that could be added for free
        missing = []
        if not os.getenv("CEREBRAS_API_KEY"):
            missing.append("Cerebras (cloud.cerebras.ai - 1M tok/day FREE)")
        if not os.getenv("SAMBANOVA_API_KEY"):
            missing.append("SambaNova (cloud.sambanova.ai - $5 free)")
        if missing:
            print(f"[LITELLM] Missing free providers: {', '.join(missing)}")

        # Store registered models for fallback filtering
        self._registered_models = registered_models

    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        primary_model: str = "gemini-lite",
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 1024,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Safely fetch chat completion with full rate-limit resilience.
        Falls back to other models automatically.
        """
        import litellm
        if not self.router:
            self._setup_router()
            if not self.router:
                raise RuntimeError("LiteLLM is not installed or failed to initialize.")

        # Prep system instruction if provided separately (standard format for LiteLLM)
        full_messages = []
        if system_instruction:
            full_messages.append({"role": "system", "content": system_instruction})
        full_messages.extend(messages)

        # Logical fallback chains for zero-budget quota protection
        # Only include models that are actually registered (have valid API keys)
        all_fallbacks = [
            "cerebras-gpt-oss-120b",     # Highest free limits
            "cerebras-zai-glm-4.7",
            "groq-llama-70b",         # High speed, separate limits
            "gemini-3.1-flash-lite",  # New generation models
            "gemini-lite",            # Load-balancing lite models
            "gemma-4-31b",
            "gemma-4-26b",
            "gemini-3-flash-preview",
            "gemini-3.5-flash",
            "gemini-flash",           # Load-balancing flash models
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "groq-llama-4-scout",     # New groq model
            "grok-2",                 # xAI grok
            "deepseek-chat",          # DeepSeek chat
            "nvidia-nemotron",
            "openrouter-gemini-free",
            "nvidia-llama-maverick",
            "groq-llama-8b"
        ]

        # Filter: only keep fallbacks that have valid API keys registered
        fallbacks = [f for f in all_fallbacks if f in self._registered_models]

        # Remove primary model from fallbacks if it's already in there
        if primary_model in fallbacks:
            fallbacks.remove(primary_model)

        # Call with fallback parameters
        try:
            # Inject options dynamically
            kwargs = {
                "model": primary_model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "fallbacks": fallbacks,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice or "auto"
            if response_format:
                kwargs["response_format"] = response_format

            # Trigger LiteLLM Router
            response = await self.router.acompletion(**kwargs)
            return response
        except Exception as e:
            print(f"[LITELLM ERROR] Router completions completely failed: {e}")
            # Last-ditch manual fallback using raw python standard requests
            raise e

    def get_chat_completion_sync(
        self,
        messages: List[Dict[str, str]],
        primary_model: str = "gemini-lite",
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 1024,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronously fetch chat completion with full rate-limit resilience.
        Falls back to other models automatically.
        """
        if not self.router:
            self._setup_router()
            if not self.router:
                raise RuntimeError("LiteLLM is not installed or failed to initialize.")

        full_messages = []
        if system_instruction:
            full_messages.append({"role": "system", "content": system_instruction})
        full_messages.extend(messages)

        all_fallbacks = [
            "cerebras-gpt-oss-120b",
            "cerebras-zai-glm-4.7",
            "groq-llama-70b",
            "gemini-3.1-flash-lite",
            "gemini-lite",
            "gemma-4-31b",
            "gemma-4-26b",
            "gemini-3-flash-preview",
            "gemini-3.5-flash",
            "gemini-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "groq-llama-4-scout",
            "grok-2",
            "deepseek-chat",
            "nvidia-nemotron",
            "openrouter-gemini-free",
            "nvidia-llama-maverick",
            "groq-llama-8b"
        ]
        fallbacks = [f for f in all_fallbacks if f in self._registered_models]

        if primary_model in fallbacks:
            fallbacks.remove(primary_model)

        try:
            kwargs = {
                "model": primary_model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "fallbacks": fallbacks,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice or "auto"
            if response_format:
                kwargs["response_format"] = response_format

            response = self.router.completion(**kwargs)
            return response
        except Exception as e:
            print(f"[LITELLM ERROR] Router sync completions completely failed: {e}")
            raise e

# Single instance importable anywhere
shared_router = LiteLLMRouter()

