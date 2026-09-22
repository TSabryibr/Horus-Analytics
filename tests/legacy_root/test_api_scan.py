import requests
import json
import time

url = "http://localhost:8200/api/scanner/start?index=ALL&intraday=false"
try:
    print(f"POSTing to {url}")
    r = requests.post(url)
    print("Status code:", r.status_code)
    print("Response:", r.text)
except Exception as e:
    print("Error:", e)

# Let's poll for a bit
for i in range(5):
    try:
        r2 = requests.get("http://localhost:8200/api/scanner/status")
        print("Status JSON:", r2.json())
    except Exception as e:
        pass
    time.sleep(1)
