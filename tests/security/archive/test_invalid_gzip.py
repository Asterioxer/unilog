import pytest
from fastapi.testclient import TestClient
from api.app import app
from api.utils.decompression import decompress_gzip_safe

def test_invalid_gzip_archive():
    # 1. Test utility raises ValueError on bad gzip header
    bad_data = b"NOT_A_GZIP_FILE_DATA_HEX_VALS"
    with pytest.raises(ValueError, match="Corrupted or invalid gzip archive"):
        decompress_gzip_safe(bad_data, max_size=1000)

def test_upload_corrupted_gzip_returns_http_400():
    client = TestClient(app)
    bad_data = b"NOT_A_GZIP_FILE_DATA_HEX_VALS"
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("corrupted.gz", bad_data, "application/gzip")},
        data={"format": "nginx"}
    )
    assert response.status_code == 400
    assert "Gzip decompression failed" in response.json()["error"]["message"]
