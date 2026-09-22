
import json
import os
import requests


BASE_URL = os.getenv("HORUS_API_BASE_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT_SEC = 10


def _fetch_json(path: str):
    url = f"{BASE_URL}{path}"
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SEC)
    response.raise_for_status()
    return response.json()


def verify_dashboard():
    print(f"API Base URL: {BASE_URL}")
    print("Testing /api/portfolio/metrics...")
    try:
        metrics = _fetch_json("/api/portfolio/metrics")
        print(f"Metrics: {json.dumps(metrics, indent=2)}")

        if metrics.get("total_pnl") != 0 or metrics.get("unrealized_pnl") != 0:
            print("[OK] Metrics are non-zero.")
        else:
            print("[WARN] Metrics are still zero. Check if data lake has prices for open tickers.")

    except requests.exceptions.RequestException as exc:
        print(f"[FAIL] Error fetching metrics: {exc}")
        print("[INFO] Ensure backend is running before this check.")
        return
    except Exception as exc:
        print(f"[FAIL] Error decoding metrics: {exc}")
        return

    print("\nTesting /api/portfolio/curve...")
    try:
        curve = _fetch_json("/api/portfolio/curve")
        points = len(curve) if isinstance(curve, list) else 0
        print(f"Curve Data Point Count: {points}")
        if points >= 2:
            print(f"[OK] Curve has baseline and current point. First: {curve[0]}, Last: {curve[-1]}")
        else:
            print("[WARN] Curve is too short.")
    except requests.exceptions.RequestException as exc:
        print(f"[FAIL] Error fetching curve: {exc}")
    except Exception as exc:
        print(f"[FAIL] Error decoding curve: {exc}")


if __name__ == "__main__":
    verify_dashboard()
