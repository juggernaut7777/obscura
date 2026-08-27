## 2025-05-18 - Fix Command Injection Vulnerability
**Vulnerability:** A Command Injection vulnerability in `goal2_sourcing_engine/start_engine.py` where user input (`prompt`, `script`, `refs`) was interpolated into a string and executed by `os.system`.
**Learning:** `os.system` with string interpolation of user input allows a malicious user to supply command line operators (like `&&` or `;`) and run arbitrary shell commands on the host machine.
**Prevention:** Avoid `os.system(cmd)` and use `subprocess.run(cmd_list)` to securely spawn the process by passing the command and its arguments as a list. Use `shlex.join(cmd_list)` to safely print the constructed command instead of building the command string manually.
