
import requests
import time

API_URL = "http://127.0.0.1:8200"

def test_start():
    print(f"Triggering Optimization on {API_URL}...")
    try:
        res = requests.post(f"{API_URL}/api/strategy/start", params={"index": "EGX30"})
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
        
        if res.status_code == 200:
            print("Monitoring Status...")
            for i in range(10):
                time.sleep(2)
                stat = requests.get(f"{API_URL}/api/strategy/status").json()
                print(f"Iter {i}: Status={stat['status']} | Progress={stat['progress']}% | Found={stat['found']}")
                if stat['status'] in ['COMPLETED', 'ERROR']:
                    print("Finished!")
                    if stat['status'] == 'ERROR':
                        print(f"ERROR DETAILS: {stat['error']}")
                    break
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    test_start()
