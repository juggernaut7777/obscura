## 2024-10-10 - Command Injection in Node.js API Routes via child_process.exec
**Vulnerability:** The Node.js Next.js backend uses `child_process.exec()` with user inputs unsafely interpolated into the command string.
**Learning:** Using template literals for shell execution exposes the application to command injection because unsanitized inputs (like `orderId`, `tracking`, etc.) can include shell metacharacters (e.g., `;`, `&`, `|`).
**Prevention:** Always use `child_process.execFile()` or `spawn()` passing arguments as an array instead of string concatenation/interpolation.
