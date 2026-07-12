from fastapi.testclient import TestClient
from api.app import app

def test_empty_file_upload_rejected():
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("empty.log", b"", "text/plain")},
        data={"format": "nginx"}
    )
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["error"]["message"]
