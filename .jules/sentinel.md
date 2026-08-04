## 2024-10-27 - Command Injection in API Route
**Vulnerability:** Command injection vulnerability in `storefront/src/app/api/checkout/route.js` due to using string interpolation with `child_process.exec` to execute a Python script with an interpolated file path.
**Learning:** `exec` spawns a shell, meaning string interpolation can be broken out of to execute arbitrary commands.
**Prevention:** Use `child_process.execFile` (or `spawn`) and pass arguments as an array. `execFile` does not spawn a shell by default, meaning arguments are safely passed to the executable without shell interpretation or expansion.
