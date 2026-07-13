import os
import ipaddress
from fastapi import Request

# Environment variables
UNILOG_TRUST_PROXY = os.environ.get("UNILOG_TRUST_PROXY", "false").lower() == "true"
UNILOG_TRUSTED_PROXIES = [
    ip.strip() for ip in os.environ.get("UNILOG_TRUSTED_PROXIES", "").split(",") if ip.strip()
]

def resolve_client_ip(request: Request) -> str:
    """Resolve client IP addressing direct, trusted reverse proxy configurations."""
    client_host = request.client.host if request.client else "127.0.0.1"
    
    if not UNILOG_TRUST_PROXY:
        return client_host

    # If trusted proxy whitelist is specified, verify socket sender is trusted
    if UNILOG_TRUSTED_PROXIES and client_host not in UNILOG_TRUSTED_PROXIES:
        return client_host

    # Check X-Forwarded-For
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        parts = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if parts:
            return parts[0]

    # Check X-Real-IP
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()

    return client_host

def is_private_ip(ip: str) -> bool:
    """Check if an IP address resides in a private subnetwork range."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False

def is_loopback(ip: str) -> bool:
    """Check if an IP address is a loopback address."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_loopback
    except ValueError:
        return False
