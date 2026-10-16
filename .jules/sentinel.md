## 2026-10-16 - Command Injection via `child_process.exec()`
**Vulnerability:** Node.js backend routes (`storefront/src/app/api/admin/orders/route.js` and `checkout/route.js`) used `child_process.exec()` with string interpolation `exec(python order_fulfillment.py --mark-paid "${orderId}")`, leading to potential command injection via malicious `orderId`. Also found `shell=True` usages in Python's `subprocess.run` across `first_run_setup.py` and `launch_flow.py`.
**Learning:** Hardcoded commands with user-provided parameters combined using template literals are vulnerable.
**Prevention:** Always use `child_process.execFile()` instead of `exec()` and pass commands/arguments as an array. In Python, avoid `shell=True` when passing commands, use list of arguments instead.
