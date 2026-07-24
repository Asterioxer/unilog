"""API request/response schemas for the /api/v1/analyze endpoint."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from api.config import UNILOG_MAX_STATS_TEXT


class AnalyzeRequest(BaseModel):
    log_text: str = Field(
        ...,
        max_length=UNILOG_MAX_STATS_TEXT,
        description="Raw log lines to analyze",
    )
    format: Optional[str] = Field(
        None,
        description="Explicit parser format (auto-detect if omitted)",
    )
    window_minutes: int = Field(
        5,
        ge=1,
        description="Analysis window duration in minutes",
    )
    enable_rules: bool = Field(
        True,
        description="Whether to evaluate the built-in rule set against the metrics",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "log_text": '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043',
                "format": None,
                "window_minutes": 5,
                "enable_rules": True,
            }
        }
    }


class InsightResponse(BaseModel):
    id: str
    category: str
    severity: str
    confidence: float
    description: str
    recommendation: str
    evidence: Dict[str, Any] = Field(default_factory=dict)


class AnalyzeMetadata(BaseModel):
    analyzed_records: int
    skipped_records: int
    missing_latency_fields: int
    execution_time_ms: float
    analyzers: List[Dict[str, str]]


class AnalyzeResponse(BaseModel):
    metrics: Dict[str, Any] = Field(
        ...,
        description="Compiled MetricsBundle containing all analyzer outputs",
    )
    insights: List[InsightResponse] = Field(
        default_factory=list,
        description="Triggered rule insights (empty if enable_rules=False)",
    )
    incidents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Correlated SOC incidents aggregating triggered insights",
    )
    system_health: Optional[Dict[str, Any]] = Field(
        None,
        description="Multi-dimensional environment system health matrix (0-100 score)",
    )
    metadata: AnalyzeMetadata
    ruleset_version: str = "1.0"

