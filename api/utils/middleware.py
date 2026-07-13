import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Read configurable Content Security Policy
UNILOG_CSP = os.environ.get(
    "UNILOG_CSP",
    "default-src 'self'; frame-ancestors 'none';"
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces strict, production-ready security headers on every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = UNILOG_CSP
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
