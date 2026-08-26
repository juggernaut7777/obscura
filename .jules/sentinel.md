## 2024-11-20 - Command Injection via os.system()
**Vulnerability:** Command Injection vulnerability found in `start_engine.py` where user input (`prompt`, `script`, `refs`) was concatenated directly into a string and executed using `os.system()`.
**Learning:** Python's `os.system()` passes strings directly to the shell, making it extremely vulnerable to command injection if any part of the string comes from user input.
**Prevention:** Always use `subprocess.run()` with a list of arguments instead of `os.system()` with string concatenation, avoiding `shell=True` whenever user input is involved.
