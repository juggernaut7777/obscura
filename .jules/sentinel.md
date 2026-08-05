
## 2024-05-18 - Command Injection via child_process.exec in Next.js API Routes
**Vulnerability:** Node.js backend endpoints in `storefront/src/app/api/*` were using `child_process.exec` and insecurely interpolating user input (like order IDs) into shell commands.
**Learning:** The frontend makes cross-boundary calls to the adjacent python backend. While easy, concatenating dynamic strings directly into `exec` introduces critical Command Injection risks on the server.
**Prevention:** Always use `child_process.execFile` (or `spawn`) with an argument array instead of string concatenation, explicitly isolating arguments from the command execution engine.
