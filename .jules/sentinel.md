## 2025-03-09 - Hardcoded Ngrok token
**Vulnerability:** A production Ngrok auth token was hardcoded directly in `goal2_sourcing_engine/all_in_one_bridge.py`.
**Learning:** Developers often hardcode tokens for quick local testing and forget to remove them before committing.
**Prevention:** Always use environment variables for sensitive tokens and implement checks for their presence rather than providing hardcoded fallbacks.
