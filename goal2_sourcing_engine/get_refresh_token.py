import os
import json
import socket
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import httpx

# ==========================================
# Google OAuth 2.0 Configuration
# ==========================================
# You must create a Desktop App OAuth Client ID in Google Cloud Console
# (https://console.cloud.google.com/apis/credentials) and paste the IDs below.
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_CLIENT_SECRET_HERE")

# Scopes needed (OpenID Connect + Email + Profile usually works for ya29 tokens, 
# or specific scopes if required by the API).
SCOPES = [
    "openid", 
    "email", 
    "profile",
    # Add any other specific Google API scopes you need here
]

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "http://localhost:8080/callback"
TOKEN_FILE = "google_refresh_token.json"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == "/callback":
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if "code" in query_params:
                self.server.auth_code = query_params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authentication successful!</h1><p>You can close this window and return to the terminal.</p></body></html>")
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authentication failed!</h1><p>No code found in the callback URL.</p></body></html>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress logging
        pass


def run_local_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)
    httpd.auth_code = None
    httpd.timeout = 1 # Non-blocking check
    
    print(f"[*] Local server listening on port {port}...")
    while httpd.auth_code is None:
        httpd.handle_request()
        
    return httpd.auth_code


def main():
    print("==================================================")
    print("ONE-TIME GOOGLE OAUTH SETUP (HEADLESS BYPASS)")
    print("==================================================")
    
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        print("[!] Warning: You must set your actual GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET inside this script or via environment variables.")
        print("Please create an OAuth Client ID (Desktop App) in Google Cloud Console.")
        print("Press Enter to try anyway, or Ctrl+C to exit and configure.")
        input()
    
    # 1. Construct the authorization URL
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent" # Force consent to ensure we get a refresh token
    }
    
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
    
    print("\n[*] Opening your browser to authenticate with Google...")
    print(f"If the browser doesn't open automatically, please click this link:\n\n{auth_url}\n")
    
    webbrowser.open(auth_url)
    
    # 2. Start local server to receive the code
    auth_code = run_local_server(8080)
    print(f"\n[+] Received Authorization Code!")
    
    # 3. Exchange the code for a refresh token
    print("[*] Exchanging code for refresh token...")
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    
    response = httpx.post(TOKEN_URL, data=token_data)
    
    if response.status_code == 200:
        token_info = response.json()
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_info, f, indent=4)
            
        print(f"\n[✅] SUCCESS! Tokens saved to {TOKEN_FILE}.")
        print("You can now run Google Flow fully headlessly without Playwright!")
        print("Your script will automatically use the refresh_token to get fresh ya29.* access tokens.")
    else:
        print(f"\n[❌] Failed to get token: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    main()
