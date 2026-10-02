## 2024-10-02 - Fix Command Injection via child_process.exec
**Vulnerability:** Command injection vulnerability in storefront API routes where user input (order IDs, tracking info) was passed directly into shell commands via `child_process.exec()` and string interpolation.
**Learning:** Using `child_process.exec()` with string templates creates a severe security risk if input contains shell metacharacters. Even seemingly benign strings like "tracking" or "orderId" can be manipulated to execute arbitrary commands if unvalidated.
**Prevention:** Always use `child_process.execFile()` or `child_process.spawn()` instead of `exec()`. Pass commands and arguments safely as an array instead of concatenating them into a single shell string.
