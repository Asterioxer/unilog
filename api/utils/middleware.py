import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Read configurable Content Security Policy
UNILOG_CSP = os.environ.get(
    "UNILOG_CSP",
    "default-src 'self'; frame-ancestors 'none';"
)

# Relaxed CSP for Swagger/ReDoc UI routes — they require inline scripts and CDN fonts/assets
_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
    "font-src 'self' fonts.gstatic.com; "
    "img-src 'self' data: fastapi.tiangolo.com cdn.jsdelivr.net; "
    "frame-ancestors 'none';"
)

_DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces strict, production-ready security headers on every response."""

    async def dispatch(self, request: Request, call_next):
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        response = await call_next(request)


        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Use relaxed CSP for Swagger/ReDoc UI, strict CSP everywhere else
        if request.url.path in _DOCS_PATHS or request.url.path.startswith("/docs"):
            response.headers["Content-Security-Policy"] = _DOCS_CSP
        else:
            response.headers["Content-Security-Policy"] = UNILOG_CSP

        return response
