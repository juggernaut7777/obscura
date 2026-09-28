## 2025-02-28 - Command Injection via Node.js child_process.exec

**Vulnerability:** User inputs (`orderId`, `tracking`, `pipeline`) were being concatenated directly into shell commands via `child_process.exec` in the backend API routes (`/api/admin/orders`, `/api/checkout`). This allows an attacker to append arbitrary shell commands to the input and execute them on the server.
**Learning:** Using string interpolation with `exec` creates a shell context where special characters are evaluated. Node.js backend delegating to Python scripts must be careful not to trust inputs.
**Prevention:** Always use `child_process.execFile` or `child_process.spawn` instead of `exec`, and pass command arguments securely as an array, preventing the shell from interpreting the inputs as separate commands.
