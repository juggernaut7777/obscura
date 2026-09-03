## 2024-05-14 - Command Injection in Interactive CLI Script
**Vulnerability:** User inputs (`prompt`, `script`, `refs`, `niche`, `brand`) were concatenated directly into shell commands via string formatting and executed using `os.system()` in `goal2_sourcing_engine/start_engine.py`, creating a critical command injection risk.
**Learning:** Passing unsanitized user inputs to `os.system()` allows execution of arbitrary shell commands if the inputs contain shell metacharacters like `;`, `&`, or `|`.
**Prevention:** Use `subprocess.run()` with a list of arguments (i.e., shell=False) instead of `os.system()`, so arguments are passed directly to the executable without shell evaluation.
