## 2024-05-15 - Command Injection via child_process.exec()
**Vulnerability:** Next.js backend API routes (e.g., checkout, admin orders) construct shell commands using string interpolation with unsanitized user inputs (e.g., `orderId`, `tracking`, `pipeline`) and execute them via `child_process.exec()`.
**Learning:** `exec` spawns a shell and parses the command string, making it vulnerable to shell injection if any part of the string is derived from unvalidated user input (e.g., `orderId="123; rm -rf /"`).
**Prevention:** Always use `child_process.execFile()` or `child_process.spawn()` with an array of arguments, instead of string interpolation with `exec()`, when handling external inputs.
