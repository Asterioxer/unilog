"""Traffic built-in rules."""

from typing import List
from unilog.analytics.rules.models import Rule


def get_rules() -> List[Rule]:
    """Return traffic built-in rules."""
    return [
        Rule(
            id="traffic-burst",
            name="Traffic Burst Detection",
            category="traffic",
            severity="medium",
            metric_selector="traffic_burst.is_bursting",
            operator="eq",
            threshold=1.0,  # Coerced bool True -> 1.0
            description_template="Traffic burst anomaly detected (is_bursting={value})",
            weight=0.9,
        ),
        Rule(
            id="bandwidth-spike",
            name="Bandwidth Spike",
            category="traffic",
            severity="medium",
            metric_selector="bandwidth.bytes_per_second",
            operator="gt",
            threshold=10000.0,
            description_template="Bandwidth throughput {value} B/s exceeds {threshold} B/s",
            weight=0.8,
        ),
        Rule(
            id="endpoint-overload",
            name="Endpoint Overload",
            category="traffic",
            severity="medium",
            metric_selector="endpoint.top_endpoint_share",
            operator="gt",
            threshold=50.0,
            description_template="Top endpoint share {value}% exceeds {threshold}% of total traffic",
            weight=0.7,
        ),
    ]
