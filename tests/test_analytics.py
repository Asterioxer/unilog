"""Tests for the Release 1 analytics infrastructure."""

from typing import Any, Mapping, Sequence

import pytest
from pydantic import BaseModel

from unilog.analytics import AnalyzerContext, BaseAnalyzer, MetricsBundle, MetricsEngine
from unilog.analytics.registry import (
    _ANALYZER_REGISTRY,
    get_analyzer,
    register_analyzer,
    resolve_analyzers,
)


class SampleMetric(BaseModel):
    value: int


class OtherMetric(BaseModel):
    value: int


@pytest.fixture(autouse=True)
def restore_analyzer_registry() -> None:
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
        @register_analyzer("invalid", produces=SampleMetric)
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
    bundle = MetricsEngine().compile([])

    assert bundle.model_dump(exclude_none=True) == {}


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
    records = [
        {"size": 100},
        {"bytes_sent": "250"},
        {"raw": "hello"},  # length 5
        {"message": "world"}  # length 5
    ]
    analyzer = TrafficAnalyzer()
    metrics = analyzer.analyze(records, AnalyzerContext())
    assert metrics.total_requests == 4
    assert metrics.volume_bytes == 360


def test_error_analyzer_calculates_ratios_and_levels() -> None:
    from unilog.analytics.modules.error import ErrorAnalyzer
    records = [
        {"level": "INFO"},
        {"level": "ERROR"},
        {"level": "critical"},
        {"level": "WARNING"}
    ]
    analyzer = ErrorAnalyzer()
    metrics = analyzer.analyze(records, AnalyzerContext())
    assert metrics.total_errors == 2
    assert metrics.error_ratio == 0.5
    assert metrics.errors_by_level == {"INFO": 1, "ERROR": 1, "CRITICAL": 1, "WARNING": 1}


def test_status_analyzer_calculates_categories() -> None:
    from unilog.analytics.modules.status import StatusAnalyzer
    records = [
        {"status_code": 200},
        {"status": "404"},
        {"status_code": 500},
        {"status": 200}
    ]
    analyzer = StatusAnalyzer()
    metrics = analyzer.analyze(records, AnalyzerContext())
    assert metrics.status_codes == {"200": 2, "404": 1, "500": 1}
    assert metrics.status_categories == {"1xx": 0, "2xx": 2, "3xx": 0, "4xx": 1, "5xx": 1}


def test_endpoint_analyzer_extracts_and_sorts_endpoints() -> None:
    from unilog.analytics.modules.endpoint import EndpointAnalyzer
    records = [
        {"path": "/index.html"},
        {"request_path": "GET /api/v1/auth HTTP/1.1"},
        {"request": "/index.html"},
        {"path": "/login"}
    ]
    analyzer = EndpointAnalyzer()
    metrics = analyzer.analyze(records, AnalyzerContext())
    assert metrics.top_endpoints[0] == {"path": "/index.html", "count": 2}
    assert any(e == {"path": "/api/v1/auth", "count": 1} for e in metrics.top_endpoints)
    assert any(e == {"path": "/login", "count": 1} for e in metrics.top_endpoints)


def test_metrics_engine_compiles_bundle_with_all_metrics() -> None:
    records = [
        {"path": "/index.html", "status_code": 200, "level": "INFO", "size": 150},
        {"path": "/login", "status_code": 401, "level": "WARN", "size": 250},
        {"path": "/api/v1/data", "status_code": 500, "level": "ERROR", "size": 50},
        {"path": "/index.html", "status_code": 200, "level": "INFO", "size": 100}
    ]

    engine = MetricsEngine()
    bundle = engine.compile(records)

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
    assert bundle.endpoint.top_endpoints[0] == {"path": "/index.html", "count": 2}