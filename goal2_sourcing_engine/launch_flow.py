import os
import sys
import socket
import subprocess
import time

def is_port_active(host: str, port: int) -> bool:
    """Check if a port is open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect((host, port))
            return True
    except:
        return False

def safe_print(msg: str):
    try:
        print(msg)
    except:
        pass

def main():
    safe_print("=" * 60)
    safe_print("              OBSCURA FLOW AUTOMATOR & LAUNCHER")
    safe_print("=" * 60)
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    debug_port = 9222
    bridge_port = 9877
    
    # 1. Start the Token Bridge if not already running
    if is_port_active("127.0.0.1", bridge_port):
        safe_print(f"[OK] Token Bridge is already running on port {bridge_port}.")
    else:
        safe_print(f"[*] Starting Token Bridge (all_in_one_bridge.py) on port {bridge_port}...")
        bridge_script = os.path.join(os.path.dirname(__file__), "all_in_one_bridge.py")
        
        # Launch token bridge as a background process
        try:
            subprocess.Popen(
                [sys.executable, "-u", bridge_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.path.dirname(__file__),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            safe_print("[+] Token Bridge launched in a new console window!")
        except Exception as e:
            safe_print(f"[!] Failed to launch Token Bridge: {e}")
            
    # 2. Start Chrome with remote debugging on port 9222 using the user's default/personal profile
    if is_port_active("127.0.0.1", debug_port):
        safe_print(f"[OK] Chrome Remote Debugger is already active on port {debug_port}.")
    else:
        # Check if chrome.exe is currently running
        is_running = False
        try:
            if sys.platform == "win32":
                tasks = subprocess.check_output("tasklist", shell=True).decode("utf-8", errors="ignore")
                if "chrome.exe" in tasks.lower():
                    is_running = True
        except:
            pass

        if is_running:
            safe_print("\n⚠️  Chrome is currently running without the remote debugging port enabled.")
            safe_print("   We need to restart it to enable port 9222 for your logged-in profiles.")
            safe_print("   Closing running Chrome windows...")
            try:
                # Force close all chrome processes
                subprocess.run("taskkill /F /IM chrome.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2.0)
            except:
                pass

        safe_print(f"[*] Launching your main Chrome profile with remote debugging port {debug_port}...")
        flow_url = "https://labs.google/fx/tools/flow"
        
        chrome_cmd = [
            chrome_path,
            f"--remote-debugging-port={debug_port}",
            "--remote-allow-origins=*",
            "--profile-directory=Profile 4",
            flow_url
        ]
        
        try:
            subprocess.Popen(chrome_cmd)
            safe_print("[+] Main Chrome launched successfully with your active accounts!")
            safe_print("   Please keep that window open so the pipeline can communicate with it.")
        except Exception as e:
            safe_print(f"[!] Failed to launch Chrome: {e}")
            
    safe_print("=" * 60)
    
if __name__ == "__main__":
    main()
