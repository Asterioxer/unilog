from fastapi.testclient import TestClient
from api.app import app

def test_pydantic_payload_limit_enforced_parse():
    client = TestClient(app)
    
    # 11,000,000 characters exceeds the 10 MB (10,485,760 bytes) limit
    payload = {"log_text": "A" * 11_000_000, "format": "nginx"}
    response = client.post("/api/v1/parse", json=payload)
    
    # Pydantic triggers validation error returning HTTP 422
    assert response.status_code == 422
    assert "String should have at most 10485760 characters" in response.text
