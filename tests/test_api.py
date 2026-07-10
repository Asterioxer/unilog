import json
import gzip
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_api_formats():
    response = client.post("/formats")
    assert response.status_code == 200
    data = response.json()
    assert "formats" in data
    # Verify nginx format details
    nginx_fmt = next(f for f in data["formats"] if f["name"] == "nginx")
    assert nginx_fmt["priority"] > 0
    assert ".log" in nginx_fmt["supported_extensions"]

def test_api_parse():
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
    response = client.post("/parse", json={"log_text": log_text, "format": "nginx"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["records"][0]["source_ip"] == "127.0.0.1"

    response_fail = client.post("/parse", json={"log_text": log_text, "format": "invalid_format"})
    assert response_fail.status_code == 400

def test_api_detect():
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
    response = client.post("/detect", json={"log_text": log_text})
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "nginx"
    assert data["confidence"] > 0.6
    assert len(data["rankings"]) > 0

def test_api_stats():
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
    response = client.post("/stats", json={"log_text": log_text, "format": "nginx"})
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "nginx"
    assert data["total_lines"] == 1
    assert data["bytes_transferred"] == 1043

def test_api_stream():
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043\n192.168.1.1 - - [10/Jul/2026:20:54:00 +0530] "POST /login HTTP/1.1" 401 230'
    response = client.post("/stream", json={"log_text": log_text, "format": "nginx"})
    assert response.status_code == 200
    # Stream returns lines of JSON records
    lines = [json.loads(line) for line in response.iter_lines() if line.strip()]
    assert len(lines) == 2
    assert lines[0]["source_ip"] == "127.0.0.1"
    assert lines[1]["source_ip"] == "192.168.1.1"

def test_api_upload_synchronous():
    # Test uploading a small valid nginx log file
    log_content = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043\n'
    response = client.post(
        "/upload",
        files={"file": ("test.log", log_content, "text/plain")},
        data={"format": "nginx"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert len(data["records"]) == 1
    assert data["records"][0]["source_ip"] == "127.0.0.1"

def test_api_upload_invalid_extension():
    response = client.post(
        "/upload",
        files={"file": ("test.exe", "binary content", "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]

def test_api_upload_empty():
    response = client.post(
        "/upload",
        files={"file": ("test.log", "", "text/plain")}
    )
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]

def test_api_upload_too_large():
    # Size limit is 100MB, let's mock it by sending too large content (or just check status code 413)
    content = b" " * (100 * 1024 * 1024 + 10)
    response = client.post(
        "/upload",
        files={"file": ("test.log", content, "text/plain")}
    )
    assert response.status_code == 413

def test_api_upload_background_processing():
    # File larger than 1MB threshold
    log_content = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043\n'
    padding = "\n" * (1 * 1024 * 1024 + 100)
    large_payload = (padding + log_content).encode("utf-8")
    
    response = client.post(
        "/upload",
        files={"file": ("test_large.log", large_payload, "text/plain")},
        data={"format": "nginx"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["task_id"] is not None
    
    task_id = data["task_id"]
    
    # Query task status (it runs synchronously within the TestClient environment context)
    response_task = client.get(f"/tasks/{task_id}")
    assert response_task.status_code == 200
    task_data = response_task.json()
    assert task_data["status"] in ("completed", "processing")
    if task_data["status"] == "completed":
        assert task_data["result"]["total"] == 1
        assert task_data["result"]["records"][0]["source_ip"] == "127.0.0.1"

def test_api_upload_gzip():
    log_content = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043\n'
    gzip_payload = gzip.compress(log_content.encode("utf-8"))
    
    response = client.post(
        "/upload",
        files={"file": ("test.log.gz", gzip_payload, "application/gzip")},
        data={"format": "nginx"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["records"][0]["source_ip"] == "127.0.0.1"

def test_api_get_task_not_found():
    response = client.get("/tasks/non_existent_task_id")
    assert response.status_code == 404

def test_api_upload_background_failed_gzip():
    # Corrupted gzip header and larger than 1MB to trigger background flow
    corrupt_content = b"\x1f\x8b" + b"broken gzip stream" * 80000
    response = client.post(
        "/upload",
        files={"file": ("test_corrupt.gz", corrupt_content, "application/gzip")},
        data={"format": "nginx"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    
    task_id = data["task_id"]
    response_task = client.get(f"/tasks/{task_id}")
    assert response_task.status_code == 200
    task_data = response_task.json()
    assert task_data["status"] == "failed"
    assert "Decompression failed" in task_data["error"] or "gzip" in task_data["error"].lower()

def test_api_upload_corrupt_sync_gzip():
    # Small corrupted gzip to trigger sync decompression failure
    corrupt_content = b"\x1f\x8b" + b"broken gzip stream"
    response = client.post(
        "/upload",
        files={"file": ("test_corrupt_small.gz", corrupt_content, "application/gzip")},
        data={"format": "nginx"}
    )
    assert response.status_code == 400
    assert "Parsing failed" in response.json()["detail"] or "decompression" in response.json()["detail"].lower()

def test_process_file_task_general_exception():
    from api.services.background_tasks import process_file_task, get_task_status
    # Passing None as content to cause general exception in background task
    process_file_task("dummy_task_id", None, "test.log", "nginx") # type: ignore
    status_info = get_task_status("dummy_task_id")
    assert status_info["status"] == "failed"
    assert status_info["error"] is not None

def test_api_invalid_formats():
    # Test invalid format for stats
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
    response = client.post("/stats", json={"log_text": log_text, "format": "invalid_format"})
    assert response.status_code == 400
    
    # Test invalid format for stream
    response_stream = client.post("/stream", json={"log_text": log_text, "format": "invalid_format"})
    assert response_stream.status_code == 400

    # Test invalid format for upload
    response_upload = client.post(
        "/upload",
        files={"file": ("test.log", log_text, "text/plain")},
        data={"format": "invalid_format"}
    )
    assert response_upload.status_code == 400

def test_api_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "unilog REST API"
    assert "/parse" in schema["paths"]
    assert "/detect" in schema["paths"]
    assert "/stats" in schema["paths"]
    assert "/formats" in schema["paths"]
    assert "/stream" in schema["paths"]
    assert "/upload" in schema["paths"]

