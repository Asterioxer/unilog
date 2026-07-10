from fastapi import APIRouter
from pydantic import BaseModel, Field
import unilog

router = APIRouter(tags=["Health"])

class HealthResponse(BaseModel):
    status: str = Field("healthy", description="API health check status indicator")
    version: str = Field("0.2.0-alpha", description="Current unilog package version")

class LiveResponse(BaseModel):
    status: str = Field("live", description="Liveness check status indicator")

class ReadyResponse(BaseModel):
    status: str = Field("ready", description="Readiness check status indicator")

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API Health Check",
    description="Check the current status and version of the unilog REST service."
)
async def health_check():
    version = getattr(unilog, "__version__", "0.2.0-alpha")
    return {"status": "healthy", "version": version}

@router.get(
    "/live",
    response_model=LiveResponse,
    summary="Liveness Check",
    description="Indicate if the application container is running."
)
async def live_check():
    return {"status": "live"}

@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Readiness Check",
    description="Indicate if the application is ready to accept traffic."
)
async def ready_check():
    # Verify built-in parsers are registered
    from unilog.registry import list_formats
    formats = list_formats()
    if not formats:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Services are not ready: no parsers registered.")
    return {"status": "ready"}
