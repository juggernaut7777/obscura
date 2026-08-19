## 2024-05-30 - Command Injection in User Prompts
**Vulnerability:** Found `os.system` executing shell commands directly concatenated with user inputs (`prompt`, `script`, `refs`) in the start menu.
**Learning:** String interpolation with user inputs into shell commands allows arbitrary command execution.
**Prevention:** Use `subprocess.run` with commands passed as a safely tokenized list instead of invoking a shell.
