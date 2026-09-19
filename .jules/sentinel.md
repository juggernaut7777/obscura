
## 2024-03-21 - [Command Injection via exec]
**Vulnerability:** Node.js API endpoints in `storefront` used `child_process.exec` with string-interpolated shell commands to invoke python scripts, which can lead to command injection.
**Learning:** String interpolation combined with `exec` invokes a shell where user-controlled variables might break out of their quotes and execute arbitrary commands.
**Prevention:** Use `child_process.execFile` instead of `exec`, passing command-line arguments as an array so they are safely handled directly by the OS without invoking a shell.
