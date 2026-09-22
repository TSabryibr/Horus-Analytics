import asyncio
from playwright.async_api import async_playwright
import sys
import threading
import uvicorn
from api import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8123, log_level="error")

async def test_links():
    print("Starting server...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    await asyncio.sleep(2)

    print("Launching playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        async def on_response(response):
            if "scanner.txt" in response.url:
                print("==> SCANNER.TXT RESPONSE!")
                print("Headers:", response.headers)
                body = await response.text()
                print("Body Prefix:", body[:100])
                
        page.on("response", on_response)
        
        print("Goto /")
        await page.goto("http://127.0.0.1:8123/")
        await page.wait_for_timeout(2000)
        
        print("Clicking Scanner...")
        await page.evaluate("() => { const links = document.querySelectorAll('a'); for (let a of links) { if (a.href.includes('/scanner')) { a.click(); break; } } }")
        await page.wait_for_timeout(3000)
        
        await browser.close()
    print("Done")

if __name__ == "__main__":
    asyncio.run(test_links())
    sys.exit(0)
