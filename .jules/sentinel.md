## 2024-05-18 - Fix Command Injection Vulnerability

**Vulnerability:** Found a Command Injection vulnerability in `goal2_sourcing_engine/start_engine.py` where raw unsanitized user inputs for UGC Video Ad compilation were executed directly via `os.system`.
**Learning:** `os.system` using f-strings with raw user inputs is highly vulnerable to command injection. Unsanitized strings allow users to inject arbitrary shell commands, posing a critical security risk.
**Prevention:** Replaced `os.system` with Python's `subprocess.run`, using a rigorous argument list (`cmd_list`), and safely parsed any variable-length space-separated inputs via `shlex.split()`. This completely eliminates shell injection as arguments are passed securely without invoking the shell interpreter.
