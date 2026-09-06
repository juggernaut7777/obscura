## 2024-05-24 - Command Injection in CLI Scripts
**Vulnerability:** Command injection via unsanitized `input()` passed to `os.system()`.
**Learning:** CLI scripts in this repository use string formatting to build shell commands (e.g., `f'python script.py --prompt "{prompt}"'`), exposing them to injection.
**Prevention:** Always use `subprocess.run()` with a list of arguments and `shlex.join()` for logging to prevent shell evaluation.
