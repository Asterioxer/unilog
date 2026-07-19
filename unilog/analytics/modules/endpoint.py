"""Request endpoint frequency metric analyzer."""

from typing import Any, Mapping, Sequence

from unilog.analytics.base import AnalyzerContext, BaseAnalyzer
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import EndpointMetrics


from unilog.analytics.helpers import normalize_endpoint


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
            path_str = normalize_endpoint(r)
            counts[path_str] = counts.get(path_str, 0) + 1

        total = len(records)
        top_share: float | None = None
        if counts and total > 0:
            top_count = max(counts.values())
            top_share = float(top_count / total * 100.0)

        sorted_endpoints = [
            {
                "path": k,
                "count": v,
                "share_pct": float(v / total * 100.0) if total > 0 else 0.0
            }
            for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True)
        ]

        return EndpointMetrics(
            top_endpoints=sorted_endpoints,
            top_endpoint_share=top_share,
        )
