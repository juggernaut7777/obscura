## 2025-03-09 - Command Injection in start_engine.py
**Vulnerability:** User input passed to `os.system()` created a command injection vulnerability.
**Learning:** Relying on `os.system()` and f-strings for shell commands is inherently unsafe when handling user input.
**Prevention:** Always use `subprocess.run()` with a list of arguments and avoid shell interpretation.
