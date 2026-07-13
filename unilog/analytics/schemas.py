"""Stable data contracts for the analytics subsystem."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


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


# --- Release 3 Performance Schemas ---

class IPMetric(BaseModel):
    """Metadata representing requests volume from a source IP address."""
    ip: str
    requests: int


class SizeDistribution(BaseModel):
    """Statistical summary of requests/responses body payload sizes."""
    count: int
    average: Optional[float] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    p50: Optional[float] = None
    p95: Optional[float] = None
    histogram: Dict[str, int] = Field(default_factory=dict)


class EndpointBandwidth(BaseModel):
    """Aggregate bandwidth metrics for a specific endpoint path."""
    endpoint: str
    bytes_sent: int
    percentage: float  # Percentage of total transferred bytes


class BurstWindow(BaseModel):
    """Details representing a traffic burst spike event windows."""
    timestamp: datetime
    requests_per_second: float
    ratio: float


class AnalyzerInfo(BaseModel):
    """Version and registration metadata of an execution module."""
    name: str
    version: str


class PerformanceMetadata(BaseModel):
    """Telemetry diagnostic metadata summarizing engine compile operations."""
    analyzed_records: int
    skipped_records: int
    missing_latency_fields: int
    execution_time_ms: float
    analyzers: List[AnalyzerInfo]


class LatencyMetrics(BaseModel):
    """Detailed percentiles and averages of request processing duration latency."""
    p50_ms: Optional[float] = None
    p90_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    avg_ms: Optional[float] = None
    max_ms: Optional[float] = None


class DistributionMetrics(BaseModel):
    """Host client requests count and body sizes distribution metrics."""
    top_ips: List[IPMetric]
    request_sizes: SizeDistribution
    response_sizes: SizeDistribution


class BandwidthMetrics(BaseModel):
    """Overall transfer bandwidth speeds and top endpoints metadata."""
    total_bytes_sent: int
    bytes_per_second: float
    top_bandwidth_endpoints: List[EndpointBandwidth]


class TrafficBurstMetrics(BaseModel):
    """Traffic burst anomalies metrics and burst timeline occurrences."""
    average_rps: float
    peak_rps: float
    burst_ratio: float
    burst_windows: List[BurstWindow]
    is_bursting: bool


class MetricsBundle(BaseModel):
    """Canonical aggregate produced by the Metrics Engine."""
    model_config = ConfigDict(extra="forbid")

    traffic: Optional[TrafficMetrics] = None
    error: Optional[ErrorMetrics] = None
    status: Optional[StatusMetrics] = None
    endpoint: Optional[EndpointMetrics] = None
    latency: Optional[LatencyMetrics] = None
    distribution: Optional[DistributionMetrics] = None
    bandwidth: Optional[BandwidthMetrics] = None
    traffic_burst: Optional[TrafficBurstMetrics] = None


class AnalysisResult(BaseModel):
    """Canonical analysis result containing the metrics bundle and execution telemetry."""
    metrics: MetricsBundle
    metadata: PerformanceMetadata