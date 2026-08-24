## 2025-02-14 - Command Injection via `os.system`
**Vulnerability:** Found a critical command injection vulnerability in `goal2_sourcing_engine/start_engine.py` where raw user input was concatenated into a shell string and executed via `os.system(cmd)`.
**Learning:** This existed because `os.system` is commonly used for rapid scripting, often forgetting that it passes strings directly to the shell, allowing attackers to inject arbitrary commands via shell metacharacters.
**Prevention:** Always use `subprocess.run` with a list of arguments instead of a single string. When user inputs are space-separated, properly tokenize them using `.split()` before extending the command list. Use `shlex.join(cmd_list)` for safe and accurate logging.
