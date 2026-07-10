from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize slowapi rate limiter utilizing client remote IP address
limiter = Limiter(key_func=get_remote_address)
