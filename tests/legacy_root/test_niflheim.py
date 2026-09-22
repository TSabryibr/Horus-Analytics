import requests
import json

url = "http://localhost:8200/api/stress-test"
payload = {"index": "EGX30"}
headers = {"Content-Type": "application/json"}

try:
    print(f"Testing {url} with payload {payload}...")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS")
        print(f"Crash Date: {data['data']['crash_date']}")
        print(f"Market Impact: {data['data']['market_impact']}%")
        print(f"Worst Affected Count: {len(data['data']['worst_affected'])}")
    else:
        print(f"❌ FAILED: {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")
