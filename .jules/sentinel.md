## 2024-03-XX - Command Injection via User Input String Formatting
**Vulnerability:** User inputs (prompt, script, refs) were directly interpolated into a command string and passed to `os.system()`, allowing for arbitrary shell command execution.
**Learning:** Command string concatenation combined with `os.system()` creates a critical command injection vector if any part of the string originates from unsanitized user input.
**Prevention:** Never use `os.system()` with user input. Always use `subprocess.run()` with a list of arguments so arguments are safely handled and not evaluated by the shell.
