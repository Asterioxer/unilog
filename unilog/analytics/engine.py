"""Metrics compilation for registered, stateless analytics analyzers."""

import time
from typing import Any, Mapping, Optional, Sequence

from pydantic import BaseModel

from unilog.analytics.base import AnalyzerContext
from unilog.analytics.registry import resolve_analyzers, validate_analyzer_registry
from unilog.analytics.schemas import AnalysisResult, MetricsBundle, PerformanceMetadata, AnalyzerInfo
from unilog.analytics.aliases import LATENCY_FIELDS


class MetricsEngine:
    """Compile registered analyzer output into the canonical analysis result."""

    def __init__(self) -> None:
        validate_analyzer_registry()

    def compile(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Optional[AnalyzerContext] = None,
    ) -> AnalysisResult:
        """Run analyzers in dependency order and validate their bundle fields."""
        analysis_context = context or AnalyzerContext()
        metric_values: dict[str, BaseModel] = {}
        
        # Telemetry statistics
        analyzed_records = len(records)
        skipped_records = sum(1 for r in records if "_parse_error" in r)
        missing_latency_fields = sum(1 for r in records if not any(f in r for f in LATENCY_FIELDS))

        start_time = time.perf_counter()
        for registration in resolve_analyzers():
            analyzer = registration.analyzer_class()
            metric = analyzer.analyze(records, analysis_context)
            self._validate_metric(registration.name, metric, registration.produces)
            metric_values[registration.name] = metric
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000.0
        
        analyzers_telemetry = [
            AnalyzerInfo(name=reg.name, version=reg.version)
            for reg in resolve_analyzers()
        ]
        
        metadata = PerformanceMetadata(
            analyzed_records=analyzed_records,
            skipped_records=skipped_records,
            missing_latency_fields=missing_latency_fields,
            execution_time_ms=execution_time_ms,
            analyzers=analyzers_telemetry
        )

        bundle = MetricsBundle.model_validate(metric_values)
        return AnalysisResult(metrics=bundle, metadata=metadata)

    @staticmethod
    def _validate_metric(
        name: str,
        metric: BaseModel,
        expected_model: Optional[type[BaseModel]],
    ) -> None:
        if expected_model is None:
            raise ValueError(f"Analyzer '{name}' must declare its produced metric model.")
        if not isinstance(metric, expected_model):
            raise TypeError(
                f"Analyzer '{name}' returned {type(metric).__name__}; "
                f"expected {expected_model.__name__}."
            )
        if name not in MetricsBundle.model_fields:
            raise ValueError(
                f"MetricsBundle does not define a field for analyzer '{name}'. "
                "Add the field in the release that introduces this analyzer."
            )