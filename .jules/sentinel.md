## 2024-05-15 - Hardcoded Ngrok Secret Token
**Vulnerability:** Found a hardcoded production Ngrok secret auth token in `all_in_one_bridge.py` (`"3CcirWo5RC3C0VxrZCPpxShwdhf_2iMxjnr1D9SGtwq54Gta3"`).
**Learning:** Hardcoding sensitive tokens within code files, even as a default value fallback, is a critical risk and violates security boundaries, potentially allowing unauthorized users to establish Ngrok tunnels under our account.
**Prevention:** Always rely strictly on environmental variables (`os.getenv("NGROK_AUTH_TOKEN")`) with no fallback defaults, and safely check for the presence of the environment variable before proceeding. If absent, gracefully exit or throw an error.
