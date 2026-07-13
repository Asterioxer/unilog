"""Traffic metric analyzer."""

from typing import Any, Mapping, Sequence

from unilog.analytics.base import AnalyzerContext, BaseAnalyzer
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import TrafficMetrics


@register_analyzer("traffic", version="1.0", produces=TrafficMetrics)
class TrafficAnalyzer(BaseAnalyzer):
    """Computes total request metrics and payload volumes in bytes."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> TrafficMetrics:
        total = len(records)
        volume = 0
        for r in records:
            # Check size, bytes_sent, body_bytes_sent fields first
            size = r.get("size") or r.get("bytes_sent") or r.get("body_bytes_sent")
            if size is not None:
                try:
                    volume += int(size)
                except (ValueError, TypeError):
                    pass
            elif "raw" in r and isinstance(r["raw"], str):
                volume += len(r["raw"])
            elif "message" in r and isinstance(r["message"], str):
                volume += len(r["message"])
        return TrafficMetrics(total_requests=total, volume_bytes=volume)
