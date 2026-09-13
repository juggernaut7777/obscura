## 2024-05-18 - Hardcoded Ngrok Production API Token
**Vulnerability:** A live production `NGROK_AUTH_TOKEN` was hardcoded as the default fallback value in `os.getenv()` in `goal2_sourcing_engine/all_in_one_bridge.py`.
**Learning:** Developers often leave hardcoded credentials during testing/development as a fallback, which inadvertently gets committed and exposes services to potential hijacking.
**Prevention:** Strictly rely on environment variables for API tokens without any hardcoded secret strings. Fail securely by validating the presence of the token and halting execution if missing.
