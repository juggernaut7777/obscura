import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent

def run_command(cmd, desc):
    print(f"[*] {desc}...")
    try:
        subprocess.run(cmd, check=True, shell=True)
        print(f"  [OK] {desc} successful.")
    except subprocess.CalledProcessError as e:
        print(f"  [FAIL] {desc} failed: {e}")
        return False
    return True

def main():
    print("=" * 50)
    print("GENERATION PIPELINE - FIRST RUN SETUP")
    print("=" * 50)

    # 1. Check Python version
    print(f"[*] Checking Python version: {sys.version.split()[0]}")

    # 2. Install requirements
    if not run_command("pip install -r requirements.txt", "Installing dependencies from requirements.txt"):
        print("[!] Stopping setup due to dependency failure.")
        return

    # 3. Install Playwright browsers
    if not run_command("python -m playwright install chromium", "Installing Playwright Chromium browser"):
        print("[!] Stopping setup due to Playwright installation failure.")
        return

    # 4. Check/Copy test products
    input_dir = BASE_DIR / "input_sourcing"
    test_dir = BASE_DIR / "test_products"
    
    input_dir.mkdir(exist_ok=True)
    
    # Check if input_sourcing is empty (except for _rejected) using os.scandir for better performance
    has_products = False
    try:
        with os.scandir(input_dir) as it:
            for entry in it:
                if entry.name != "_rejected" and entry.is_file():
                    has_products = True
                    break
    except OSError:
        pass
            
    if not has_products and test_dir.exists():
        print("[*] input_sourcing is empty. Copying test products...")
        import shutil
        try:
            with os.scandir(test_dir) as it:
                for entry in it:
                    if entry.is_file() and entry.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and entry.stat().st_size > 30000:
                        shutil.copy(entry.path, input_dir / entry.name)
                        print(f"  [+] Copied {entry.name}")
        except OSError:
            pass

    print("\n" + "=" * 50)
    print("SETUP COMPLETE. YOU ARE READY TO RUN.")
    print("=" * 50)
    print("\nNext Steps:")
    print("1. If using the Chrome Extension bridge, load the flow_extension folder in Chrome.")
    print("2. Run: python local_generation_worker.py")
    print("3. The script will open a browser. Log into Google within 5 minutes.")
    print("4. Sit back and watch it generate.")

if __name__ == "__main__":
    main()
