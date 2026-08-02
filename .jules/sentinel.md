
## 2024-05-18 - Fix Command Injection in UGC Ad Creator
**Vulnerability:** Command Injection in `goal2_sourcing_engine/start_engine.py` via `os.system` using unsanitized user inputs (`prompt`, `script`, `refs`).
**Learning:** Shell strings constructed with user input and executed via `os.system` can be trivially exploited to run arbitrary commands.
**Prevention:** Always use `subprocess.run` with a list of arguments instead of string interpolation for shell commands. Additionally, use `sys.executable` instead of hardcoding `python`.
