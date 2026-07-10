import os
import shutil
import sys

# Safe print for Windows
def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

# Directories relative to script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_SOURCING_DIR = os.path.join(BASE_DIR, "input_sourcing")
REVIEW_PENDING_DIR = os.path.join(BASE_DIR, "review_pending")
MANUAL_CURATION_DIR = os.path.join(BASE_DIR, "MANUAL_CURATION")
OUTPUT_READY_FOR_SALE_DIR = os.path.join(BASE_DIR, "OUTPUT_READY_FOR_SALE")
HISTORY_FILE = os.path.join(BASE_DIR, "data", "scraped_albums_history.json")

def clear_directory(path: str, keep_dir: bool = True):
    if not os.path.exists(path):
        return
    safe_print(f"[*] Cleaning: {path}")
    count_files = 0
    count_dirs = 0
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                count_dirs += 1
            else:
                os.remove(item_path)
                count_files += 1
        except Exception as e:
            safe_print(f"  [!] Failed to delete {item}: {e}")
            
    safe_print(f"  [OK] Removed {count_dirs} directories and {count_files} files.")

def main():
    wipe_history = "--wipe-history" in sys.argv
    wipe_curation = "--all" in sys.argv or "--wipe-curation" in sys.argv
    wipe_output = "--all" in sys.argv or "--wipe-output" in sys.argv
    
    safe_print("==================================================")
    safe_print("OBSCURA PIPELINE WAREHOUSE CLEANER & RESET UTILITY")
    safe_print("==================================================")
    
    # 1. Clear staging files
    clear_directory(INPUT_SOURCING_DIR)
    clear_directory(REVIEW_PENDING_DIR)
    
    # 2. Clear curated files if requested
    if wipe_curation:
        clear_directory(MANUAL_CURATION_DIR)
    else:
        safe_print("[*] Preserving MANUAL_CURATION/ (use --wipe-curation or --all to clear)")

    # 3. Clear output files if requested
    if wipe_output:
        clear_directory(OUTPUT_READY_FOR_SALE_DIR)
    else:
        safe_print("[*] Preserving OUTPUT_READY_FOR_SALE/ (use --wipe-output or --all to clear)")

    # 4. Wipe persistent scraped history if requested
    if wipe_history:
        if os.path.exists(HISTORY_FILE):
            try:
                os.remove(HISTORY_FILE)
                safe_print("[*] Deleted permanent scraped albums history file.")
            except Exception as e:
                safe_print(f"[!] Failed to delete history file: {e}")
    else:
        safe_print("[*] Preserving permanent history. Scraper will not duplicate past items.")

    safe_print("\n[+] Reset process completed! Sourcing engine ready to scrape freshly.")

if __name__ == "__main__":
    main()
