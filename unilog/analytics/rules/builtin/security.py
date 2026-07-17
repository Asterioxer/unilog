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
            metric_selector="security.bot_metrics.headless_fingerprints_count",
            operator="gt",
            threshold=0.0,
            description_template="Headless automated browser client footprint detected ({value} headless hits)",
            weight=1.0,
        ),
        Rule(
            id="sec-cs-02",
            name="Credential Stuffing Attack",
            category="security",
            severity="critical",
            metric_selector="security.brute_force.lockout_candidates_count",
            operator="gt",
            threshold=0.0,
            description_template="Credential stuffing candidates identified ({value} accounts/IPs exceeding failed login threshold)",
            weight=1.0,
        ),
        Rule(
            id="sec-enum-03",
            name="Directory Enumeration Scan",
            category="security",
            severity="high",
            metric_selector="security.enumeration.error_404_ratio",
            operator="gt",
            threshold=10.0,
            description_template="Abnormally high 404 response footprint ({value}% of total traffic)",
            weight=1.0,
        ),
        Rule(
            id="sec-scan-04",
            name="Vulnerability Scanning Probe",
            category="security",
            severity="high",
            metric_selector="security.scanner_metrics.scanner_hits_count",
            operator="gt",
            threshold=0.0,
            description_template="Probes trying to locate admin panels, backups, or configs ({value} hits detected)",
            weight=1.0,
        ),
        Rule(
            id="sec-inj-05",
            name="SQL Injection Attempt",
            category="security",
            severity="critical",
            metric_selector="security.injection_metrics.sql_injection_count",
            operator="gt",
            threshold=0.0,
            description_template="SQL query signature injection payloads detected in request URI/body ({value} hits)",
            weight=1.0,
        ),
        Rule(
            id="sec-inj-06",
            name="XSS Injection Attempt",
            category="security",
            severity="critical",
            metric_selector="security.injection_metrics.xss_injection_count",
            operator="gt",
            threshold=0.0,
            description_template="Cross-Site Scripting signature payloads detected in request URI/body ({value} hits)",
            weight=1.0,
        ),
        Rule(
            id="sec-inj-07",
            name="Path Traversal Attempt",
            category="security",
            severity="critical",
            metric_selector="security.injection_metrics.path_traversal_count",
            operator="gt",
            threshold=0.0,
            description_template="Directory path traversal escape payloads detected in request URI/body ({value} hits)",
            weight=1.0,
        ),
    ]
