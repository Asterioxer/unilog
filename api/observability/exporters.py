from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from api.observability.metrics import REGISTRY
from api.observability.recorder import recorder

def generate_prometheus_metrics() -> bytes:
    """Generate Prometheus exposition text format bytes."""
    recorder.update_uptime()
    return generate_latest(REGISTRY)

PROMETHEUS_CONTENT_TYPE = CONTENT_TYPE_LATEST
