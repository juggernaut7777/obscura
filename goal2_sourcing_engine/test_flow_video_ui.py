import asyncio
import os
import sys

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow_bridge import FlowBridge

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
    safe_print("         OBSCURA VEO 3.1 VIDEO GENERATION TEST")
    safe_print("=" * 60)
    safe_print("\n[*] Starting Flow UI Bridge in visible mode (headless=False)...")
    safe_print("[!] A Chrome browser window will open shortly.")
    safe_print("[!] IMPORTANT: If you are not logged in, please log in within the next 60 seconds.")
    safe_print("=" * 60 + "\n")

    # Start bridge with headless=False to let the user see and log in
    bridge = FlowBridge(headless=False)
    await bridge.start()
    
    # Create a fresh worker page with video capture enabled
    page = await bridge._setup_page(capture_video=True)
    
    prompt = "A close-up slow pan of premium heavyweight streetwear hoodie embroidery details, luxury fashion lookbook style, cinematic lighting."
    
    try:
        safe_print(f"\n🚀 Launching Video Generation...")
        safe_print(f"   Prompt: '{prompt}'")
        safe_print(f"   Model: Veo 3.1 - Lite")
        safe_print(f"   Aspect Ratio: 16:9\n")
        
        # Pass the initialized page to generate_video
        results = await bridge.generate_video(
            prompt=prompt,
            model="Veo 3.1 - Lite",
            aspect_ratio="16:9",
            output_prefix="veo_test",
            page=page
        )
        
        if results:
            safe_print("\n" + "=" * 60)
            safe_print("✅ SUCCESS! Video generated and saved:")
            for r in results:
                safe_print(f"   - {r}")
            safe_print("=" * 60)
        else:
            safe_print("\n" + "=" * 60)
            safe_print("❌ FAILED: No video files were returned.")
            safe_print("=" * 60)
            
    except Exception as e:
        safe_print(f"\n❌ Error running video generation: {e}")
        import traceback
        traceback_print = traceback.format_exc()
        safe_print(traceback_print)
        
    finally:
        safe_print("\n[*] Closing browser session...")
        await bridge.close()
        safe_print("[OK] Done!")

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(main())
