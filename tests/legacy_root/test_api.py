import urllib.request
import urllib.error
import json

try:
    with urllib.request.urlopen("http://127.0.0.1:8200/api/strategy") as response:
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    print(f"Body: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
