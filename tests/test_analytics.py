"""Tests for the analytics infrastructure and performance analyzers."""

from datetime import datetime, timedelta
import os
from typing import Any, Mapping, Sequence, Generator, cast, Dict, List
import pytest
from pydantic import BaseModel

from unilog.analytics import AnalyzerContext, BaseAnalyzer, MetricsBundle, MetricsEngine
from unilog.analytics.registry import (
    _ANALYZER_REGISTRY,
    get_analyzer,
    register_analyzer,
    resolve_analyzers,
)
from unilog.analytics.schemas import (
    TrafficMetrics,
    ErrorMetrics,
    StatusMetrics,
    EndpointMetrics,
    LatencyMetrics,
    DistributionMetrics,
    BandwidthMetrics,
    TrafficBurstMetrics,
)


class SampleMetric(BaseModel):
    value: int


class OtherMetric(BaseModel):
    value: int


@pytest.fixture(autouse=True)
def restore_analyzer_registry() -> Generator[None, None, None]:
    """Keep global registry tests isolated without exposing mutation as public API."""
    from unilog.analytics.registry import _ensure_discovered
    _ensure_discovered()
    original_registry = _ANALYZER_REGISTRY.copy()
    yield
    _ANALYZER_REGISTRY.clear()
    _ANALYZER_REGISTRY.update(original_registry)


def test_metrics_bundle_is_an_empty_strict_contract() -> None:
    bundle = MetricsBundle()

    assert bundle.model_dump(exclude_none=True) == {}
    with pytest.raises(ValueError):
        MetricsBundle.model_validate({"traffic": {}})


def test_analyzer_context_uses_stable_defaults() -> None:
    context = AnalyzerContext()

    assert context.window_minutes == 5
    assert context.timezone == "UTC"
    assert context.bucket_seconds == 60
    assert context.parser_metadata == {}
    assert context.histogram_bucket_size == 100


def test_register_analyzer_retains_explicit_metadata() -> None:
    @register_analyzer("sample", version="1.2", produces=SampleMetric)
    class SampleAnalyzer(BaseAnalyzer):
        def analyze(
            self,
            records: Sequence[Mapping[str, Any]],
            context: AnalyzerContext,
        ) -> SampleMetric:
            return SampleMetric(value=len(records))

    registration = get_analyzer("sample")

    assert registration is not None
    assert registration.analyzer_class is SampleAnalyzer
    assert registration.version == "1.2"
    assert registration.dependencies == ()
    assert registration.produces is SampleMetric


def test_resolve_analyzers_orders_dependencies_before_dependants() -> None:
    @register_analyzer("first", produces=SampleMetric)
    class FirstAnalyzer(BaseAnalyzer):
        def analyze(
            self,
            records: Sequence[Mapping[str, Any]],
            context: AnalyzerContext,
        ) -> SampleMetric:
            return SampleMetric(value=1)

    @register_analyzer("second", dependencies=["first"], produces=SampleMetric)
    class SecondAnalyzer(BaseAnalyzer):
        def analyze(
            self,
            records: Sequence[Mapping[str, Any]],
            context: AnalyzerContext,
        ) -> SampleMetric:
            return SampleMetric(value=2)

    assert [registration.name for registration in resolve_analyzers(["second"])] == [
        "first",
        "second",
    ]


def test_registry_rejects_analyzers_without_a_valid_base_class() -> None:
    with pytest.raises(TypeError, match="inherit from BaseAnalyzer"):
        @register_analyzer("invalid", produces=SampleMetric)  # type: ignore[arg-type]
        class InvalidAnalyzer:
            pass


def test_registry_rejects_missing_dependency_during_engine_initialization() -> None:
    @register_analyzer("dependent", dependencies=["missing"], produces=SampleMetric)
    class DependentAnalyzer(BaseAnalyzer):
        def analyze(
            self,
            records: Sequence[Mapping[str, Any]],
            context: AnalyzerContext,
        ) -> SampleMetric:
            return SampleMetric(value=1)

    with pytest.raises(ValueError, match="not registered"):
        MetricsEngine()


def test_engine_returns_the_empty_bundle_when_no_analyzers_are_registered() -> None:
    _ANALYZER_REGISTRY.clear()
    result = MetricsEngine().compile([])

    assert result.metrics.model_dump(exclude_none=True) == {}
    assert result.metadata.analyzed_records == 0


def test_engine_rejects_analyzer_output_without_a_declared_bundle_field() -> None:
    @register_analyzer("sample", produces=SampleMetric)
    class SampleAnalyzer(BaseAnalyzer):
        def analyze(
            self,
            records: Sequence[Mapping[str, Any]],
            context: AnalyzerContext,
        ) -> SampleMetric:
            return SampleMetric(value=1)

    with pytest.raises(ValueError, match="does not define a field"):
        MetricsEngine().compile([])


