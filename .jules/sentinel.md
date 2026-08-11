## 2026-08-11 - Fix command injection in start_engine.py
**Vulnerability:** Command injection vulnerability in `start_engine.py` due to concatenating user input directly into an `os.system` shell command.
**Learning:** The interactive CLI tool was using an insecure pattern of constructing command strings for `os.system()` with unsanitized user inputs, making it trivial for an attacker to run arbitrary shell commands via input prompts.
**Prevention:** Always use `subprocess.run` (or similar `subprocess` functions) with a list of arguments, and use `shlex.split()` for safely parsing space-separated user strings, to prevent shell metacharacters from executing arbitrary commands.
