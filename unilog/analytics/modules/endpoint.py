"""Request endpoint frequency metric analyzer."""

from typing import Any, Mapping, Sequence

from unilog.analytics.base import AnalyzerContext, BaseAnalyzer
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import EndpointMetrics


@register_analyzer("endpoint", version="1.0", produces=EndpointMetrics)
class EndpointAnalyzer(BaseAnalyzer):
    """Identifies the most highly requested endpoints with frequency count rankings."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> EndpointMetrics:
        counts: dict[str, int] = {}
        for r in records:
            path = r.get("path") or r.get("request_path") or r.get("request")
            if path:
                path_str = str(path).strip()
                parts = path_str.split()
                if len(parts) >= 2:
                    path_str = parts[1]
                elif len(parts) == 1:
                    path_str = parts[0]

                counts[path_str] = counts.get(path_str, 0) + 1

        sorted_endpoints = [
            {"path": k, "count": v}
            for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True)
        ]
        return EndpointMetrics(top_endpoints=sorted_endpoints)
