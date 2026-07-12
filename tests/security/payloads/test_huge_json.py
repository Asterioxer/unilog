from fastapi.testclient import TestClient
from api.app import app

def test_pydantic_payload_limit_enforced_detect_and_stats():
    client = TestClient(app)
    
    # Detect endpoint limit (1 MB / 1,048,576 chars)
    # 1,100,000 characters exceeds the limit
    payload_detect = {"log_text": "A" * 1_100_000}
    response_detect = client.post("/api/v1/detect", json=payload_detect)
    assert response_detect.status_code == 422
    assert "at most 1048576 characters" in response_detect.text
    
    # Stats endpoint limit (10 MB / 10,485,760 chars)
    # 11,000,000 characters exceeds the limit
    payload_stats = {"log_text": "A" * 11_000_000, "format": "nginx"}
    response_stats = client.post("/api/v1/stats", json=payload_stats)
    assert response_stats.status_code == 422
    assert "at most 10485760 characters" in response_stats.text
