## 2024-05-18 - Fix Command Injection in start_engine.py
**Vulnerability:** Command injection vulnerability via `os.system` using string interpolation with user input in `goal2_sourcing_engine/start_engine.py`.
**Learning:** Using `os.system` with f-strings allows attackers to execute arbitrary shell commands (e.g. by passing `"; rm -rf /"` as input).
**Prevention:** Always use `subprocess.run` and pass commands and arguments safely as a list so they are not evaluated by a shell.
