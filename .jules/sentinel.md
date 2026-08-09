## 2024-05-18 - [CRITICAL] Command Injection in start_engine.py
**Vulnerability:** Untrusted user input (`prompt`, `script`, `refs`) concatenated into a shell command and executed using `os.system(cmd)` inside `goal2_sourcing_engine/start_engine.py`.
**Learning:** Using string interpolation with `os.system` creates a critical command injection vector where a user can enter `; malicious_command` as a prompt, executing arbitrary code.
**Prevention:** Always use `subprocess.run` with a list of arguments instead of string interpolation for shell commands to ensure shell metacharacters are safely escaped.
