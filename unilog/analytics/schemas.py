"""Stable data contracts for the analytics subsystem."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class TrafficMetrics(BaseModel):
    """Log traffic volume metrics."""
    total_requests: int
    volume_bytes: int


class ErrorMetrics(BaseModel):
    """Log error rate and severity distribution metrics."""
    total_errors: int
    error_ratio: float
    errors_by_level: Dict[str, int]


class StatusMetrics(BaseModel):
    """HTTP status code distributions."""
    status_codes: Dict[str, int]
    status_categories: Dict[str, int]


class EndpointMetrics(BaseModel):
    """Request endpoint metrics mapping frequencies."""
    top_endpoints: List[Dict[str, Any]]


class MetricsBundle(BaseModel):
    """Canonical aggregate produced by the Metrics Engine."""
    model_config = ConfigDict(extra="forbid")

    traffic: Optional[TrafficMetrics] = None
    error: Optional[ErrorMetrics] = None
    status: Optional[StatusMetrics] = None
    endpoint: Optional[EndpointMetrics] = None