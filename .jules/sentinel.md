## 2024-05-24 - API Route Command Injection via child_process.exec
**Vulnerability:** Found arbitrary shell command injection in API routes when user input was concatenated into string arguments and passed to `child_process.exec`.
**Learning:** The project relies on Python scripts to perform backend actions instead of a traditional nodejs backend, meaning it passes arguments back and forth using `child_process`.
**Prevention:** Never use `child_process.exec` with untrusted input string interpolation; always use `child_process.execFile` or `spawn` and pass parameters in an arguments array to bypass the shell entirely.
