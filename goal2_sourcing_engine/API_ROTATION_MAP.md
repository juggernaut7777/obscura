# OBSCURA AI Sourcing Pipeline — API Key Rotation & Use-Case Mapping
> **Last Updated:** June 16, 2026  
> **Status:** ACTIVE  

This document outlines the allocation, priority order, and optimal usage of the **11 free-tier API keys** across different providers in the OBSCURA AI fashion and resale pipeline. 

---

## 1. Provider Capabilities & Quota Limits

| Provider | Key Count | Active Models | Active Quota / Limits | Rate Limit Type |
| :--- | :---: | :--- | :--- | :--- |
| **Google Gemini** | **6** | Gemini 2.5/3.1 Flash Lite<br>Gemma 4 31B/26B<br>Gemini 2.5/3.5 Flash | 15 RPM, 250K TPM, 500 RPD (Flash Lite)<br>15 RPM, 1.5K RPD (Gemma 4)<br>5 RPM, 250K TPM, 20 RPD (Flash) | Per Key / Project (Limits multiply across projects) |
| **NVIDIA NIM** | **1** | Llama 3.2 11B Vision<br>Mistral Nemotron 70B<br>Llama 4 Maverick 17b | 40 RPM, Unlimited TPM | Shared Account Quota |
| **Groq** | **1** | Llama 3.3 70B Versatile<br>Llama 3.1 8b Instant<br>Llama 4 Scout 17b | 30 RPM, 14.4K RPD (Llama 3.3)<br>30 RPM, 14.4K RPD (Llama 3.1) | Shared Account Quota |
| **Cerebras** | **1** | Llama 3.3 70B<br>Llama 3.1 8b | 30 RPM, 1M Tokens/Day | High-Speed Inference Limit |
| **DeepSeek** | **1** | DeepSeek-Chat (DeepSeek-V3) | 100 RPM, 5M signup tokens | Account Balance |
| **OpenRouter** | **1** | Gemini 2.5 Flash Free<br>Llama 3.3 70B Free | Variable free credits (No hard limit) | Public Load Limits |
| **xAI Grok** | **1** | Grok-2 | 10 RPM (Trial Limits) | Cooldown-based |

---

## 2. Dynamic Router Fallback Cascades

LiteLLM Router dynamically rotates keys and routes calls. The fallback order is designed to optimize latency, prioritize the highest free-tier quotas first, and fallback to more rate-restricted models last.

```
[Primary Request: gemini-lite]
       │
       ├──► (Fallback 1) Cerebras Llama 70B / 8B (Highest free throughput & speed)
       │
       ├──► (Fallback 2) Groq Llama 70B / 8B (Fast responsive backup)
       │
       ├──► (Fallback 3) Gemini 3.1 Flash Lite / 2.5 Flash Lite (Workspace load-balancers)
       │
       ├──► (Fallback 4) Gemma 4 31B / 26B (High-context, high-RPM text)
       │
       ├──► (Fallback 5) Gemini 3.5 / 2.5 Flash (Rate-restricted, high-fidelity fallback)
       │
       ├──► (Fallback 6) xAI Grok-2 (Alternative reasoning check)
       │
       ├──► (Fallback 7) DeepSeek Chat (Token-based heavy reasoning)
       │
       └──► (Fallback 8) NVIDIA NIM (Nemotron / Maverick) / OpenRouter Free
```

---

## 3. Optimal Use-Case Assignment Matrix

To maximize efficiency and preserve token counts/RPM budgets, tasks are matched to specific models:

### 📸 Task A: Image Evaluation & VLM Scoring
* **Primary model:** `nvidia-llama-vision` (Llama 3.2 11B Vision via NVIDIA NIM)
* **Rationale:** NVIDIA NIM offers 40 RPM with zero token limits. This model is exceptionally fast and accurate at evaluating image layouts and flagging non-fashion items.
* **Secondary/Fallback:** `gemini-lite` (Gemini 2.5/3.1 Flash Lite via Gemini keys).

### 🏷️ Task B: Style Tagging & Gender Categorization
* **Primary model:** `gemini-lite` / `gemini-3.1-flash-lite`
* **Rationale:** Gemini's native multimodal processing is highly reliable at detecting style features and gender (male vs. female clothing). Multiplexing across 6 keys provides up to 90 RPM of vision capability.
* **Secondary/Fallback:** `nvidia-llama-vision`.

### 💬 Task C: Discord Bot Chat Brain (Interactive Mode)
* **Primary model:** `gemini-lite`
* **Rationale:** Requires low latency and conversational memory. Gemini Flash Lite has an extremely fast time-to-first-token and is free under the multiplexed keys.
* **Secondary/Fallback:** `groq-llama-70b` / `cerebras-llama-70b`.

### 🕵️ Task D: Reddit Sourcing & Seller Scout Parser
* **Primary model:** `deepseek-chat` / `cerebras-llama-70b`
* **Rationale:** Reading and parsing raw Reddit JSON feeds and text lists requires a model that can ingest large contexts without rate limits. DeepSeek V3 handles massive context sizes efficiently, and Cerebras is ultra-fast.
* **Secondary/Fallback:** `gemma-4-31b`.

### ✍️ Task E: Lookbook Descriptions & Instagram DM Outreach
* **Primary model:** `deepseek-chat`
* **Rationale:** Generating persuasive sales copy and copywriting requires strong reasoning and human-like prose. DeepSeek-Chat provides state-of-the-art text writing quality at zero cost via free tokens.
* **Secondary/Fallback:** `grok-2` / `gemini-3.5-flash`.

---

## 4. Operational Best Practices
1. **Never Hardcode Keys:** Keys must only reside in the `.env` file (loaded via `load_dotenv()`).
2. **Cool-down Protection:** A model endpoint that encounters a `429 Too Many Requests` is automatically put on cooldown for 60 seconds by the `LiteLLMRouter` to prevent loop-banning.
3. **Use Aliases:** Developers should use the generic aliases (`gemini-lite`, `gemini-flash`) instead of specific endpoints to allow the router to load-balance requests across all 6 keys.
