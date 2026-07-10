from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["Health"])

class HealthResponse(BaseModel):
    status: str = Field("healthy", description="API health status indicator")
    version: str = Field("0.1.0", description="Current unilog package version")

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API Health Check",
    description="Check the current status and version of the unilog REST service."
)
async def health_check():
    import unilog
    # Dynamically fetch version if defined, else use fallback
    version = getattr(unilog, "__version__", "0.1.0-beta")
    return {"status": "healthy", "version": version}
