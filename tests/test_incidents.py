"""Unit tests for IncidentCorrelator and TimelineBuilder."""

import pytest
from datetime import datetime, timezone
import unilog
from unilog.analytics import MetricsEngine, IncidentCorrelator
from unilog.analytics.rules import RuleEngine, RuleSet, RuleContext
from unilog.analytics.rules.builtin import collect_all_rules


def test_incident_correlator_empty():
    """Verify that IncidentCorrelator([]) safely returns an empty list."""
    correlator = IncidentCorrelator()
    metrics = MetricsEngine().compile([])
    incidents = correlator.correlate([], metrics.metrics)
    assert incidents == []


def test_security_incident_correlation():
    """Test correlation of co-occurring security scanner, bot, and 404 probe alerts into a single incident."""
    raw_logs = [
        '185.220.101.47 - - [24/Jul/2026:19:00:00 +0000] "GET /wp-admin HTTP/1.1" 404 150 "-" "Nikto/2.1.6"',
        '185.220.101.47 - - [24/Jul/2026:19:00:01 +0000] "GET /.env HTTP/1.1" 404 120 "-" "Nikto/2.1.6"',
        '185.220.101.47 - - [24/Jul/2026:19:00:02 +0000] "GET /config.php HTTP/1.1" 404 110 "-" "Playwright/1.39.0 (headless)"',
        '185.220.101.47 - - [24/Jul/2026:19:00:03 +0000] "POST /api/v1/auth/login HTTP/1.1" 401 90 "-" "Go-http-client/2.0"',
        '185.220.101.47 - - [24/Jul/2026:19:00:04 +0000] "POST /api/v1/auth/login HTTP/1.1" 401 90 "-" "Go-http-client/2.0"'
    ]

    df = unilog.parse_string("\n".join(raw_logs))
    records = df.to_dict(orient="records")

    engine = MetricsEngine()
    result = engine.compile(records)

    ruleset = RuleSet(rules=collect_all_rules())
    rule_engine = RuleEngine()
    rule_context = RuleContext(timestamp=datetime.now(timezone.utc), window_minutes=5)
    insights = rule_engine.evaluate(result.metrics, ruleset, rule_context)

    correlator = IncidentCorrelator()
    incidents = correlator.correlate(insights, result.metrics, records)

    assert len(incidents) >= 1
    sec_inc = incidents[0]

    # Verify ID format
    assert sec_inc.incident_id.startswith("INC-")

    # Verify affected IPs
    assert "185.220.101.47" in sec_inc.affected_ips

    # Verify threat profile suspected tools
    assert sec_inc.threat_profile is not None
    assert "Nikto" in sec_inc.threat_profile.suspected_tools
    assert "Playwright (headless)" in sec_inc.threat_profile.suspected_tools

    # Verify evidence-based confidence rationale
    assert len(sec_inc.confidence_evidence) >= 1
    assert any("Nikto" in ev for ev in sec_inc.confidence_evidence)

    # Verify actionable recommendations
    assert len(sec_inc.recommendations) >= 1
    assert any("Block" in r for r in sec_inc.recommendations)
