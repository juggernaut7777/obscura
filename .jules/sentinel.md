## 2024-09-24 - Node.js Command Injection Prevention
**Vulnerability:** Usage of child_process.exec() with string interpolation of unsanitized user inputs in API routes.
**Learning:** Hardcoding shell commands with string templates opens the door to arbitrary command execution on the host machine.
**Prevention:** Always use child_process.execFile() or child_process.spawn() and pass inputs safely as an array of arguments.
