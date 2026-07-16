"""Reliability built-in rules."""

from typing import List
from unilog.analytics.rules.models import Rule


def get_rules() -> List[Rule]:
    """Return reliability built-in rules."""
    return [
        Rule(
            id="high-error-ratio",
            name="High Error Ratio",
            category="reliability",
            severity="high",
            metric_selector="error.error_ratio",
            operator="gt",
            threshold=0.05,
            description_template="Error ratio {value} exceeds {threshold}",
            weight=1.0,
        ),
        Rule(
            id="high-5xx-rate",
            name="High HTTP 5xx Rate",
            category="reliability",
            severity="critical",
            metric_selector="status.http_5xx_rate",
            operator="gt",
            threshold=0.02,
            description_template="HTTP 5xx rate {value} exceeds {threshold}",
            weight=1.2,
        ),
    ]
