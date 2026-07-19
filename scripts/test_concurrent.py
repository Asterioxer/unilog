import asyncio
import httpx
import pathlib

API_BASE = "http://127.0.0.1:8002/api/v1"
log_path = pathlib.Path.home() / "Desktop" / "security_200.csv"

if not log_path.exists():
    print(f"Error: {log_path} not found")
    import sys
    sys.exit(1)

log_text = log_path.read_text(encoding="utf-8")

async def test_endpoint(client, name, url, payload):
    try:
        print(f"Sending to {name}...")
        resp = await client.post(url, json=payload, timeout=30.0)
        print(f"{name} response: {resp.status_code} ({len(resp.content)} bytes)")
        if resp.status_code != 200:
            print(f"{name} error: {resp.text[:500]}")
    except Exception as e:
        print(f"{name} exception: {e}")

async def main():
    async with httpx.AsyncClient() as client:
        tasks = [
            test_endpoint(client, "analyze", f"{API_BASE}/analyze", {
                "log_text": log_text,
                "format": "windows",
                "enable_rules": True,
                "window_minutes": 60
            }),
            test_endpoint(client, "detect", f"{API_BASE}/detect", {
                "log_text": log_text
            }),
            test_endpoint(client, "parse", f"{API_BASE}/parse", {
                "log_text": log_text,
                "format": "windows"
            })
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
