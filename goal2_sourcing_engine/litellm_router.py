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

        # ─── 1. GOOGLE GEMINI KEYS (Each key = separate project = separate quota) ───
        gemini_keys = [
            val for key, val in os.environ.items() 
            if key.startswith("GEMINI_API_KEY")
        ]
        seen_keys = set()
        unique_gemini_keys = []
        for k in gemini_keys:
            if k and k.strip() and k not in seen_keys:
                seen_keys.add(k)
                unique_gemini_keys.append(k)

        for i, api_key in enumerate(unique_gemini_keys):
            # ═══════════════════════════════════════════════════════════════
            # 1a. GENERIC ALIASES (load-balance across model generations)
            # ═══════════════════════════════════════════════════════════════

            # gemini-lite → fast flash-lite models (30 RPM each across 6 keys = 180 RPM!)
            for lite_model, lite_rpm in [
                ("gemini-3.5-flash-lite", 30),
                ("gemini-2.5-flash-lite", 15),
                ("gemini-2.5-flash", 10),
            ]:
                model_list.append({
                    "model_name": "gemini-lite",
                    "litellm_params": {
                        "model": f"gemini/{lite_model}",
                        "api_key": api_key,
                        "rpm": lite_rpm
                    }
                })

            # gemini-flash → mainline flash models (15 RPM each across 6 keys = 90 RPM!)
            for flash_model, flash_rpm in [
                ("gemini-3.5-flash", 15),
                ("gemini-3.6-flash", 15),
                ("gemini-2.5-flash", 10),
            ]:
                model_list.append({
                    "model_name": "gemini-flash",
                    "litellm_params": {
                        "model": f"gemini/{flash_model}",
                        "api_key": api_key,
                        "rpm": flash_rpm
                    }
                })

            # gemini-pro → pro-tier models for complex reasoning
            for pro_model, pro_rpm in [
                ("gemini-2.5-pro", 5),
                ("gemini-1.5-pro", 2),
            ]:
                model_list.append({
                    "model_name": "gemini-pro",
                    "litellm_params": {
                        "model": f"gemini/{pro_model}",
                        "api_key": api_key,
                        "rpm": pro_rpm
                    }
                })



            # gemini-image → models with native image generation
            for img_model, img_rpm in [
                ("gemini-3.1-flash-image", 10),
                ("gemini-3.1-flash-lite-image", 10),
                ("gemini-3-pro-image", 5),
                ("gemini-2.5-flash-image", 5),
            ]:
                model_list.append({
                    "model_name": "gemini-image",
                    "litellm_params": {
                        "model": f"gemini/{img_model}",
                        "api_key": api_key,
                        "rpm": img_rpm
                    }
                })

            # ═══════════════════════════════════════════════════════════════
            # 1b. SPECIFIC MODEL TARGETS (direct routing & fallback chains)
            # ═══════════════════════════════════════════════════════════════

            # ── FLASH MODELS (Text/Vision/Reasoning) ──
            model_list.append({
                "model_name": "gemini-3.5-flash",
                "litellm_params": {
                    "model": "gemini/gemini-3.5-flash",
                    "api_key": api_key,
                    "rpm": 15
                }
            })
            model_list.append({
                "model_name": "gemini-3.6-flash",
                "litellm_params": {
                    "model": "gemini/gemini-3.6-flash",
                    "api_key": api_key,
                    "rpm": 15
                }
            })
            model_list.append({
                "model_name": "gemini-2.5-flash",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-flash",
                    "api_key": api_key,
                    "rpm": 10
                }
            })
            model_list.append({
                "model_name": "gemini-1.5-flash",
                "litellm_params": {
                    "model": "gemini/gemini-1.5-flash",
                    "api_key": api_key,
                    "rpm": 15
                }
            })

            # ── FLASH-LITE MODELS (High RPM workhorses) ──
            model_list.append({
                "model_name": "gemini-3.5-flash-lite",
                "litellm_params": {
                    "model": "gemini/gemini-3.5-flash-lite",
                    "api_key": api_key,
                    "rpm": 30
                }
            })
            model_list.append({
                "model_name": "gemini-2.5-flash-lite",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-flash-lite",
                    "api_key": api_key,
                    "rpm": 15
                }
            })
            model_list.append({
                "model_name": "gemini-2.5-flash-lite",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-flash-lite",
                    "api_key": api_key,
                    "rpm": 15
                }
            })

            # ── PRO MODELS (Complex reasoning, deep analysis) ──
            model_list.append({
                "model_name": "gemini-2.5-pro",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-pro",
                    "api_key": api_key,
                    "rpm": 5
                }
            })
            model_list.append({
                "model_name": "gemini-1.5-pro",
                "litellm_params": {
                    "model": "gemini/gemini-1.5-pro",
                    "api_key": api_key,
                    "rpm": 5
                }
            })


            # ── IMAGE GENERATION MODELS ──
            model_list.append({
                "model_name": "gemini-3.1-flash-image",
                "litellm_params": {
                    "model": "gemini/gemini-3.1-flash-image",
                    "api_key": api_key,
                    "rpm": 10
                }
            })
            model_list.append({
                "model_name": "gemini-3.1-flash-lite-image",
                "litellm_params": {
                    "model": "gemini/gemini-3.1-flash-lite-image",
                    "api_key": api_key,
                    "rpm": 10
                }
            })
            model_list.append({
                "model_name": "gemini-3-pro-image",
                "litellm_params": {
                    "model": "gemini/gemini-3-pro-image",
                    "api_key": api_key,
                    "rpm": 5
                }
            })
            model_list.append({
                "model_name": "nano-banana-pro",
                "litellm_params": {
                    "model": "gemini/nano-banana-pro-preview",
                    "api_key": api_key,
                    "rpm": 5
                }
            })
            model_list.append({
                "model_name": "gemini-2.5-flash-image",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-flash-image",
                    "api_key": api_key,
                    "rpm": 5
                }
            })

            # ── OMNI / VIDEO / AUDIO MODELS ──
            model_list.append({
                "model_name": "gemini-omni-flash",
                "litellm_params": {
                    "model": "gemini/gemini-omni-flash-preview",
                    "api_key": api_key,
                    "rpm": 5
                }
            })

            # ── TTS MODELS (Text-to-Speech) ──
            model_list.append({
                "model_name": "gemini-3.1-tts",
                "litellm_params": {
                    "model": "gemini/gemini-3.1-flash-tts-preview",
                    "api_key": api_key,
                    "rpm": 10
                }
            })
            model_list.append({
                "model_name": "gemini-2.5-flash-tts",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-flash-preview-tts",
                    "api_key": api_key,
                    "rpm": 10
                }
            })
            model_list.append({
                "model_name": "gemini-2.5-pro-tts",
                "litellm_params": {
                    "model": "gemini/gemini-2.5-pro-preview-tts",
                    "api_key": api_key,
                    "rpm": 5
                }
            })

            # ── LATEST AUTO-ALIASES (always point to newest stable) ──
            model_list.append({
                "model_name": "gemini-flash-latest",
                "litellm_params": {
                    "model": "gemini/gemini-flash-latest",
                    "api_key": api_key,
                    "rpm": 10
                }
            })
            model_list.append({
                "model_name": "gemini-flash-lite-latest",
                "litellm_params": {
                    "model": "gemini/gemini-flash-lite-latest",
                    "api_key": api_key,
                    "rpm": 15
                }
            })
            model_list.append({
                "model_name": "gemini-pro-latest",
                "litellm_params": {
                    "model": "gemini/gemini-pro-latest",
                    "api_key": api_key,
                    "rpm": 2
                }
            })

            # ── GEMMA OPEN MODELS (15 RPM, strong reasoning) ──
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
                "model_name": "groq-qwen-27b",
                "litellm_params": {
                    "model": "groq/qwen/qwen3.6-27b",
                    "api_key": groq_key,
                    "rpm": 30
                }
            })
            model_list.append({
                "model_name": "groq-gpt-oss-20b",
                "litellm_params": {
                    "model": "groq/openai/gpt-oss-20b",
                    "api_key": groq_key,
                    "rpm": 30
                }
            })
            model_list.append({
                "model_name": "groq-gpt-oss-20b-2",
                "litellm_params": {
                    "model": "groq/openai/gpt-oss-20b",
                    "api_key": groq_key,
                    "rpm": 30
                }
            })

        # ─── 2b. CEREBRAS KEYS (Highest priority — 1M tokens/day FREE, 2600+ TPS) ───
        cerebras_key = os.getenv("CEREBRAS_API_KEY")
        if cerebras_key:
            # Llama 4 Scout: 2600+ tokens/sec — THE fastest free inference model
            model_list.append({
                "model_name": "cerebras-gpt-oss-120b-2",
                "litellm_params": {
                    "model": "cerebras/gpt-oss-120b",
                    "api_key": cerebras_key,
                    "rpm": 30
                }
            })
            # Llama 3.3 70B on Cerebras — fast & capable for classification/reasoning
            model_list.append({
                "model_name": "cerebras-gpt-oss-120b",
                "litellm_params": {
                    "model": "cerebras/gpt-oss-120b",
                    "api_key": cerebras_key,
                    "rpm": 30
                }
            })
            model_list.append({
                "model_name": "cerebras-gpt-oss-120b",
                "litellm_params": {
                    "model": "cerebras/gpt-oss-120b",
                    "api_key": cerebras_key,
                    "rpm": 30
                }
            })
            model_list.append({
                "model_name": "cerebras-gemma-4-31b",
                "litellm_params": {
                    "model": "cerebras/gemma-4-31b",
                    "api_key": cerebras_key,
                    "rpm": 30
                }
            })

        # ─── 2c. SAMBANOVA KEYS ($5 free credits, 400+ TPS on Llama 405B) ───
        sambanova_key = os.getenv("SAMBANOVA_API_KEY")
        if sambanova_key:
            model_list.append({
                "model_name": "sambanova-llama-4-maverick",
                "litellm_params": {
                    "model": "sambanova/Llama-4-Maverick-17B-128E-Instruct",
                    "api_key": sambanova_key,
                    "rpm": 50
                }
            })
            model_list.append({
                "model_name": "sambanova-llama",
                "litellm_params": {
                    "model": "sambanova/Meta-Llama-3.3-70B-Instruct",
                    "api_key": sambanova_key,
                    "rpm": 50
                }
            })

        # ─── 3. OPENROUTER FREE KEYS ───
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            model_list.append({
                "model_name": "openrouter-free",
                "litellm_params": {
                    "model": "openrouter/openrouter/auto",
                    "api_key": openrouter_key,
                    "rpm": 20
                }
            })
            model_list.append({
                "model_name": "openrouter-nemotron-free",
                "litellm_params": {
                    "model": "openrouter/nvidia/nemotron-3-ultra:free",
                    "api_key": openrouter_key,
                    "rpm": 20
                }
            })
            model_list.append({
                "model_name": "openrouter-gemma-free",
                "litellm_params": {
                    "model": "openrouter/google/gemma-2-9b-it:free",
                    "api_key": openrouter_key,
                    "rpm": 20
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
            missing.append("Cerebras (cloud.cerebras.ai - 1M tok/day FREE, 2600+ TPS)")
        if not os.getenv("SAMBANOVA_API_KEY"):
            missing.append("SambaNova (cloud.sambanova.ai - $5 free, 400+ TPS on 405B)")
        if missing:
            print(f"[LITELLM] [!] Missing free providers: {', '.join(missing)}")

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

        # Check if messages contain image_url (Vision task)
        has_images = any(
            isinstance(m.get("content"), list) and any(isinstance(item, dict) and item.get("type") == "image_url" for item in m.get("content", []))
            for m in full_messages
        )

        if has_images:
            all_fallbacks = [
                "gemini-flash",
                "gemini-lite",
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-1.5-flash",
                "gemini-2.5-pro",
                "nvidia-llama-vision",
                "openrouter-free"
            ]
        else:
            all_fallbacks = [
                # ── Fast free inference ──
                "cerebras-gpt-oss-120b-2",
                "cerebras-gpt-oss-120b",
                "cerebras-gpt-oss-120b",
                "cerebras-gemma-4-31b",
                "sambanova-llama-4-maverick",
                "sambanova-llama",
                "groq-gpt-oss-20b-2",
                "groq-qwen-27b",
                # ── Gemini Lite (high RPM) ──
                "gemini-lite",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash-lite",
                "gemini-1.5-flash",
                # ── Gemini Flash ──
                "gemini-flash",
                "gemini-2.5-flash",
                "gemini-2.5-flash",
                # ── Gemini Pro ──
                "gemini-pro",
                "gemini-2.5-pro",
                "gemini-1.5-pro",
                # ── Other providers ──
                "grok-2",
                "deepseek-chat",
                "nvidia-nemotron",
                "openrouter-free",
                "openrouter-nemotron-free",
                "nvidia-llama-maverick",
                "groq-gpt-oss-20b"
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

        # Check if messages contain image_url (Vision task)
        has_images = any(
            isinstance(m.get("content"), list) and any(isinstance(item, dict) and item.get("type") == "image_url" for item in m.get("content", []))
            for m in full_messages
        )

        if has_images:
            all_fallbacks = [
                "gemini-flash",
                "gemini-lite",
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-1.5-flash",
                "gemini-2.5-pro",
                "nvidia-llama-vision",
                "openrouter-free"
            ]
        else:
            all_fallbacks = [
                # ── Fast free inference ──
                "cerebras-gpt-oss-120b-2",
                "cerebras-gpt-oss-120b",
                "cerebras-gpt-oss-120b",
                "cerebras-gemma-4-31b",
                "sambanova-llama-4-maverick",
                "sambanova-llama",
                "groq-gpt-oss-20b-2",
                "groq-qwen-27b",
                # ── Gemini Lite (high RPM) ──
                "gemini-lite",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash-lite",
                "gemini-1.5-flash",
                # ── Gemini Flash ──
                "gemini-flash",
                "gemini-2.5-flash",
                "gemini-2.5-flash",
                # ── Gemini Pro ──
                "gemini-pro",
                "gemini-2.5-pro",
                "gemini-1.5-pro",
                # ── Other providers ──
                "grok-2",
                "deepseek-chat",
                "nvidia-nemotron",
                "openrouter-free",
                "openrouter-nemotron-free",
                "nvidia-llama-maverick",
                "groq-gpt-oss-20b"
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

