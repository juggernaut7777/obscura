## 2024-05-15 - Command Injection in start_engine.py
**Vulnerability:** Found a command injection vulnerability in `goal2_sourcing_engine/start_engine.py` where user input was directly concatenated into a string and passed to `os.system()`.
**Learning:** Using `os.system()` with string formatting on user input allows arbitrary command execution.
**Prevention:** Always use `subprocess.run()` with a list of arguments instead of passing a formatted string to a shell.
