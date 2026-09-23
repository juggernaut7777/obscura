## 2024-05-15 - Command Injection in Next.js API Routes via Python Execution
**Vulnerability:** Node.js backend routes used child_process.exec() with string interpolation to pass user inputs to Python scripts.
**Learning:** Next.js API routes often bridge to Python for processing. Using exec() instead of execFile() creates a dangerous shell injection vector if user inputs (like order IDs) are not escaped.
**Prevention:** Always use child_process.execFile() (or spawn()) and pass command arguments safely as an array to avoid shell interpretation.
