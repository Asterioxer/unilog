"""Error level metric analyzer."""

from typing import Any, Mapping, Sequence

from unilog.analytics.base import AnalyzerContext, BaseAnalyzer
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import ErrorMetrics


@register_analyzer("error", version="1.0", produces=ErrorMetrics)
class ErrorAnalyzer(BaseAnalyzer):
    """Calculates error ratios and groups occurrences by classification level."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> ErrorMetrics:
        total = len(records)
        errors = 0
        by_level: dict[str, int] = {}
        for r in records:
            level = r.get("level")
            if level:
                level_str = str(level).upper().strip()
                by_level[level_str] = by_level.get(level_str, 0) + 1
                if level_str in ("ERROR", "CRITICAL", "FATAL", "SEVERE"):
                    errors += 1
        ratio = (errors / total) if total > 0 else 0.0
        return ErrorMetrics(
            total_errors=errors,
            error_ratio=ratio,
            errors_by_level=by_level,
        )
