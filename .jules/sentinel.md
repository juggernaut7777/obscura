## 2024-05-24 - Command Injection in Interactive Prompts
**Vulnerability:** Interactive CLI prompts used `os.system` with string concatenation (`cmd = f'python compile_ugc_ad.py --prompt "{prompt}"'`), allowing command injection if user input contains shell metacharacters like `;`, `&`, or `$()`.
**Learning:** Even internal CLI tools are vulnerable if they build shell commands from raw inputs without escaping or safe execution.
**Prevention:** Always use `subprocess.run` with a command list (array of strings) instead of `os.system()` with `shell=True` when executing commands that include user inputs. Use `shlex.join` for safe logging of the constructed command.
