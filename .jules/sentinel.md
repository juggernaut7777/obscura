## 2024-05-15 - Hardcoded NGROK Auth Token
**Vulnerability:** A hardcoded production Ngrok authentication token was used as a fallback value for an environment variable.
**Learning:** Using `os.getenv` with a hardcoded sensitive string fallback defeats the purpose of environment variables and exposes secrets directly in source control.
**Prevention:** Always validate the presence of sensitive tokens dynamically. If a token is absent, securely handle the failure (e.g., abort the operation or log a generic error) without ever defining a default secret in the code.
