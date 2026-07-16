"""Unit and integration tests for the rule engine and evaluation subsystem."""

import pytest
from datetime import datetime, timezone

from unilog.analytics import MetricsEngine
from unilog.analytics.schemas import MetricsBundle
from unilog.analytics.rules import Rule, RuleSet, RuleContext, RuleEngine
from unilog.analytics.rules.operators import get_operator, OPERATORS
from unilog.analytics.rules.recommendations import RecommendationProvider
from unilog.analytics.rules.evaluator import RuleEvaluator
from unilog.analytics.rules.builtin import collect_all_rules


def test_operator_registry() -> None:
    """Test all registered operators behave as expected."""
    assert len(OPERATORS) == 5
    assert get_operator("gt")(5.0, 3.0) is True
    assert get_operator("gt")(3.0, 5.0) is False
    assert get_operator("lt")(2.0, 4.0) is True
    assert get_operator("gte")(3.0, 3.0) is True
    assert get_operator("lte")(4.0, 5.0) is True
    assert get_operator("eq")(1.0, 1.0) is True
    assert get_operator("eq")(1.0, 0.0) is False

    with pytest.raises(ValueError, match="Unknown operator"):
        get_operator("invalid_op")


def test_recommendation_provider() -> None:
    """Test that RecommendationProvider returns severity-aware recommendations."""
    provider = RecommendationProvider()
    rule_perf = Rule(
        id="test-perf",
        name="Test Perf",
        category="performance",
        severity="critical",
        metric_selector="latency.p99_ms",
        operator="gt",
        threshold=500.0,
        description_template="Description",
    )
    rec = provider.recommend(rule_perf, 600.0, "critical")
    assert "Scale deployment immediately" in rec

    rule_sec = Rule(
        id="test-sec",
        name="Test Sec",
        category="security",
        severity="medium",
        metric_selector="ip.count",
        operator="gt",
        threshold=10.0,
        description_template="Description",
    )
    rec_sec = provider.recommend(rule_sec, 12.0, "medium")
    assert "Review access logs for suspicious patterns" in rec_sec

    # Fallback default
    rule_unknown = Rule(
        id="test-unknown",
        name="Test Unknown",
        category="unknown_category",
        severity="low",
        metric_selector="unknown.field",
        operator="gt",
        threshold=1.0,
        description_template="Description",
    )
    rec_unknown = provider.recommend(rule_unknown, 2.0, "low")
    assert "Review the triggered metric and take appropriate action" in rec_unknown


def test_selector_resolution() -> None:
    """Test dot-separated metric selector path traversal into MetricsBundle."""
    # Build a bundle with synthetic values
    from unilog.analytics.schemas import LatencyMetrics, ErrorMetrics, MetricsBundle
    
    bundle = MetricsBundle(
        latency=LatencyMetrics(p99_ms=450.5, avg_ms=120.0),
        error=ErrorMetrics(total_errors=5, error_ratio=0.08, errors_by_level={"ERROR": 5}),
    )

    evaluator = RuleEvaluator()
    assert evaluator._resolve_selector(bundle, "latency.p99_ms") == 450.5
    assert evaluator._resolve_selector(bundle, "error.error_ratio") == 0.08
    assert evaluator._resolve_selector(bundle, "latency.p95_ms") is None  # field exists but is None
    assert evaluator._resolve_selector(bundle, "nonexistent.field") is None


def test_confidence_computation() -> None:
    """Test that confidence scales properly with sample size (analyzed_records)."""
    evaluator = RuleEvaluator()
    rule = Rule(
        id="test-latency",
        name="High Latency",
        category="performance",
        severity="high",
        metric_selector="latency.p99_ms",
        operator="gt",
        threshold=200.0,
        description_template="P99 latency {value}ms exceeds {threshold}ms",
        weight=1.0,
    )
    
    from unilog.analytics.schemas import LatencyMetrics
    bundle = MetricsBundle(latency=LatencyMetrics(p99_ms=250.0))

    # Low sample size (10 records) -> confidence should be lower
    context_low = RuleContext(timestamp=datetime.now(timezone.utc), analyzed_records=10)
    insight_low = evaluator.evaluate(rule, bundle, context_low)
    assert insight_low is not None
    assert insight_low.confidence == 0.1  # 10 / 100 * 1.0

    # High sample size (120 records) -> confidence should cap at weight (1.0)
    context_high = RuleContext(timestamp=datetime.now(timezone.utc), analyzed_records=120)
    insight_high = evaluator.evaluate(rule, bundle, context_high)
    assert insight_high is not None
    assert insight_high.confidence == 1.0  # capped at 1.0


