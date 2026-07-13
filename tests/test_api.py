import json
import gzip
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app, raise_server_exceptions=False)

def test_api_health_checks():
    # 1. /health check
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    
    # 2. /live check
    response_live = client.get("/live")
    assert response_live.status_code == 200
    assert response_live.json() == {"status": "live"}
    
    # 3. /ready check
    response_ready = client.get("/ready")
    assert response_ready.status_code == 200
    assert response_ready.json() == {"status": "ready"}

def test_api_middleware_headers():
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"

def test_api_formats():
    response = client.post("/api/v1/formats")
    assert response.status_code == 200
    data = response.json()
    assert "formats" in data
    nginx_fmt = next(f for f in data["formats"] if f["name"] == "nginx")
    assert nginx_fmt["priority"] > 0

def test_api_parse():
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
    response = client.post("/api/v1/parse", json={"log_text": log_text, "format": "nginx"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["records"][0]["source_ip"] == "127.0.0.1"

    # Test error model layout on validation/exception failure
    response_fail = client.post("/api/v1/parse", json={"log_text": log_text, "format": "invalid_format"})
    assert response_fail.status_code == 400
    data_fail = response_fail.json()
    assert data_fail["success"] is False
    assert data_fail["error"]["code"] == "INVALID_LOG"
    assert "Invalid format requested" in data_fail["error"]["message"]

def test_api_detect():
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
    response = client.post("/api/v1/detect", json={"log_text": log_text})
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "nginx"
    assert data["confidence"] > 0.6

def test_api_stats():
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
    response = client.post("/api/v1/stats", json={"log_text": log_text, "format": "nginx"})
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "nginx"
    assert data["bytes_transferred"] == 1043

def test_api_stream():
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
    response = client.post("/api/v1/stream", json={"log_text": log_text, "format": "nginx"})
    assert response.status_code == 200
    lines = [json.loads(line) for line in response.iter_lines() if line.strip()]
    assert len(lines) == 1
    assert lines[0]["source_ip"] == "127.0.0.1"

def test_api_upload_synchronous():
    log_content = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043\n'
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.log", log_content, "text/plain")},
        data={"format": "nginx"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert len(data["records"]) == 1

def test_api_upload_invalid_extension():
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.exe", "binary content", "application/octet-stream")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_LOG"

def test_api_upload_empty():
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.log", "", "text/plain")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False

def test_api_upload_too_large():
    content = b" " * (100 * 1024 * 1024 + 10)
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.log", content, "text/plain")}
    )
    assert response.status_code == 413
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FILE_TOO_LARGE"

def test_api_upload_background_processing():
    log_content = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043\n'
    padding = "\n" * (1 * 1024 * 1024 + 100)
    large_payload = (padding + log_content).encode("utf-8")
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test_large.log", large_payload, "text/plain")},
        data={"format": "nginx"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    
    task_id = data["task_id"]
    response_task = client.get(f"/api/v1/tasks/{task_id}")
    assert response_task.status_code == 200
    task_data = response_task.json()
    assert task_data["status"] in ("completed", "processing")

def test_api_upload_gzip():
    log_content = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043\n'
    gzip_payload = gzip.compress(log_content.encode("utf-8"))
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.log.gz", gzip_payload, "application/gzip")},
        data={"format": "nginx"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

def test_api_get_task_not_found():
    response = client.get("/api/v1/tasks/non_existent_task_id")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"

def test_api_upload_background_failed_gzip():
    corrupt_content = b"\x1f\x8b" + b"broken gzip stream" * 80000
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test_corrupt.gz", corrupt_content, "application/gzip")},
        data={"format": "nginx"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    
    task_id = data["task_id"]
    response_task = client.get(f"/api/v1/tasks/{task_id}")
    assert response_task.status_code == 200
    task_data = response_task.json()
    assert task_data["status"] == "failed"

def test_api_upload_corrupt_sync_gzip():
    corrupt_content = b"\x1f\x8b" + b"broken gzip stream"
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test_corrupt_small.gz", corrupt_content, "application/gzip")},
        data={"format": "nginx"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False

def test_process_file_task_general_exception():
    from api.services.background_tasks import process_file_task, get_task_status
    process_file_task("dummy_task_id2", None, "test.log", "nginx") # type: ignore
    status_info = get_task_status("dummy_task_id2")
    assert status_info["status"] == "failed"

def test_api_invalid_formats():
    log_text = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
    response = client.post("/api/v1/stats", json={"log_text": log_text, "format": "invalid_format"})
    assert response.status_code == 400
    
    response_stream = client.post("/api/v1/stream", json={"log_text": log_text, "format": "invalid_format"})
    assert response_stream.status_code == 400

    response_upload = client.post(
        "/api/v1/upload",
        files={"file": ("test.log", log_text, "text/plain")},
        data={"format": "invalid_format"}
    )
    assert response_upload.status_code == 400

def test_api_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "unilog REST API"
    assert "/api/v1/parse" in schema["paths"]
    assert "/api/v1/detect" in schema["paths"]
    assert "/api/v1/stats" in schema["paths"]
    assert "/api/v1/formats" in schema["paths"]
    assert "/api/v1/stream" in schema["paths"]
    assert "/api/v1/upload" in schema["paths"]

def test_api_rate_limiter():
    limit_exceeded = False
    for _ in range(105):
        response = client.post("/api/v1/formats")
        if response.status_code == 429:
            limit_exceeded = True
            data = response.json()
            assert data["success"] is False
            assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
            break
    assert limit_exceeded is True

@app.get("/trigger_internal_error")
async def trigger_internal_error():
    raise ValueError("Unexpected database failure")

def test_api_global_exception_handler():
    response = client.get("/trigger_internal_error")
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"


def test_api_ready_check_failure(monkeypatch):
    import unilog.registry
    monkeypatch.setattr(unilog.registry, "list_formats", lambda: [])
    response = client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert "no parsers registered" in data["error"]["message"]

