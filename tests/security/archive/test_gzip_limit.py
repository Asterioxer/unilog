import pytest
import gzip
from fastapi.testclient import TestClient
from api.app import app
from api.utils.decompression import decompress_gzip_safe, DecompressionLimitExceeded

def test_safe_gzip_decompression_limit():
    # 1. Test utility limit validation
    large_line = b"A" * 5000
    compressed = gzip.compress(large_line)
    
    # max_size 1000 is smaller than 5000, should raise limit exception
    with pytest.raises(DecompressionLimitExceeded):
        decompress_gzip_safe(compressed, max_size=1000, chunk_size=50)

    # max_size 10000 is larger, should succeed
    decompressed = decompress_gzip_safe(compressed, max_size=10000, chunk_size=50)
    assert decompressed == large_line

def test_upload_gzip_bomb_limits_http_413():
    # Build client
    client = TestClient(app)
    
    # Compress a payload that exceeds decompression threshold
    # Configure low max size via patching/mocking or environment variables
    # We can create a mock upload payload that exceeds 200MB uncompressed, 
    # but to make the test fast and safe, we can mock/patch UNILOG_MAX_DECOMPRESSED_SIZE to a low value.
    import api.routers.log as log_router
    orig_max = log_router.UNILOG_MAX_DECOMPRESSED_SIZE
    log_router.UNILOG_MAX_DECOMPRESSED_SIZE = 1000  # set low limit for test
    
    try:
        bomb_content = gzip.compress(b"A" * 1500)
        response = client.post(
            "/api/v1/upload",
            files={"file": ("bomb.gz", bomb_content, "application/gzip")},
            data={"format": "nginx"}
        )
        assert response.status_code == 413
        assert "Decompressed payload size limit exceeded" in response.json()["error"]["message"]
    finally:
        log_router.UNILOG_MAX_DECOMPRESSED_SIZE = orig_max
