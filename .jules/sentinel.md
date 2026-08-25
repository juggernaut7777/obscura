## 2024-08-25 - Command Injection in User Input Handling
**Vulnerability:** Found a command injection vulnerability in `start_engine.py` where user inputs (`prompt`, `script`, `refs`) were concatenated directly into a string command and passed to `os.system(cmd)`.
**Learning:** Using `os.system` with string interpolation for user-provided inputs allows attackers to execute arbitrary shell commands (e.g., passing `" && rm -rf /"`).
**Prevention:** Always use `subprocess.run(cmd_list)` passing a list of arguments without `shell=True` to ensure inputs are passed safely and not evaluated by a shell.
