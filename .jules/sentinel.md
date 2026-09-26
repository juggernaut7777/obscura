## 2024-05-01 - Prevent Command Injection with execFile
**Vulnerability:** Node.js `child_process.exec` used with string interpolated user input (e.g. `orderId`, `tracking`, `pipeline`) allowing command injection.
**Learning:** `exec` spawns a shell and parses the command string, evaluating shell metacharacters and injected commands.
**Prevention:** Always use `child_process.execFile` or `spawn` with an array of arguments, bypassing the shell and avoiding evaluation of untrusted input.
