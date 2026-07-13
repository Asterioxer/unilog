"""Metrics compilation for registered, stateless analytics analyzers."""

from typing import Any, Mapping, Optional, Sequence

from pydantic import BaseModel

from unilog.analytics.base import AnalyzerContext
from unilog.analytics.registry import resolve_analyzers, validate_analyzer_registry
from unilog.analytics.schemas import MetricsBundle


class MetricsEngine:
    """Compile registered analyzer output into the canonical metrics bundle."""

    def __init__(self) -> None:
        validate_analyzer_registry()

    def compile(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Optional[AnalyzerContext] = None,
    ) -> MetricsBundle:
        """Run analyzers in dependency order and validate their bundle fields."""
        analysis_context = context or AnalyzerContext()
        metric_values: dict[str, BaseModel] = {}

        for registration in resolve_analyzers():
            analyzer = registration.analyzer_class()
            metric = analyzer.analyze(records, analysis_context)
            self._validate_metric(registration.name, metric, registration.produces)
            metric_values[registration.name] = metric

        return MetricsBundle.model_validate(metric_values)

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