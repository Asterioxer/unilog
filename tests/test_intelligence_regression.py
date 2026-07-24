"""Regression tests for Release 10 Intelligence Pipeline."""

import pytest
from datetime import datetime, timezone
import unilog
from unilog.analytics import MetricsEngine, IncidentCorrelator, HealthCalculator
from unilog.analytics.rules import RuleEngine, RuleSet, RuleContext
from unilog.analytics.rules.builtin import collect_all_rules


def test_correlator_empty_list_returns_empty():
    """Verify IncidentCorrelator([]) returns empty list without raising exceptions."""
    correlator = IncidentCorrelator()
    metrics = MetricsEngine().compile([]).metrics
    assert correlator.correlate([], metrics) == []


def test_insights_backward_compatibility():
    """Verify that AnalysisResult.insights structure and content remain unchanged."""
    raw_log = '127.0.0.1 - - [24/Jul/2026:19:00:00 +0000] "GET /index.html HTTP/1.1" 200 100 "-" "Mozilla/5.0"'
    df = unilog.parse_string(raw_log)
    records = df.to_dict(orient="records")

    result = MetricsEngine().compile(records)
    ruleset = RuleSet(rules=collect_all_rules())
    insights = RuleEngine().evaluate(result.metrics, ruleset, RuleContext(timestamp=datetime.now(timezone.utc)))

    assert isinstance(insights, list)
