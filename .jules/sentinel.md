## 2025-05-24 - Fixed Command Injection in Admin API
**Vulnerability:** Unsanitized user inputs (`orderId`, `tracking`, `pipeline`) were directly interpolated into a shell string executed via `child_process.exec()`.
**Learning:** Using `exec()` with string interpolation in API route handlers creates a command injection risk when passing user data to background python scripts.
**Prevention:** Always use `child_process.execFile()` and pass commands and arguments safely as an array instead of interpolating them into a string.
