from fastapi.testclient import TestClient
from api.app import app

def test_upload_file_size_exceeded():
    client = TestClient(app)
    
    # Configure low max file size for test
    import api.routers.log as log_router
    orig_max = log_router.UNILOG_MAX_FILE_SIZE
    log_router.UNILOG_MAX_FILE_SIZE = 100  # Set limit to 100 bytes
    
    try:
        large_content = b"A" * 150
        response = client.post(
            "/api/v1/upload",
            files={"file": ("large.log", large_content, "text/plain")},
            data={"format": "nginx"}
        )
        assert response.status_code == 413
        assert "exceeds maximum limit" in response.json()["error"]["message"]
    finally:
        log_router.UNILOG_MAX_FILE_SIZE = orig_max
