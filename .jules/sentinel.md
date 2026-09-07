## 2024-09-07 - Command Injection in CLI Menus
**Vulnerability:** Found `os.system()` using string concatenation (`cmd += ...`) with direct user input (`input().strip()`) in `start_engine.py`. This allowed an attacker to inject and execute arbitrary shell commands.
**Learning:** Even internal or local CLI menus must treat user input as untrusted. Developer shortcuts using `os.system` with f-strings for executing secondary Python scripts is a common and dangerous pattern.
**Prevention:** Never use `os.system` or `subprocess.run(shell=True)` when incorporating user input. Always use `subprocess.run()` and pass the command and arguments as a list. Use `shlex.join(cmd_list)` if the exact command needs to be printed for logging purposes.
