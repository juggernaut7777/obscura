## 2026-06-05 - [Initial Setup]
**Vulnerability:** Sentinel instructions exist
**Learning:** Ready to protect
**Prevention:** Sentinel is active
## 2024-05-18 - [Fix Command Injection in API Routes]
**Vulnerability:** Node.js API routes were using `child_process.exec` to run python scripts with string interpolated arguments, allowing arbitrary command execution if an attacker manipulated inputs like `orderId` or checkout data.
**Learning:** Command Injection vulnerability exists when user-controlled inputs are passed directly to `exec` as part of a shell command string.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` with an array of arguments, rather than string concatenation in a shell.
