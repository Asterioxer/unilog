"""
Upload a log file to the unilog API server.
Handles both synchronous and asynchronous (polling) upload tasks.
Usage: uv run python scripts/upload_log.py <path_to_file> [explicit_format]
"""
import sys
import time
import pathlib
import json

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "http://127.0.0.1:8002/api/v1"

if len(sys.argv) < 2:
    print("ERROR: Please specify the file path to upload.")
    print("Usage: uv run python scripts/upload_log.py <path_to_file> [explicit_format]")
    sys.exit(1)

file_path = pathlib.Path(sys.argv[1])
explicit_format = sys.argv[2] if len(sys.argv) > 2 else "auto"

if not file_path.exists():
    print(f"ERROR: File not found: {file_path}")
    sys.exit(1)

print(f"Uploading '{file_path.name}' ({file_path.stat().st_size:,} bytes)...")

# ── POST /upload ──────────────────────────────────────────────────────────────
upload_url = f"{API_BASE}/upload"
files = {"file": (file_path.name, file_path.open("rb"), "application/octet-stream")}
data = {"format": explicit_format}

try:
    resp = requests.post(upload_url, files=files, data=data, timeout=30)
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

if not resp.ok:
    print(f"\nHTTP {resp.status_code} Error:")
    try:
        err = resp.json()
        print(json.dumps(err, indent=2))
    except Exception:
        print(resp.text[:1000])
    sys.exit(1)

result = resp.json()
status = result.get("status")
task_id = result.get("task_id")
resolved_format = result.get("format")

# ── Handle Synchronous Result ─────────────────────────────────────────────────
if status == "completed":
    print("\n✓ Upload completed synchronously!")
    print(f"  Detected Format : {resolved_format}")
    records = result.get("records", [])
    print(f"  Records Parsed  : {len(records)}")
    if records:
        print("\nFirst parsed record example:")
        first = {k: v for k, v in records[0].items() if k != "raw"}
        print(f"  {first}")
    sys.exit(0)

# ── Handle Asynchronous Result ────────────────────────────────────────────────
if status == "processing" and task_id:
    print(f"\n⧗ File exceeds threshold. Task {task_id} queued for background parsing.")
    
    poll_url = f"{API_BASE}/tasks/{task_id}"
    while True:
        time.sleep(1)
        try:
            poll_resp = requests.get(poll_url, timeout=10)
            if not poll_resp.ok:
                print(f"Polling failed: HTTP {poll_resp.status_code}")
                break
            
            task_result = poll_resp.json()
            task_status = task_result.get("status")
            
            if task_status == "completed":
                print("\n✓ Background parsing completed!")
                task_res = task_result.get("result", {})
                print(f"  Detected Format : {task_res.get('format')}")
                recs = task_res.get("records", [])
                print(f"  Records Parsed  : {len(recs)}")
                if recs:
                    print("\nFirst parsed record example:")
                    first = {k: v for k, v in recs[0].items() if k != "raw"}
                    print(f"  {first}")
                break
            elif task_status == "failed":
                print(f"\n✗ Background parsing failed: {task_result.get('error')}")
                break
            else:
                print(".", end="", flush=True)
        except Exception as e:
            print(f"\nError while polling: {e}")
            break
