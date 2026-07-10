"""
VTON Space Discovery — Multi-Space Scanner
============================================
Scans multiple known VTON Hugging Face Spaces to find which ones are
currently alive and responding, then inspects their API.
"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gradio_client import Client

# All known VTON-related HF Spaces to try
SPACES = [
    "yisol/IDM-VTON",
    "zhengchong/CatVTON",
    "Nymbo/Virtual-Try-On",
    "Kwai-Kolors/Kolors-Virtual-Try-On", 
    "levihsu/OOTDiffusion",
    "bingbangboom/flux_virtual_try_on",
    "xenova/virtual-try-on",
    "JEEZUSLOL/CatVTON",
]

print("=" * 60)
print("MULTI-SPACE VTON SCANNER")
print("=" * 60)

working_spaces = []

for space_id in SPACES:
    print(f"\nTesting: {space_id} ...", end=" ")
    try:
        client = Client(space_id, verbose=False)
        print("ONLINE!")
        working_spaces.append((space_id, client))
    except Exception as e:
        err = str(e)[:80]
        print(f"OFFLINE ({err})")

print("\n" + "=" * 60)
print(f"RESULTS: {len(working_spaces)}/{len(SPACES)} spaces are ONLINE")
print("=" * 60)

# Inspect API of each working space
for space_id, client in working_spaces:
    print(f"\n--- API for: {space_id} ---")
    try:
        client.view_api()
    except Exception as e:
        print(f"   Could not inspect API: {e}")

print("\nDone!")
