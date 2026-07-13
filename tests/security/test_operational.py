import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from starlette.requests import Request

from api.app import app
from api.security.network import resolve_client_ip
import api.security.network as network
from api.schemas.task import TaskMetadata

client = TestClient(app, raise_server_exceptions=False)

def make_mock_request(client_host: str, headers: dict = None) -> Request:
    """Helper to construct a Starlette Request with custom client IP and headers."""
    scope = {
        "type": "http",
        "client": (client_host, 12345),
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    }
    return Request(scope)

# --- Error Safety Tests ---

def test_unexpected_internal_error_does_not_leak_traceback():
    """Verify that unhandled exceptions yield a generic error message to clients."""
    with patch("unilog.parse_string", side_effect=RuntimeError("internal database leak at /secret/path")):
        response = client.post(
            "/api/v1/parse",
            json={"log_text": "sample log message", "format": "nginx"}
        )
        # Even if the exception is internal, the catch-all handler or parse except block returns a safe 400 or 500 error
        assert response.status_code in (400, 500)
        data = response.json()
        assert "success" in data
        assert data["success"] is False
        error_msg = data["error"]["message"]
        # Confirm internal secrets, tracebacks, and raw exception text are obfuscated
        assert "leak" not in error_msg
        assert "/secret/path" not in error_msg
        assert "RuntimeError" not in error_msg

# --- Network Client IP Resolver Tests ---

def test_resolve_client_ip_no_trust_proxy():
    """Verify raw client host is returned when proxy trust is disabled."""
    with patch.object(network, "UNILOG_TRUST_PROXY", False):
        req = make_mock_request("192.168.1.50", {"X-Forwarded-For": "10.0.0.1, 10.0.0.2", "X-Real-IP": "10.0.0.1"})
        assert resolve_client_ip(req) == "192.168.1.50"

def test_resolve_client_ip_trusted_proxy_x_forwarded_for():
    """Verify the leftmost client IP is extracted from X-Forwarded-For header when proxy trust is enabled."""
    with patch.object(network, "UNILOG_TRUST_PROXY", True):
        with patch.object(network, "UNILOG_TRUSTED_PROXIES", []):
            req = make_mock_request("192.168.1.50", {"X-Forwarded-For": "198.51.100.42, 10.0.0.1"})
            assert resolve_client_ip(req) == "198.51.100.42"

def test_resolve_client_ip_trusted_proxy_x_real_ip():
    """Verify X-Real-IP fallback is used when proxy trust is enabled and X-Forwarded-For is absent."""
    with patch.object(network, "UNILOG_TRUST_PROXY", True):
        with patch.object(network, "UNILOG_TRUSTED_PROXIES", []):
            req = make_mock_request("192.168.1.50", {"X-Real-IP": "198.51.100.84"})
            assert resolve_client_ip(req) == "198.51.100.84"

def test_resolve_client_ip_trusted_proxy_whitelist_match():
    """Verify headers are trusted when the socket client matches the trusted proxy whitelist."""
    with patch.object(network, "UNILOG_TRUST_PROXY", True):
        with patch.object(network, "UNILOG_TRUSTED_PROXIES", ["192.168.1.50"]):
            req = make_mock_request("192.168.1.50", {"X-Real-IP": "198.51.100.99"})
            assert resolve_client_ip(req) == "198.51.100.99"

def test_resolve_client_ip_trusted_proxy_whitelist_mismatch():
    """Verify headers are ignored when the socket client does not match the trusted proxy whitelist."""
    with patch.object(network, "UNILOG_TRUST_PROXY", True):
        with patch.object(network, "UNILOG_TRUSTED_PROXIES", ["192.168.1.99"]):
            req = make_mock_request("192.168.1.50", {"X-Real-IP": "198.51.100.99"})
            assert resolve_client_ip(req) == "192.168.1.50"

# --- CORS & Security Headers Middleware Tests ---

def test_security_headers_are_present_on_responses():
    """Verify the SecurityHeadersMiddleware attaches appropriate headers on response."""
    response = client.get("/health")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "no-referrer"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
    assert "geolocation" in headers.get("Permissions-Policy", "")

# --- Diagnostics Route Tests ---

def test_diagnostics_system_info_route():
    """Verify that /system/info returns correct capability telemetry fields."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["analytics_enabled"] is True
    assert data["registered_parsers"] > 0
    assert data["registered_analyzers"] > 0
    assert isinstance(data["supported_formats"], list)
    assert "nginx" in data["supported_formats"]
    assert data["ruleset_version"] == "1.0"
    assert "python_version" in data
    assert "platform" in data

# --- Task Metadata Tests ---

def test_background_task_metadata_generation():
    """Verify task metadata properties are populated and persistent under TaskMetadata."""
    from api.services.background_tasks import tasks_db
    
    # 1. Manually insert a task with TaskMetadata to simulate upload endpoint setup
    metadata = TaskMetadata(
        created_at=time.time(),
        client_ip="192.168.2.100",
        owner_id=None
    )
    task_id = "test-task-metadata-uuid"
    tasks_db[task_id] = {
        "status": "processing",
        "filename": "server.log",
        "result": None,
        "error": None,
        "created_at": metadata.created_at,
        "metadata": metadata.model_dump()
    }
    
    # 2. Get status via endpoint
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert data["metadata"]["client_ip"] == "192.168.2.100"
    assert data["metadata"]["owner_id"] is None
    assert "created_at" in data["metadata"]
