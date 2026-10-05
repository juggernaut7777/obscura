## 2024-05-18 - Command Injection in Admin Orders API
**Vulnerability:** User input parameters (`orderId`, `tracking`, `pipeline`) were directly concatenated into a shell command string and passed to `child_process.exec()`.
**Learning:** Using `child_process.exec()` with string interpolation is a critical command injection risk, as unsanitized inputs allow execution of arbitrary shell commands.
**Prevention:** Always use `child_process.execFile()` or `child_process.spawn()` with arguments passed safely as an array instead of concatenating a command string.
