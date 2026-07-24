## 2024-05-24 - [Command Injection]
**Vulnerability:** Command injection via child_process.exec in Next.js API routes bridging to Python scripts.
**Learning:** Concatenating unsanitized user inputs into child_process.exec can allow arbitrary shell command execution.
**Prevention:** Use child_process.execFile and pass arguments as an array rather than interpolating strings.
