## 2024-05-24 - Command Injection via child_process.exec()
**Vulnerability:** Command injection vulnerability in Next.js API routes (checkout, admin orders, admin upload) where unsanitized user inputs (`orderId`, `tracking`, etc.) were directly concatenated into shell commands executed by `child_process.exec()`.
**Learning:** Using `exec()` with string interpolation is inherently dangerous because it spawns a shell, allowing attackers to append malicious commands (e.g., using semicolons or backticks).
**Prevention:** Always use `child_process.execFile()` or `child_process.spawn()` and pass commands and their arguments safely as an array, which prevents the shell from interpreting the arguments as executable code.
