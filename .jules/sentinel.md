## 2024-05-18 - [CRITICAL] Fix Command Injection in start_engine.py
**Vulnerability:** User inputs (`prompt`, `script`, `refs`) were directly interpolated into a shell command string and executed via `os.system()`, allowing potential arbitrary command execution.
**Learning:** Using `os.system()` with string concatenation/interpolation on user input creates a severe command injection vector.
**Prevention:** Always use `subprocess.run()` with a list of arguments instead of a single string and `os.system()`, especially when handling user-provided data. Use `shlex.join()` for safe logging.
