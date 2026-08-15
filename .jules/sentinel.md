## 2023-10-27 - Command Injection in Admin Routes
**Vulnerability:** Command injection found in `/api/admin/orders` via Node `child_process.exec`.
**Learning:** High-level APIs wrapping python execution incorrectly relied on building strings from untrusted JSON payloads to call `python script.py --arg "payload"`. This directly exposed the system shell.
**Prevention:** Always use `child_process.execFile` (or `spawn`) where you explicitly pass the binary as the first argument, and untrusted user inputs cleanly encapsulated within an argument array to prevent shell evaluation.
