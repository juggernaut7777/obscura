## 2026-08-21 - Command Injection in Interactive Prompts
**Vulnerability:** User inputs (`prompt`, `script`, `refs`) were concatenated directly into a shell string and executed via `os.system()` in `start_engine.py`. This allowed a malicious user to inject arbitrary shell commands (e.g., `; rm -rf /`).
**Learning:** Even internal or CLI-driven tools must treat user input as untrusted. `os.system()` implicitly spawns a shell that parses and evaluates string inputs, making it highly vulnerable to injection.
**Prevention:** Always use `subprocess.run()` with a list of arguments instead of a single string. This bypasses the shell entirely, passing arguments directly to the executable.
