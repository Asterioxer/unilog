"""HTTP status categories metric analyzer."""

from typing import Any, Mapping, Sequence

from unilog.analytics.base import AnalyzerContext, BaseAnalyzer
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import StatusMetrics


@register_analyzer("status", version="1.0", produces=StatusMetrics)
class StatusAnalyzer(BaseAnalyzer):
    """Aggregates HTTP response status codes and category counts."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> StatusMetrics:
        codes: dict[str, int] = {}
        categories = {"1xx": 0, "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}
        for r in records:
            status = r.get("status_code")
            if status is None:
                status = r.get("status")
            if status is not None:
                try:
                    status_val = int(status)
                    status_str = str(status_val)
                    codes[status_str] = codes.get(status_str, 0) + 1

                    cat_prefix = status_str[0]
                    cat_key = f"{cat_prefix}xx"
                    if cat_key in categories:
                        categories[cat_key] += 1
                except (ValueError, TypeError):
                    pass
        return StatusMetrics(status_codes=codes, status_categories=categories)
