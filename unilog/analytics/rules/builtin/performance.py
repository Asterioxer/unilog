"""Performance built-in rules."""

from typing import List
from unilog.analytics.rules.models import Rule


def get_rules() -> List[Rule]:
    """Return performance built-in rules."""
    return [
        Rule(
            id="high-latency-p99",
            name="High P99 Latency",
            category="performance",
            severity="high",
            metric_selector="latency.p99_ms",
            operator="gt",
            threshold=500.0,
            description_template="P99 latency {value}ms exceeds {threshold}ms",
            weight=1.0,
        ),
        Rule(
            id="high-latency-p95",
            name="High P95 Latency",
            category="performance",
            severity="medium",
            metric_selector="latency.p95_ms",
            operator="gt",
            threshold=300.0,
            description_template="P95 latency {value}ms exceeds {threshold}ms",
            weight=0.8,
        ),
    ]
