## 2024-03-24 - Remove Hardcoded Secrets
**Vulnerability:** A hardcoded production Ngrok API token was present as a fallback in `goal2_sourcing_engine/all_in_one_bridge.py`.
**Learning:** Fallbacks in `os.getenv` for API keys bypass security practices and lead to credential leaks.
**Prevention:** Ensure environment variable lookups for API tokens never contain hardcoded default production keys. Gracefully exit or log an error instead if it is missing.
## 2024-03-24 - Prevent Command Injection
**Vulnerability:** Use of `os.system()` and `subprocess` with `shell=True` can lead to command injection if arbitrary user input is passed to them.
**Learning:** Calling system shells without proper tokenization can easily lead to execution of malicious commands.
**Prevention:** Avoid `os.system()` and `subprocess` calls with `shell=True` when handling user input. Always use `subprocess.run()` and pass commands and their arguments safely as a list so they are not evaluated by a shell.
