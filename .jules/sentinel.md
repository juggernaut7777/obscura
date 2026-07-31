## 2025-02-14 - Fix Command Injection in interactive scripts
**Vulnerability:** Found critical command injection vulnerabilities in interactive shell scripts (`start_engine.py`) using `os.system` with f-string formatted arguments constructed directly from `input()` calls.
**Learning:** `os.system` runs commands through a sub-shell and does no escaping. Untrusted input parsed from interactive CLI workflows like input() can easily inject extra commands if concatenated directly or unquoted.
**Prevention:** Always use `subprocess.run` with a list of arguments instead of string interpolation via `os.system` or `subprocess.Popen(shell=True)`. Space-separated variable inputs should be parsed using string `.split()` to properly segregate list arguments.