def test_rule_evaluator_triggers_and_skips() -> None:
    """Test that evaluator correctly returns Insight or None depending on condition."""
    evaluator = RuleEvaluator()
    rule = Rule(
        id="test-error",
        name="High Error Rate",
        category="reliability",
        severity="high",
        metric_selector="error.error_ratio",
        operator="gt",
        threshold=0.05,
        description_template="Error ratio {value} exceeds {threshold}",
        weight=1.0,
    )
    
    from unilog.analytics.schemas import ErrorMetrics
    context = RuleContext(timestamp=datetime.now(timezone.utc), analyzed_records=100)

    # 1. Condition NOT met: error ratio is 0.02 (<= 0.05)
    bundle_ok = MetricsBundle(error=ErrorMetrics(total_errors=2, error_ratio=0.02, errors_by_level={}))
    assert evaluator.evaluate(rule, bundle_ok, context) is None

    # 2. Condition MET: error ratio is 0.08 (> 0.05)
    bundle_fail = MetricsBundle(error=ErrorMetrics(total_errors=8, error_ratio=0.08, errors_by_level={}))
    insight = evaluator.evaluate(rule, bundle_fail, context)
    assert insight is not None
    assert insight.category == "reliability"
    assert insight.severity == "high"
    assert insight.confidence == 1.0
    assert "Error ratio 0.08 exceeds 0.05" in insight.description
    assert insight.evidence["observed_value"] == 0.08
    assert insight.evidence["threshold"] == 0.05


def test_built_in_rules_collection() -> None:
    """Test built-in rules are loaded correctly."""
    rules = collect_all_rules()
    assert len(rules) >= 7  # 2 perf + 2 reliability + 3 traffic
    ids = {r.id for r in rules}
    assert "high-latency-p99" in ids
    assert "high-latency-p95" in ids
    assert "high-error-ratio" in ids
    assert "high-5xx-rate" in ids
    assert "traffic-burst" in ids
    assert "bandwidth-spike" in ids
    assert "endpoint-overload" in ids


def test_rule_engine_orchestration() -> None:
    """Test RuleEngine correctly evaluates multiple rules in a ruleset."""
    ruleset = RuleSet(rules=[
        Rule(
            id="rule-1",
            name="R1",
            category="performance",
            severity="low",
            metric_selector="latency.avg_ms",
            operator="gt",
            threshold=10.0,
            description_template="R1 template {value}",
        ),
        Rule(
            id="rule-2",
            name="R2",
            category="performance",
            severity="high",
            metric_selector="latency.avg_ms",
            operator="gt",
            threshold=100.0,
            description_template="R2 template {value}",
            enabled=False,  # disabled rule should be skipped
        ),
        Rule(
            id="rule-3",
            name="R3",
            category="reliability",
            severity="medium",
            metric_selector="error.error_ratio",
            operator="gt",
            threshold=0.5,
            description_template="R3 template {value}",
        )
    ])

    from unilog.analytics.schemas import LatencyMetrics, ErrorMetrics
    bundle = MetricsBundle(
        latency=LatencyMetrics(avg_ms=15.0),
        error=ErrorMetrics(total_errors=1, error_ratio=0.1, errors_by_level={}),
    )

    context = RuleContext(timestamp=datetime.now(timezone.utc), analyzed_records=100)
    engine = RuleEngine()
    insights = engine.evaluate(bundle, ruleset, context)

    # Only rule-1 should trigger.
    # rule-2 is disabled.
    # rule-3 condition not met (0.1 is not > 0.5).
    assert len(insights) == 1
    assert insights[0].metadata["rule_id"] == "rule-1"


def test_metrics_engine_compile_with_ruleset() -> None:
    """Test full integration: MetricsEngine.compile resolves ruleset and generates insights."""
    records = [
        {"latency": 600.0, "status_code": 500, "level": "ERROR", "path": "/api/users", "size": 12000},
        {"latency": 700.0, "status_code": 500, "level": "ERROR", "path": "/api/users", "size": 15000},
        {"latency": 800.0, "status_code": 200, "level": "INFO", "path": "/api/users", "size": 5000},
    ]

    ruleset = RuleSet(rules=collect_all_rules())
    engine = MetricsEngine()
    result = engine.compile(records, ruleset=ruleset)

    assert result.metrics is not None
    assert result.metrics.latency is not None
    assert result.metrics.status is not None
    assert result.metrics.endpoint is not None
    assert result.metrics.latency.p99_ms == pytest.approx(798.0, 0.1)
    assert result.metrics.status.http_5xx_rate == pytest.approx(0.666, 0.01)
    assert result.metrics.endpoint.top_endpoint_share == 100.0

    # Ensure insights were generated
    assert len(result.insights) > 0
    triggered_ids = {ins.metadata["rule_id"] for ins in result.insights}
    
    # 5xx rate is 66.6% (> 2%), P99 latency is 798ms (> 500ms), Endpoint overload is 100% (> 50%), Bandwidth is spike (> 10000)
    assert "high-latency-p99" in triggered_ids
    assert "high-5xx-rate" in triggered_ids
    assert "endpoint-overload" in triggered_ids
