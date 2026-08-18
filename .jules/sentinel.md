## 2026-06-05 - Fix Command Injection Vulnerability in CLI tools
**Vulnerability:** User inputs were concatenated into a string and passed to `os.system()` in `goal2_sourcing_engine/start_engine.py`, creating a command injection vulnerability.
**Learning:** Internal CLI tools often use `os.system()` for convenience, but taking user inputs directly into these commands poses severe risks (e.g. executing arbitrary commands with `;` or `&&`).
**Prevention:** Always use `subprocess.run()` with a list of arguments, rather than `shell=True` or `os.system()`, to avoid invoking a shell wrapper.
