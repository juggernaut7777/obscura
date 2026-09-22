## 2026-09-22 - Fix Command Injection in Admin API
**Vulnerability:** Node.js API route vulnerable to command injection via `child_process.exec()` where user inputs (`orderId`, `tracking`, etc.) were directly interpolated into a shell string without sanitization.
**Learning:** Using `exec()` with template literals makes parameter injection trivial to exploit.
**Prevention:** Always use `child_process.execFile()` (or `spawn()`) to safely pass command arguments as an array, eliminating shell interpretation.
