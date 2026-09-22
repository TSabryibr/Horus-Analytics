import requests
import sys

def verify():
    base_url = "http://127.0.0.1:8000"
    print(f"🔍 [Phase 7] Verifying Data Engine at {base_url}...")
    
    # 1. Check History (Parquet)
    try:
        resp = requests.get(f"{base_url}/api/data/ticker/COMI")
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 0 and 'Close' in data[0]:
                print(f"✅ [History] Success! Loaded {len(data)} daily bars for COMI.")
            else:
                print(f"❌ [History] Data empty or malformed: {str(data)[:100]}")
        else:
            print(f"❌ [History] API Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ [History] Connection Failed: {e}")

    # 2. Check Intraday (Parquet)
    try:
        resp = requests.get(f"{base_url}/api/intraday/COMI")
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 0 and 'Close' in data[0]:
                print(f"✅ [Intraday] Success! Loaded {len(data)} intraday bars for COMI.")
            else:
                print(f"❌ [Intraday] Data empty or malformed: {str(data)[:100]}")
        else:
            print(f"❌ [Intraday] API Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ [Intraday] Connection Failed: {e}")

if __name__ == "__main__":
    verify()
