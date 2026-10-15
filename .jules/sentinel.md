## 2024-10-11 - Command Injection in API Routes
**Vulnerability:** Command Injection vulnerabilities in Next.js API routes due to executing local Python scripts via `child_process.exec()` with unsanitized user input (e.g., `orderId`, `tracking`) interpolated directly into the command string.
**Learning:** In projects that delegate backend processing to local scripts via `child_process`, it's common to unsafely build command strings, introducing severe Remote Code Execution (RCE) risks if user input reaches the shell command.
**Prevention:** Always use `child_process.execFile()` or `child_process.spawn()` and pass commands and their arguments safely as an array instead of string interpolation with `child_process.exec()`.
