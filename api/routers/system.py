import sys
from fastapi import APIRouter
import unilog
from unilog.analytics.registry import list_analyzers

router = APIRouter(tags=["System"])

@router.get("/system/info", summary="Get system capability telemetry")
async def get_system_info():
    """Expose system configuration capabilities and version telemetry."""
    fmts = unilog.list_formats()
    supported_formats = [f["name"] for f in fmts]
    
    return {
        "version": "0.4.0-alpha.2",
        "analytics_enabled": True,
        "registered_parsers": len(supported_formats),
        "registered_analyzers": len(list_analyzers()),
        "supported_formats": supported_formats,
        "ruleset_version": "1.0",
        "python_version": sys.version,
        "platform": sys.platform
    }
