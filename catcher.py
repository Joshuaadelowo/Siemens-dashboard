import json
from pathlib import Path

def run_catcher():
    print("[CATCHER] Checking for incoming text file...")
    
    incoming_path = Path(__file__).resolve().parent / "payload.txt"
    dashboard_path = Path(__file__).resolve().parent / "siemens_data.json"
    
    # 1. Check if the "received" file exists
    if not incoming_path.exists():
        print("[CATCHER] Error: No text file found!")
        return

    # 2. Read the received text file
    with open(incoming_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # 3. Write/update the local dashboard dataset
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(raw_text)

    print(f"[CATCHER] Success! Read data from '{incoming_path.name}' and updated '{dashboard_path.name}'.")

if __name__ == "__main__":
    run_catcher()