## 2024-05-18 - Fix Command Injection in start_engine.py
**Vulnerability:** A critical command injection vulnerability in `start_engine.py` where untrusted user input from `input()` for prompts, scripts, and references was concatenated into a string and executed using `os.system()`.
**Learning:** Using `os.system()` with string concatenation based on user input exposes the system to command execution attacks.
**Prevention:** Always use `subprocess.run()` with a list of arguments and `shlex.split()` for parsing space-separated user inputs safely.
