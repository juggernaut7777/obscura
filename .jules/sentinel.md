## 2024-05-18 - [Command Injection via os.system]
**Vulnerability:** Found critical command injection vulnerabilities in `start_engine.py` where `os.system()` was used with interpolated user input (e.g., `cmd = f"python compile_ugc_ad.py --prompt \"{prompt}\" ..."`).
**Learning:** Using `os.system` or `subprocess.run(shell=True)` with string interpolation allows users to easily break out of quotes and execute arbitrary shell commands (e.g., `"; rm -rf /"`).
**Prevention:** Always use `subprocess.run` with a list of arguments instead of a single string. This avoids the shell interpreter entirely. Furthermore, prefer using `sys.executable` for Python scripts to prevent PATH hijacking.
