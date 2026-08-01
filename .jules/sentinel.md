## 2024-05-24 - Fix Command Injection Vulnerability in CLI tools
**Vulnerability:** Command injection via direct string interpolation of user input `os.system(cmd)` where `cmd` was built from `prompt`, `script`, and `refs` in `goal2_sourcing_engine/start_engine.py` (menu option 10).
**Learning:** `os.system` is prone to command injection and is unsafe to use with user input. Also found multiple hardcoded `"python"` execution paths in `os.system` that rely on the environment `PATH`, risking execution using the wrong interpreter.
**Prevention:** Use `subprocess.run` with a list of arguments for safe command execution. Always use `sys.executable` to ensure scripts execute within the current Python virtual environment instead of hardcoded `"python"`.
