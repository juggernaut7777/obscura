import asyncio
import os
import sys
import socket
import subprocess
import time

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generation_router import GenerationRouter

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
    """Safely print messages on Windows to avoid UnicodeEncodeErrors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            encoding = sys.stdout.encoding or 'utf-8'
            print(msg.encode('utf-8', errors='replace').decode(encoding, errors='replace'))
        except Exception:
            print("[Print Error] Unable to encode output print message.")

async def main():
    safe_print("=" * 60)
    safe_print("      OBSCURA SILENT VEO 3.1 VIDEO GENERATION TEST")
    safe_print("=" * 60)
    
    bridge_port = 9877
    
    # 1. Ensure the Token Bridge is running
    if is_port_active("127.0.0.1", bridge_port):
        safe_print(f"[OK] Token Bridge is active on port {bridge_port}.")
    else:
        safe_print(f"[*] Starting Token Bridge (all_in_one_bridge.py) on port {bridge_port}...")
        bridge_script = os.path.join(os.path.dirname(__file__), "all_in_one_bridge.py")
        try:
            subprocess.Popen(
                [sys.executable, "-u", bridge_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.path.dirname(__file__),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            safe_print("[+] Token Bridge launched in background console.")
            safe_print("[*] Waiting 3 seconds for bridge to initialize...")
            await asyncio.sleep(3.0)
        except Exception as e:
            safe_print(f"[!] Failed to launch Token Bridge: {e}")
            return

    # 2. Instruct the user to ensure Chrome is open with Flow
    safe_print("\n[!] Please make sure:")
    safe_print("    1. Your personal Chrome is open.")
    safe_print("    2. The 'OBSCURA' Chrome extension is loaded.")
    safe_print("    3. You have a tab open to Google Flow: https://labs.google/fx/tools/flow")
    safe_print("    (This allows the extension to automatically grab tokens securely without opening any new windows)\n")
    
    prompt = "A slow cinematic dolly zoom of a model walking down a foggy Tokyo alley wearing a luxury black streetwear hoodie, moody cinematic lighting."
    
    try:
        router = GenerationRouter()
        
        # force_engine="flow" routes to Direct Flow HTTP API
        safe_print("🚀 Launching Direct Flow API Video Generation...")
        safe_print(f"   Prompt: '{prompt}'")
        safe_print(f"   Engine: flow (Direct HTTP API)\n")
        
        results = await router.generate_video(
            prompt=prompt,
            aspect="16:9",
            output_prefix="silent_veo",
            force_engine="flow"
        )
        
        if results:
            safe_print("\n" + "=" * 60)
            safe_print("✅ SUCCESS! Video generated and downloaded:")
            for r in results:
                safe_print(f"   - {r}")
            safe_print("=" * 60)
        else:
            safe_print("\n" + "=" * 60)
            safe_print("❌ FAILED: Direct API returned no video results.")
            safe_print("   Ensure your Google Flow tab is active in Chrome and logged in.")
            safe_print("=" * 60)
            
    except Exception as e:
        safe_print(f"\n❌ Error during generation: {e}")
        import traceback
        safe_print(traceback.format_exc())

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(main())
