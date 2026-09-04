## 2024-09-04 - Fix Command Injection in Child Process Execution
**Vulnerability:** Shell command injection vulnerability in `child_process.exec()` via string concatenation.
**Learning:** Using `exec()` with unvalidated user input exposes the system to command execution attacks.
**Prevention:** Always use `child_process.execFile()` or `spawn()` and pass arguments as an array instead of string concatenation, preventing shell evaluation of arguments.
