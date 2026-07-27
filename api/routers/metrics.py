from fastapi import APIRouter, Response
from api.observability import generate_prometheus_metrics
from api.observability.exporters import PROMETHEUS_CONTENT_TYPE

router = APIRouter(tags=["Metrics"])

@router.get(
    "/metrics",
    summary="Prometheus Metrics Endpoint",
    description="Expose real-time operational telemetry, parsing latency, incident metrics, "
                "and system health scores in standard Prometheus exposition text format.",
    response_class=Response,
)
async def get_metrics():
    """Scrape endpoint for Prometheus server."""
    data = generate_prometheus_metrics()
    return Response(content=data, media_type=PROMETHEUS_CONTENT_TYPE)
