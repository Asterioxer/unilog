"""Unit tests for session and journey analyzers."""

import pytest
from datetime import datetime, timedelta
from unilog.analytics import AnalyzerContext
from unilog.analytics.modules.session import SessionAnalyzer
from unilog.analytics.modules.journey import JourneyAnalyzer, map_path_to_stage


def test_session_reconstruction_and_timeout() -> None:
    analyzer = SessionAnalyzer()
    context = AnalyzerContext()

    t0 = datetime(2026, 7, 17, 12, 0, 0)
    records = [
        # Session 1 for IP A
        {"timestamp": t0, "source_ip": "1.1.1.1", "method": "GET", "path": "/", "status_code": 200, "size": 100},
        {"timestamp": t0 + timedelta(minutes=15), "source_ip": "1.1.1.1", "method": "GET", "path": "/products", "status_code": 200, "size": 200},
        # Session 2 for IP A (after 35 minutes)
        {"timestamp": t0 + timedelta(minutes=50), "source_ip": "1.1.1.1", "method": "GET", "path": "/cart", "status_code": 200, "size": 50},
        
        # Session 1 for IP B
        {"timestamp": t0, "source_ip": "2.2.2.2", "method": "POST", "path": "/login", "status_code": 200, "size": 150},
    ]

    metrics = analyzer.analyze(records, context)

    assert metrics.active_sessions_count == 3
    assert metrics.longest_session_duration_seconds == 15 * 60.0
    
    # 2 out of 3 sessions had request count = 1 (bounce) -> bounce rate is 66.67%
    assert metrics.bounce_rate == pytest.approx(66.67, 0.01)
    assert metrics.requests_per_session == pytest.approx(1.33, 0.01)


def test_journey_stage_mapping() -> None:
    assert map_path_to_stage("/") == "Landing"
    assert map_path_to_stage("/home") == "Landing"
    assert map_path_to_stage("/products") == "Products"
    assert map_path_to_stage("/product/123") == "Product"
    assert map_path_to_stage("/cart") == "Cart"
    assert map_path_to_stage("/checkout") == "Checkout"
    assert map_path_to_stage("/other-page") == "Other"


def test_journey_analyzer_enrichment() -> None:
    session_analyzer = SessionAnalyzer()
    journey_analyzer = JourneyAnalyzer()
    context = AnalyzerContext()

    t0 = datetime(2026, 7, 17, 12, 0, 0)
    records = [
        {"timestamp": t0, "source_ip": "1.1.1.1", "method": "GET", "path": "/", "status_code": 200},
        {"timestamp": t0 + timedelta(minutes=5), "source_ip": "1.1.1.1", "method": "GET", "path": "/products", "status_code": 200},
        {"timestamp": t0 + timedelta(minutes=10), "source_ip": "1.1.1.1", "method": "GET", "path": "/cart", "status_code": 200},
    ]

    # SessionAnalyzer writes to context.parser_metadata["reconstructed_sessions"]
    session_analyzer.analyze(records, context)
    journey_metrics = journey_analyzer.analyze(records, context)

    assert journey_metrics.stage_counts["Landing"] == 1
    assert journey_metrics.stage_counts["Products"] == 1
    assert journey_metrics.stage_counts["Cart"] == 1
    assert journey_metrics.funnel["Landing"] == 1
    assert journey_metrics.funnel["Checkout"] == 0
    assert len(journey_metrics.journeys) == 1
    assert journey_metrics.journeys[0] == ["Landing", "Products", "Cart"]


def test_security_behavior_indicators() -> None:
    session_analyzer = SessionAnalyzer()
    context = AnalyzerContext()

    t0 = datetime(2026, 7, 17, 12, 0, 0)
    
    # 1. Bot activity (>500 requests)
    bot_records = [
        {"timestamp": t0 + timedelta(seconds=i), "source_ip": "3.3.3.3", "method": "GET", "path": f"/page-{i}", "status_code": 200}
        for i in range(505)
    ]
    
    # 2. Credential stuffing (>40 failed logins)
    cs_records = [
        {"timestamp": t0 + timedelta(seconds=i*5), "source_ip": "4.4.4.4", "method": "POST", "path": "/login", "status_code": 401}
        for i in range(45)
    ]

    metrics = session_analyzer.analyze(bot_records + cs_records, context)

    assert metrics.possible_bot_count == 1
    assert metrics.credential_stuffing_count == 1