def test_engine_rejects_analyzer_output_that_breaks_its_declared_contract() -> None:
    @register_analyzer("sample", produces=SampleMetric)
    class InvalidOutputAnalyzer(BaseAnalyzer):
        def analyze(
            self,
            records: Sequence[Mapping[str, Any]],
            context: AnalyzerContext,
        ) -> BaseModel:
            return OtherMetric(value=1)

    with pytest.raises(TypeError, match="expected SampleMetric"):
        MetricsEngine().compile([])


def test_traffic_analyzer_calculates_totals_and_sizes() -> None:
    from unilog.analytics.modules.traffic import TrafficAnalyzer
    records: List[Dict[str, Any]] = [
        {"size": 100},
        {"bytes_sent": "250"},
        {"raw": "hello"},  # length 5
        {"message": "world"}  # length 5
    ]
    analyzer = TrafficAnalyzer()
    metrics = cast(TrafficMetrics, analyzer.analyze(records, AnalyzerContext()))
    assert metrics.total_requests == 4
    assert metrics.volume_bytes == 360


def test_error_analyzer_calculates_ratios_and_levels() -> None:
    from unilog.analytics.modules.error import ErrorAnalyzer
    records: List[Dict[str, Any]] = [
        {"level": "INFO"},
        {"level": "ERROR"},
        {"level": "critical"},
        {"level": "WARNING"}
    ]
    analyzer = ErrorAnalyzer()
    metrics = cast(ErrorMetrics, analyzer.analyze(records, AnalyzerContext()))
    assert metrics.total_errors == 2
    assert metrics.error_ratio == 0.5
    assert metrics.errors_by_level == {"INFO": 1, "ERROR": 1, "CRITICAL": 1, "WARNING": 1}


def test_status_analyzer_calculates_categories() -> None:
    from unilog.analytics.modules.status import StatusAnalyzer
    records: List[Dict[str, Any]] = [
        {"status_code": 200},
        {"status": "404"},
        {"status_code": 500},
        {"status": 200}
    ]
    analyzer = StatusAnalyzer()
    metrics = cast(StatusMetrics, analyzer.analyze(records, AnalyzerContext()))
    assert metrics.status_codes == {"200": 2, "404": 1, "500": 1}
    assert metrics.status_categories == {"1xx": 0, "2xx": 2, "3xx": 0, "4xx": 1, "5xx": 1}
    assert metrics.http_5xx_rate == 0.25


def test_endpoint_analyzer_extracts_and_sorts_endpoints() -> None:
    from unilog.analytics.modules.endpoint import EndpointAnalyzer
    records: List[Dict[str, Any]] = [
        {"path": "/index.html"},
        {"request_path": "GET /api/v1/auth HTTP/1.1"},
        {"request": "/index.html"},
        {"path": "/login"}
    ]
    analyzer = EndpointAnalyzer()
    metrics = cast(EndpointMetrics, analyzer.analyze(records, AnalyzerContext()))
    assert metrics.top_endpoints[0] == {"path": "/index.html", "count": 2, "share_pct": 50.0}
    assert any(e == {"path": "/api/v1/auth", "count": 1, "share_pct": 25.0} for e in metrics.top_endpoints)
    assert any(e == {"path": "/login", "count": 1, "share_pct": 25.0} for e in metrics.top_endpoints)
    assert metrics.top_endpoint_share == 50.0


def test_metrics_engine_compiles_bundle_with_all_metrics() -> None:
    records: List[Dict[str, Any]] = [
        {"path": "/index.html", "status_code": 200, "level": "INFO", "size": 150},
        {"path": "/login", "status_code": 401, "level": "WARN", "size": 250},
        {"path": "/api/v1/data", "status_code": 500, "level": "ERROR", "size": 50},
        {"path": "/index.html", "status_code": 200, "level": "INFO", "size": 100}
    ]

    engine = MetricsEngine()
    result = engine.compile(records)
    bundle = result.metrics

    assert bundle.traffic is not None
    assert bundle.traffic.total_requests == 4
    assert bundle.traffic.volume_bytes == 550

    assert bundle.error is not None
    assert bundle.error.total_errors == 1
    assert bundle.error.error_ratio == 0.25

    assert bundle.status is not None
    assert bundle.status.status_codes == {"200": 2, "401": 1, "500": 1}
    assert bundle.status.status_categories == {"1xx": 0, "2xx": 2, "3xx": 0, "4xx": 1, "5xx": 1}

    assert bundle.endpoint is not None
    assert bundle.endpoint.top_endpoints[0] == {"path": "/index.html", "count": 2, "share_pct": 50.0}


# --- Release 3 Performance Analyzers Tests ---

