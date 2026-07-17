"""Unit tests for the SecurityAnalyzer and simplified rules."""

from datetime import datetime, timedelta
from unilog.analytics import AnalyzerContext
from unilog.analytics.modules.session import SessionAnalyzer
from unilog.analytics.modules.security_analyzer import SecurityAnalyzer
from unilog.analytics.rules.builtin.security import get_rules
from unilog.analytics.rules import RuleEngine, RuleContext, RuleSet
from unilog.analytics.schemas import MetricsBundle
from datetime import timezone


def test_security_analyzer_detections() -> None:
    session_analyzer = SessionAnalyzer()
    security_analyzer = SecurityAnalyzer()
    context = AnalyzerContext()

    t0 = datetime(2026, 7, 17, 12, 0, 0)
    records = [
        # SQL Injection
        {"timestamp": t0, "source_ip": "1.1.1.1", "method": "GET", "path": "/products?id=1%20UNION%20SELECT%20username", "status_code": 200, "user_agent": "Mozilla"},
        # XSS Injection
        {"timestamp": t0 + timedelta(seconds=1), "source_ip": "1.1.1.1", "method": "GET", "path": "/search?q=<script>alert(1)</script>", "status_code": 200, "user_agent": "Mozilla"},
        # Traversal Injection
        {"timestamp": t0 + timedelta(seconds=2), "source_ip": "1.1.1.1", "method": "GET", "path": "/download?file=../../etc/passwd", "status_code": 200, "user_agent": "Mozilla"},
        # Scanner Probe
        {"timestamp": t0 + timedelta(seconds=3), "source_ip": "2.2.2.2", "method": "GET", "path": "/.env", "status_code": 404, "user_agent": "Mozilla"},
        # Headless Bot User Agent
        {"timestamp": t0 + timedelta(seconds=4), "source_ip": "3.3.3.3", "method": "GET", "path": "/", "status_code": 200, "user_agent": "HeadlessChrome/114.0.0.0"},
    ]

    # Pre-populate session module outputs in the context
    session_analyzer.analyze(records, context)
    metrics = security_analyzer.analyze(records, context)

    assert metrics.injection_metrics.sql_injection_count == 1
    assert metrics.injection_metrics.xss_injection_count == 1
    assert metrics.injection_metrics.path_traversal_count == 1
    assert metrics.scanner_metrics.scanner_hits_count == 1
    assert metrics.bot_metrics.headless_fingerprints_count == 1
    assert metrics.enumeration.error_404_ratio == 20.0  # 1 out of 5 requests is 404 (20%)


def test_brute_force_and_lockouts() -> None:
    session_analyzer = SessionAnalyzer()
    security_analyzer = SecurityAnalyzer()
    context = AnalyzerContext()

    t0 = datetime(2026, 7, 17, 12, 0, 0)
    records = []
    # Trigger lockout candidate threshold of 40 failed logins
    for i in range(45):
        records.append({
            "timestamp": t0 + timedelta(seconds=i),
            "source_ip": "4.4.4.4",
            "method": "POST",
            "path": "/api/v1/login",
            "status_code": 401,
            "user_agent": "Mozilla"
        })

    session_analyzer.analyze(records, context)
    metrics = security_analyzer.analyze(records, context)

    assert metrics.brute_force.failed_logins_per_ip["4.4.4.4"] == 45
    assert metrics.brute_force.failure_ratio == 100.0
    assert "4.4.4.4" in metrics.brute_force.lockout_candidates
    assert metrics.brute_force.lockout_candidates_count == 1


def test_rules_trigger_on_security_metrics() -> None:
    session_analyzer = SessionAnalyzer()
    security_analyzer = SecurityAnalyzer()
    context = AnalyzerContext()

    t0 = datetime(2026, 7, 17, 12, 0, 0)
    records = [
        {"timestamp": t0, "source_ip": "9.9.9.9", "method": "GET", "path": "/products?id=1%20UNION%20SELECT%201", "status_code": 200, "user_agent": "Mozilla"},
        {"timestamp": t0 + timedelta(seconds=1), "source_ip": "9.9.9.9", "method": "GET", "path": "/wp-admin", "status_code": 404, "user_agent": "Mozilla"},
    ]

    session_metrics = session_analyzer.analyze(records, context)
    security_metrics = security_analyzer.analyze(records, context)

    bundle = MetricsBundle(
        session=session_metrics,
        security=security_metrics
    )

    rules = get_rules()
    ruleset = RuleSet(version="1.0", rules=rules)
    engine = RuleEngine()
    rule_context = RuleContext(
        timestamp=datetime.now(timezone.utc),
        window_minutes=5,
        analyzed_records=2,
        skipped_records=0,
        parser_metadata={}
    )
    insights = engine.evaluate(bundle, ruleset, rule_context)

    # We should have triggered SQL Injection attempt and Vulnerability Scan probe!
    triggered_ids = {ins.id for ins in insights}
    assert any("sec-inj-05" in tid for tid in triggered_ids)
    assert any("sec-scan-04" in tid for tid in triggered_ids)
