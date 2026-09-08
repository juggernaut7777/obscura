## 2024-05-24 - Command Injection in User Input Prompts
**Vulnerability:** Command injection in `start_engine.py` via `os.system()` evaluating unsanitized user inputs (`prompt` and `niche`).
**Learning:** User inputs from `input()` were placed directly into f-strings representing shell commands, allowing shell metacharacter injection.
**Prevention:** Always use `subprocess.run()` with a list of arguments instead of strings, avoiding `shell=True` (or `os.system`) when parsing user input.