def test_latency_analyzer() -> None:
    from unilog.analytics.modules.latency import LatencyAnalyzer
    records: List[Dict[str, Any]] = [
        {"latency": "100.5"},
        {"request_time": 200.0},
        {"duration_ms": 300.2},
        {"other": "ignored"}
    ]
    analyzer = LatencyAnalyzer()
    metrics = cast(LatencyMetrics, analyzer.analyze(records, AnalyzerContext()))
    
    assert metrics.avg_ms == pytest.approx(200.23, 0.01)
    assert metrics.min_ms == 100.5
    assert metrics.max_ms == 300.2
    assert metrics.p50_ms == 200.0
    assert metrics.p90_ms == pytest.approx(280.16, 0.01)
    assert metrics.p95_ms == pytest.approx(290.18, 0.01)
    assert metrics.p99_ms == pytest.approx(298.02, 0.01)


def test_latency_analyzer_empty() -> None:
    from unilog.analytics.modules.latency import LatencyAnalyzer
    analyzer = LatencyAnalyzer()
    metrics = cast(LatencyMetrics, analyzer.analyze([], AnalyzerContext()))
    assert metrics.avg_ms is None
    assert metrics.p50_ms is None


def test_distribution_analyzer() -> None:
    from unilog.analytics.modules.distribution import DistributionAnalyzer
    records: List[Dict[str, Any]] = [
        {"source_ip": "192.168.1.1", "request_size": 150, "size": 350},
        {"ip": "192.168.1.2", "request_size": 250, "size": 450},
        {"source_ip": "192.168.1.1", "request_size": 50, "size": 150}
    ]
    analyzer = DistributionAnalyzer()
    metrics = cast(DistributionMetrics, analyzer.analyze(records, AnalyzerContext(histogram_bucket_size=100)))
    
    # Check IP metrics
    assert len(metrics.top_ips) == 2
    assert metrics.top_ips[0].ip == "192.168.1.1"
    assert metrics.top_ips[0].requests == 2
    
    # Check sizes
    assert metrics.request_sizes.count == 3
    assert metrics.request_sizes.minimum == 50
    assert metrics.request_sizes.maximum == 250
    assert metrics.request_sizes.average == 150.0
    assert metrics.request_sizes.histogram == {"0-99": 1, "100-199": 1, "200-299": 1}
    
    assert metrics.response_sizes.count == 3
    assert metrics.response_sizes.minimum == 150
    assert metrics.response_sizes.maximum == 450
    assert metrics.response_sizes.average == 316.6666666666667
    assert metrics.response_sizes.histogram == {"100-199": 1, "300-399": 1, "400-499": 1}


def test_bandwidth_analyzer() -> None:
    from unilog.analytics.modules.bandwidth import BandwidthAnalyzer
    records: List[Dict[str, Any]] = [
        {"path": "/index.html", "size": 100},
        {"request": "GET /api/v1/auth HTTP/1.1", "bytes_sent": 200},
        {"path": "/index.html", "size": 300}
    ]
    analyzer = BandwidthAnalyzer()
    metrics = cast(BandwidthMetrics, analyzer.analyze(records, AnalyzerContext(window_minutes=5)))
    
    assert metrics.total_bytes_sent == 600
    assert metrics.bytes_per_second == 2.0  # 600 / 300
    assert len(metrics.top_bandwidth_endpoints) == 2
    assert metrics.top_bandwidth_endpoints[0].endpoint == "/index.html"
    assert metrics.top_bandwidth_endpoints[0].bytes_sent == 400
    assert metrics.top_bandwidth_endpoints[0].percentage == pytest.approx(66.666, 0.1)


def test_traffic_burst_analyzer() -> None:
    from unilog.analytics.modules.burst import TrafficBurstAnalyzer
    base_time = datetime(2026, 7, 13, 12, 0, 0)
    records: List[Dict[str, Any]] = []
    
    # 4 requests at base_time, 2 requests at base_time+1sec
    for _ in range(4):
        records.append({"timestamp": base_time.isoformat()})
    for _ in range(2):
        records.append({"timestamp": (base_time + timedelta(seconds=1)).isoformat()})
        
    analyzer = TrafficBurstAnalyzer()
    metrics = cast(TrafficBurstMetrics, analyzer.analyze(records, AnalyzerContext(window_minutes=5)))
    
    assert metrics.average_rps == pytest.approx(6 / 300, 0.001)
    assert metrics.peak_rps == 4.0
    assert metrics.burst_ratio == pytest.approx(4 / (6 / 300), 0.001)
    assert len(metrics.burst_windows) == 2
    assert metrics.burst_windows[0].requests_per_second == 4.0
    assert metrics.burst_windows[0].timestamp == base_time
    assert metrics.is_bursting is False  # peak_rps < 5 (our boundary check threshold)


