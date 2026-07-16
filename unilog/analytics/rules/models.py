"""Data models for the rule evaluation subsystem."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Rule(BaseModel):
    """Declarative threshold-based rule definition."""

    id: str
    name: str
    category: str  # "performance" | "traffic" | "reliability" | "security"
    severity: str  # "low" | "medium" | "high" | "critical"
    metric_selector: str  # dotted path into MetricsBundle, e.g. "latency.p99_ms"
    operator: str  # "gt" | "lt" | "gte" | "lte" | "eq"
    threshold: float
    description_template: str  # "P99 latency {value}ms exceeds {threshold}ms"
    weight: float = 1.0  # confidence weight multiplier
    enabled: bool = True


class RuleSet(BaseModel):
    """Ordered collection of rules with version metadata."""

    version: str = "1.0"
    rules: List[Rule] = Field(default_factory=list)


class RuleContext(BaseModel):
    """Immutable execution context supplied to every rule evaluation."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    window_minutes: int = Field(default=5, ge=1)
    analyzed_records: int = 0
    skipped_records: int = 0
    ruleset_version: str = "1.0"
    parser_metadata: Dict[str, Any] = Field(default_factory=dict)
