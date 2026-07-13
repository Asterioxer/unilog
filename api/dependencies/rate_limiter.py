from slowapi import Limiter
from api.security.network import resolve_client_ip

# Initialize slowapi rate limiter utilizing client remote IP address
limiter = Limiter(key_func=resolve_client_ip)