def test_traffic_burst_analyzer_spike() -> None:
    from unilog.analytics.modules.burst import TrafficBurstAnalyzer
    base_time = datetime(2026, 7, 13, 12, 0, 0)
    records: List[Dict[str, Any]] = []
    
    # 10 requests at base_time (significant spike)
    for _ in range(10):
        records.append({"timestamp": base_time.isoformat()})
        
    analyzer = TrafficBurstAnalyzer()
    metrics = cast(TrafficBurstMetrics, analyzer.analyze(records, AnalyzerContext(window_minutes=5)))
    
    assert metrics.is_bursting is True
    assert metrics.peak_rps == 10.0


def test_metrics_engine_performance_metadata() -> None:
    records = [
        {"path": "/index.html", "status_code": 200, "latency": 15.0},
        {"path": "/login", "status_code": 401, "_parse_error": "malformed line"},
        {"path": "/api/v1/data", "status_code": 500}  # missing latency field
    ]
    
    engine = MetricsEngine()
    result = engine.compile(records)
    
    assert result.metadata.analyzed_records == 3
    assert result.metadata.skipped_records == 1
    assert result.metadata.missing_latency_fields == 2
    assert result.metadata.execution_time_ms >= 0.0
    assert len(result.metadata.analyzers) >= 8


@pytest.mark.performance
@pytest.mark.skipif(
    os.getenv("GITHUB_ACTIONS") == "true",
    reason="Skip performance benchmark in CI environments"
)
def test_performance_benchmark() -> None:
    # 100,000 records performance verification
    import time
    
    records = [
        {
            "source_ip": f"192.168.1.{i % 254}",
            "timestamp": "2026-07-13T12:00:00.000Z",
            "method": "GET",
            "path": f"/api/v1/resource/{i % 10}",
            "status_code": 200,
            "size": 1024,
            "request_size": 256,
            "latency": 5.4,
            "level": "INFO"
        }
        for i in range(100000)
    ]
    
    engine = MetricsEngine()
    start = time.perf_counter()
    result = engine.compile(records)
    elapsed = time.perf_counter() - start
    
    assert result.metrics is not None
    # 100,000 records compile duration budget threshold check
    assert elapsed < 15.0


def test_analysis_result_insights_schema() -> None:
    from unilog.analytics.schemas import Insight
    engine = MetricsEngine()
    result = engine.compile([])
    
    assert isinstance(result.insights, list)
    assert result.ruleset_version == "1.0"
    
    # Verify we can validate with mock Insight objects
    mock_insight = Insight(
        id="test-1",
        category="security",
        severity="critical",
        confidence=0.9,
        timestamp=datetime.now(),
        description="SQL injection detected",
        recommendation="Block IP"
    )
    result.insights.append(mock_insight)
    assert len(result.insights) == 1


def test_distribution_analyzer_ip_limit() -> None:
    from unilog.analytics.modules.distribution import DistributionAnalyzer
    # 100 unique IPs
    records = [{"source_ip": f"192.168.1.{i}"} for i in range(100)]
    analyzer = DistributionAnalyzer()
    
    # Custom limit of 10
    metrics = cast(DistributionMetrics, analyzer.analyze(records, AnalyzerContext(top_ips_limit=10)))
    assert len(metrics.top_ips) == 10

    # Default limit of 50
    metrics_default = cast(DistributionMetrics, analyzer.analyze(records, AnalyzerContext()))
    assert len(metrics_default.top_ips) == 50


def test_extract_timestamp_various_formats() -> None:
    from unilog.analytics.helpers import extract_timestamp
    
    # Datetime object
    dt = datetime(2026, 7, 13, 15, 0, 0)
    assert extract_timestamp({"timestamp": dt}) == dt
    
    # ISO string
    assert extract_timestamp({"timestamp": "2026-07-13T15:00:00"}) == dt
    
    # Apache/Nginx combined format timestamp
    from dateutil.tz import tzutc
    dt_utc = datetime(2026, 7, 13, 15, 0, 0, tzinfo=tzutc())
    apache_ts = "13/Jul/2026:15:00:00 +0000"
    assert extract_timestamp({"timestamp": apache_ts}) == dt_utc

    # Malformed/Missing
    assert extract_timestamp({"timestamp": "-"}) is None
    assert extract_timestamp({}) is None


def test_endpoint_normalization_consistency() -> None:
    from unilog.analytics.helpers import normalize_endpoint
    
    assert normalize_endpoint({"path": "GET /users HTTP/1.1"}) == "/users"
    assert normalize_endpoint({"request_path": "DELETE /admin/settings HTTP/1.1"}) == "/admin/settings"
    assert normalize_endpoint({"request": "/index.html"}) == "/index.html"
    assert normalize_endpoint({"path": "/login"}) == "/login"
    assert normalize_endpoint({}) == "unknown"