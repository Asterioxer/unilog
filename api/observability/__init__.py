"""
unilog Observability Subsystem
Modular telemetry, metrics, exposition exporters, and middleware.
"""
from api.observability.metrics import REGISTRY
from api.observability.recorder import recorder
from api.observability.middleware import PrometheusMiddleware
from api.observability.exporters import generate_prometheus_metrics

__all__ = [
    "REGISTRY",
    "recorder",
    "PrometheusMiddleware",
    "generate_prometheus_metrics",
]
