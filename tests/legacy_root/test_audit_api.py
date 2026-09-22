
import asyncio
import httpx
import json

async def test_audit():
    url = "http://127.0.0.1:8200/api/v1/ai/audit"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, timeout=40.0)
            print(f"Status: {resp.status_code}")
            print(f"Body: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_audit())
