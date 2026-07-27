import re
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api.observability.metrics import REQUESTS_TOTAL
from api.observability.recorder import recorder

# Regex rules for endpoint path normalization to prevent Prometheus cardinality explosion
PATH_NORMALIZATION_PATTERNS = [
    (re.compile(r"^/api/v1/tasks/[^/]+$"), "/api/v1/tasks/{task_id}"),
]

def normalize_endpoint_path(path: str) -> str:
    """Normalize dynamic parametric path parameters to static label strings."""
    for pattern, replacement in PATH_NORMALIZATION_PATTERNS:
        if pattern.match(path):
            return replacement
    return path

class PrometheusMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware to measure HTTP request count, status codes, latency, and exceptions."""

    async def dispatch(self, request: Request, call_next) -> Response:
        exception_name = "none"
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            exception_name = exc.__class__.__name__
            raise exc
        finally:
            if request.url.path != "/metrics":
                endpoint = normalize_endpoint_path(request.url.path)
                REQUESTS_TOTAL.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status=str(status_code),
                    exception=exception_name,
                ).inc()
            recorder.update_uptime()
