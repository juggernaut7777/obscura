## 2025-02-28 - [Command Injection via exec]
**Vulnerability:** Command Injection
**Learning:** Using `child_process.exec()` with string interpolation of user input allows an attacker to append arbitrary shell commands.
**Prevention:** Always use `child_process.execFile()` or `child_process.spawn()` and pass arguments as an array instead of string concatenation.
