## 2026-06-05 - Fix Command Injection in Next.js Admin API
**Vulnerability:** Unsanitized user inputs (orderId, tracking, pipeline) were being passed via string interpolation to `child_process.exec()` in the Next.js API routes when calling Python fulfillment scripts.
**Learning:** This architectural pattern (Next.js acting as a bridge executing local Python scripts via child_process) creates an inherently high risk for command injection if inputs aren't meticulously handled.
**Prevention:** Never use `exec()` with string interpolation for external scripts. Always use `execFile()` or `spawn()` and pass the command and its arguments as an explicit array, which bypasses the shell and prevents malicious parameter escaping.
