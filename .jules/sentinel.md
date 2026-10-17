## 2026-10-17 - Fix Node.js Command Injection
**Vulnerability:** Found child_process.exec() used with string interpolation for handling API inputs in storefront routes.
**Learning:** exec() runs in a shell, allowing attackers to append commands if inputs aren't perfectly sanitized. execFile() avoids the shell and passes arguments directly, preventing injection.
**Prevention:** Always use child_process.execFile() or child_process.spawn() and pass commands and their arguments safely as an array.
