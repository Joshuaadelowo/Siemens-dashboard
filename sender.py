import json
from pathlib import Path
from datetime import datetime

def run_sender():
    print("[SENDER] Simulating data capture...")
    
    # 1. Dummy payload representing your fetched Siemens data
    payload_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Payload successfully generated",
        "sample_reading": 125525.0
    }
    
    # 2. Convert payload to text
    text_content = json.dumps(payload_data, indent=4)
    
    # 3. Save to a text file (simulating an outgoing email attachment)
    outgoing_path = Path(__file__).resolve().parent / "payload.txt"
    with open(outgoing_path, "w", encoding="utf-8") as f:
        f.write(text_content)
        
    print(f"[SENDER] Text file generated at: {outgoing_path}")

if __name__ == "__main__":
    run_sender()