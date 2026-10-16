
## 2024-05-18 - Prevent Command Injection via execFile
**Vulnerability:** Command injection vulnerability in the admin orders API endpoint via unsanitized `orderId`, `tracking`, and `pipeline` parameters.
**Learning:** `exec` evaluates arguments using the shell, making it susceptible to command injection when combined with user input.
**Prevention:** Always use `execFile` or `spawn` and pass arguments as an array to avoid shell evaluation.
