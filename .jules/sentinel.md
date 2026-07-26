## 2024-07-26 - [Command Injection via os.system and input string concatenation]
**Vulnerability:** Found critical command injection vulnerabilities in Python scripts (e.g. `start_engine.py`) where user inputs were concatenated directly into shell commands strings and executed via `os.system()`.
**Learning:** `os.system()` with concatenated user input is fundamentally insecure because arbitrary shell commands can be injected. This pattern was heavily used in interactive CLI tools.
**Prevention:** Always use `subprocess.run` passing arguments as a list. Use `.split()` when dealing with space-separated multiple string inputs. Use `sys.executable` instead of `"python"` string literals to prevent PATH hijacking.
