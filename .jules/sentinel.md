## 2024-05-24 - Fix Command Injection in Engine Setup
**Vulnerability:** Command Injection in `start_engine.py` (Option 10) due to directly interpolating unvalidated user input into `os.system(cmd)` shell commands.
**Learning:** Shell injections occur when user input isn't sanitized before being executed as part of an OS command. Even internal CLI tools can be vulnerable.
**Prevention:** Always use `subprocess.run` (or similar) with a list of arguments (e.g. `["python", "script.py", "--arg", user_input]`) instead of string formatting with `os.system()` to ensure arguments are passed safely to the OS without shell interpolation.
