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
    http_5xx_rate: Optional[float] = None


class EndpointMetrics(BaseModel):
    """Request endpoint metrics mapping frequencies."""
    top_endpoints: List[Dict[str, Any]]
    top_endpoint_share: Optional[float] = None


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
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    avg_ms: Optional[float] = None
    min_ms: Optional[float] = None
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


class SessionRequest(BaseModel):
    """Normalized request item inside a reconstructed session."""
    timestamp: datetime
    method: str
    path: str
    status_code: int
    size: int
    journey_stage: str = "Other"


class Session(BaseModel):
    """Reconstructed user request session details."""
    session_id: str
    client_ip: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    request_count: int
    requests: List[SessionRequest]
    journey: List[str] = Field(default_factory=list)


class SessionMetrics(BaseModel):
    """Aggregate statistics representing user session behaviors."""
    average_session_duration_seconds: float
    bounce_rate: float
    pages_per_session: float
    requests_per_session: float
    active_sessions_count: int
    longest_session_duration_seconds: float
    sessions: List[Session] = Field(default_factory=list)
    possible_bot_count: int = 0
    credential_stuffing_count: int = 0
    endpoint_enumeration_count: int = 0


class JourneyMetrics(BaseModel):
    """funnel and page progression flow metrics."""
    journeys: List[List[str]] = Field(default_factory=list)
    stage_counts: Dict[str, int] = Field(default_factory=dict)
    funnel: Dict[str, int] = Field(default_factory=dict)


class BruteForceMetrics(BaseModel):
    """Brute force authentication attempt indicators."""
    failed_logins_per_ip: Dict[str, int] = Field(default_factory=dict)
    failure_ratio: float = 0.0
    lockout_candidates: List[str] = Field(default_factory=list)
    lockout_candidates_count: int = 0


class EnumerationMetrics(BaseModel):
    """directory and path scanning indicators."""
    distinct_endpoints_per_ip: Dict[str, int] = Field(default_factory=dict)
    error_404_ratio: float = 0.0


class BotMetrics(BaseModel):
    """Automated traffic and bot activity metrics."""
    requests_per_minute: Dict[str, float] = Field(default_factory=dict)
    missing_user_agent_count: int = 0
    headless_fingerprints_count: int = 0


class ScannerMetrics(BaseModel):
    """Security probes and standard vulnerabilities scanner hits."""
    scanned_ips: Dict[str, int] = Field(default_factory=dict)
    scanner_hits_count: int = 0


class InjectionMetrics(BaseModel):
    """Structured code injection attempt counts."""
    sql_injection_count: int = 0
    xss_injection_count: int = 0
    path_traversal_count: int = 0
    rce_cmd_injection_count: int = 0


class SecurityMetrics(BaseModel):
    """Canonical security analytics indicators summary."""
    brute_force: BruteForceMetrics
    enumeration: EnumerationMetrics
    bot_metrics: BotMetrics
    scanner_metrics: ScannerMetrics
    injection_metrics: InjectionMetrics


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
    session: Optional[SessionMetrics] = None
    journey: Optional[JourneyMetrics] = None
    security: Optional[SecurityMetrics] = None


class Insight(BaseModel):
    """Structured operation engine insight event."""
    id: str
    category: str  # e.g., "security", "performance", "traffic", "reliability"
    severity: str  # e.g., "low", "medium", "high", "critical"
    confidence: float
    timestamp: datetime
    description: str
    recommendation: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimelineEvent(BaseModel):
    """Chronological event footprint within an incident timeline."""
    timestamp: str
    event_type: str              # e.g., "scanner_probe", "bot_fingerprint", "threshold_breach"
    description: str
    severity: str                # e.g., "LOW", "MEDIUM", "HIGH", "CRITICAL"


class ThreatProfile(BaseModel):
    """Correlated threat actor and automated tool profiling."""
    suspected_tools: List[str] = Field(default_factory=list)   # e.g., ["Nikto", "Playwright (headless)"]
    capabilities: List[str] = Field(default_factory=list)      # e.g., ["Directory Discovery", "Admin Probing"]
    observed_targets: List[str] = Field(default_factory=list)  # e.g., ["/wp-admin", "/.env"]
    risk_level: str = "MEDIUM"                                 # e.g., "CRITICAL", "HIGH", "MEDIUM"


class Incident(BaseModel):
    """Correlated operational or security incident object aggregating multiple insights."""
    incident_id: str             # e.g., "INC-20260724-143206-7F2A"
    title: str                   # e.g., "Automated Reconnaissance Attack"
    severity: str                # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    confidence: float            # 0.0 - 1.0 (e.g., 0.98)
    confidence_evidence: List[str] = Field(default_factory=list) # e.g., ["✓ Known scanner UA", "✓ Sensitive probe paths"]
    affected_ips: List[str] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    threat_profile: Optional[ThreatProfile] = None
    sub_findings: List[str] = Field(default_factory=list)       # List of underlying Insight IDs
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)    # Actionable remediation checklist


class HealthSubScore(BaseModel):
    """Individual system domain health score metric."""
    score: int                   # 0 - 100
    status: str                  # "HEALTHY", "WARNING", "CRITICAL"
    summary: str


class SystemHealthScore(BaseModel):
    """Multi-dimensional environment health metric score matrix."""
    overall_score: int           # 0 - 100
    status: str                  # "HEALTHY", "WARNING", "CRITICAL"
    security: HealthSubScore
    reliability: HealthSubScore
    performance: HealthSubScore
    traffic: HealthSubScore


class AnalysisResult(BaseModel):
    """Canonical analysis result containing the metrics bundle, insights list, correlated incidents, and execution telemetry."""
    metrics: MetricsBundle
    insights: List[Insight] = Field(default_factory=list)
    incidents: List[Incident] = Field(default_factory=list)
    system_health: Optional[SystemHealthScore] = None
    metadata: PerformanceMetadata
    ruleset_version: str = "1.0"