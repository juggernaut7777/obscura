## 2025-02-12 - Command Injection via child_process.exec
**Vulnerability:** The 'storefront' application used child_process.exec with string interpolated inputs, allowing arbitrary command execution if an attacker controlled the 'orderId', 'tracking', or 'pipeline' values.
**Learning:** Executing Python scripts from a Node.js backend using shell-evaluated exec makes it trivial to inject commands via unescaped string concatenation.
**Prevention:** Always use child_process.execFile (or spawn) and pass arguments as an array. This ensures the operating system treats inputs strictly as arguments, rather than executable shell commands.
