from fastapi import Request, Depends, HTTPException

class AuthenticationBackend:
    """Interface abstraction for authentication strategy backends."""

    def authenticate(self, request: Request) -> bool:
        """Authenticate request incoming variables. Returns True on success, False otherwise."""
        raise NotImplementedError("Authentication backends must implement authenticate.")

class NoAuthBackend(AuthenticationBackend):
    """Fallback default authenticator allowing all requests."""

    def authenticate(self, request: Request) -> bool:
        return True

# Dependency injection helpers
def get_auth_backend() -> AuthenticationBackend:
    """Return the active AuthenticationBackend instance."""
    return NoAuthBackend()

def verify_auth(
    request: Request,
    backend: AuthenticationBackend = Depends(get_auth_backend)
) -> None:
    """Validate request authentication against the active strategy."""
    if not backend.authenticate(request):
        raise HTTPException(
            status_code=401,
            detail="Authentication verification failed."
        )
