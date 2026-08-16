
## 2025-02-23 - Command Injection in Node.js child_process.exec
**Vulnerability:** User input from API requests (like `orderId`, `tracking`, etc.) was being directly interpolated into a string and executed via `child_process.exec()`. An attacker could pass a crafted string (e.g., `"123"; rm -rf /`) to execute arbitrary shell commands.
**Learning:** Using `exec` with string interpolation of unsanitized input is highly dangerous and allows command injection.
**Prevention:** Always use `execFile` or `spawn` instead of `exec`, and pass arguments as an array so they are not evaluated by a shell.
