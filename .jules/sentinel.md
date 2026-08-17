## 2025-05-24 - Command Injection in start_engine.py
**Vulnerability:** User inputs (prompt, script, refs) were directly interpolated into a bash string and executed via `os.system()`, allowing for arbitrary command execution.
**Learning:** Using `os.system()` with formatted strings containing user inputs creates a critical command injection vector.
**Prevention:** Always use `subprocess.run()` with a list of arguments instead of a shell string, ensuring user input is safely passed as arguments and never evaluated by a shell.
