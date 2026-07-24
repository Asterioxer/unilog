"""Unit tests for HealthCalculator."""

from unilog.analytics import MetricsEngine, HealthCalculator, IncidentCorrelator
from datetime import datetime, timezone


def test_health_calculator_clean_logs():
    """Verify system health score for clean logs is 100 HEALTHY."""
    metrics = MetricsEngine().compile([])
    calculator = HealthCalculator()
    health = calculator.calculate(metrics.metrics, [], [])

    assert health.overall_score == 100
    assert health.status == "HEALTHY"
    assert health.security.score == 100
    assert health.reliability.score == 100
    assert health.performance.score == 100
    assert health.traffic.score == 100


def test_health_calculator_with_incident():
    """Verify system health score drops when active incidents occur."""
    import unilog
    from unilog.analytics.rules import RuleEngine, RuleSet, RuleContext
    from unilog.analytics.rules.builtin import collect_all_rules

    raw_logs = [
        '192.168.1.1 - - [24/Jul/2026:19:00:00 +0000] "GET /wp-admin HTTP/1.1" 404 150 "-" "Nikto/2.1.6"',
        '192.168.1.1 - - [24/Jul/2026:19:00:01 +0000] "GET /.env HTTP/1.1" 404 120 "-" "Nikto/2.1.6"',
        '192.168.1.1 - - [24/Jul/2026:19:00:02 +0000] "GET /config.php HTTP/1.1" 500 110 "-" "Playwright/1.39.0 (headless)"',
    ]

    df = unilog.parse_string("\n".join(raw_logs))
    records = df.to_dict(orient="records")

    engine = MetricsEngine()
    result = engine.compile(records)

    ruleset = RuleSet(rules=collect_all_rules())
    rule_engine = RuleEngine()
    insights = rule_engine.evaluate(result.metrics, ruleset, RuleContext(timestamp=datetime.now(timezone.utc)))

    correlator = IncidentCorrelator()
    incidents = correlator.correlate(insights, result.metrics, records)

    calculator = HealthCalculator()
    health = calculator.calculate(result.metrics, insights, incidents)

    assert health.overall_score < 100
    assert health.security.score < 100
