## 2024-05-18 - Fix Command Injection in start_engine.py
**Vulnerability:** `os.system()` was used directly with interpolated strings from user input (`prompt`, `script`, `refs`) in a CLI script, leading to Command Injection.
**Learning:** Python CLI tools in this codebase frequently use `os.system` for basic process spawning. When arguments are passed, this leads to injection vulnerabilities.
**Prevention:** Use `subprocess.run` with an argument list, and `sys.executable` for Python scripts to avoid PATH hijacking.
