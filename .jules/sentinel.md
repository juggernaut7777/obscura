## 2024-05-24 - Command Injection in API routes
**Vulnerability:** Next.js API routes (`admin/orders/route.js`, `checkout/route.js`, `admin/upload/route.js`) used `child_process.exec()` with string interpolation for system commands. This allowed arbitrary command execution by an attacker supplying crafted inputs (e.g., `orderId`, `tracking`).
**Learning:** Using string interpolation with `exec` bypasses parameter isolation, treating input as literal bash execution commands, leading to severe command injection risks.
**Prevention:** Always use `child_process.execFile()` instead of `exec()` and pass external user input safely through the args array. This ensures inputs are treated as data, not executable code.
