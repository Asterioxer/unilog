"""Security built-in rules."""

from typing import List
from unilog.analytics.rules.models import Rule


def get_rules() -> List[Rule]:
    """Return security built-in rules."""
    return [
        Rule(
            id="sec-bot-01",
            name="Suspected Bot Activity",
            category="security",
            severity="high",
            metric_selector="session.possible_bot_count",
            operator="gt",
            threshold=0.0,
            description_template="Suspected crawler or automated bot activity ({value} sessions detected)",
            weight=1.0,
        ),
        Rule(
            id="sec-cs-02",
            name="Credential Stuffing Attack suspected",
            category="security",
            severity="critical",
            metric_selector="session.credential_stuffing_count",
            operator="gt",
            threshold=0.0,
            description_template="High volume of authentication failure patterns ({value} sessions suspected)",
            weight=1.0,
        ),
        Rule(
            id="sec-enum-03",
            name="Directory Enumeration Attack suspected",
            category="security",
            severity="high",
            metric_selector="session.endpoint_enumeration_count",
            operator="gt",
            threshold=0.0,
            description_template="Abnormally high unique resource query footprint ({value} sessions suspected)",
            weight=1.0,
        ),
    ]
