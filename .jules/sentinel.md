## 2024-09-27 - Mitigate Command Injection in Next.js API Routes
**Vulnerability:** Command injection vulnerabilities existed in multiple Next.js API routes where user-provided input was interpolated directly into shell commands passed to `child_process.exec()`.
**Learning:** Using `exec()` with string interpolation allows attackers to append arbitrary shell commands. `execFile()` safely escapes arguments by passing them as an array directly to the executable.
**Prevention:** Always use `child_process.execFile()` or `child_process.spawn()` with an array of arguments when executing external binaries or scripts, avoiding `child_process.exec()` entirely for dynamic commands.
