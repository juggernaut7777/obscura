## 2024-05-19 - Fix Command Injection in Child Process
**Vulnerability:** Command injection vulnerability in Node.js API endpoints using `child_process.exec` with unvalidated user input.
**Learning:** Using template literals to inject user input directly into shell commands via `exec` allows attackers to append arbitrary shell commands.
**Prevention:** Always use `child_process.execFile` or `spawn` instead of `exec`, passing user inputs as an array of arguments to avoid shell execution.
