import os
import json
import asyncio
import httpx

async def get_headless_token():
    cookie_file = "google_cookies.json"
    if not os.path.exists(cookie_file):
        print("[!] google_cookies.json not found.")
        return None
        
    with open(cookie_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    cookies_dict = {}
    for c in data.get("cookies", []):
        cookies_dict[c["name"]] = c["value"]
        
    if "__Secure-next-auth.session-token" not in cookies_dict:
        print("[!] Session token not found in cookies.")
        return None

    try:
        print("[*] Fetching headless auth session...")
        async with httpx.AsyncClient(cookies=cookies_dict, timeout=10.0) as client:
            resp = await client.get("https://labs.google/fx/api/auth/session")
            if resp.status_code == 200:
                auth_data = resp.json()
                access_token = auth_data.get("access_token")
                if access_token:
                    print(f"[+] Successfully extracted headlessly! Token starts with: {access_token[:15]}...")
                    return access_token
                else:
                    print("[!] No access_token in response:", auth_data)
            else:
                print(f"[!] Failed to fetch session. Status: {resp.status_code}")
                print(resp.text[:200])
    except Exception as e:
        print(f"[!] Error: {e}")
        
    return None

if __name__ == "__main__":
    asyncio.run(get_headless_token())
