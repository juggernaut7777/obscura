## 2024-05-24 - [Command Injection in CLI Menu]
**Vulnerability:** Command injection vulnerability in `goal2_sourcing_engine/start_engine.py` via unsanitized user input (`prompt`, `script`, `refs`) passed directly to `os.system` using f-strings.
**Learning:** Using `os.system()` with string concatenation for user-supplied arguments inherently allows for command injection because the string is evaluated by the shell, bypassing argument escaping.
**Prevention:** Always use `subprocess.run` with a list of arguments (which avoids shell evaluation) instead of string concatenation, and use `shlex.split()` to safely parse space-separated user inputs.
