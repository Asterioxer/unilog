from typing import Any, Mapping, Sequence
from pydantic import BaseModel
from unilog.analytics.base import BaseAnalyzer, AnalyzerContext
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import LatencyMetrics
from unilog.analytics.aliases import LATENCY_FIELDS
from unilog.analytics.math_helpers import calculate_percentile

@register_analyzer("latency", produces=LatencyMetrics)
class LatencyAnalyzer(BaseAnalyzer):
    """Extract and analyze request processing duration latency percentiles and averages."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> BaseModel:
        latencies = []
        for record in records:
            for field in LATENCY_FIELDS:
                if field in record:
                    val = record[field]
                    if val is not None and val != "-":
                        try:
                            latencies.append(float(val))
                            break  # Match the first available field name
                        except ValueError:
                            pass
        
        if not latencies:
            return LatencyMetrics()
            
        avg_ms = float(sum(latencies) / len(latencies))
        max_ms = float(max(latencies))
        p50_ms = calculate_percentile(latencies, 50.0)
        p90_ms = calculate_percentile(latencies, 90.0)
        p99_ms = calculate_percentile(latencies, 99.0)
        
        return LatencyMetrics(
            p50_ms=p50_ms,
            p90_ms=p90_ms,
            p99_ms=p99_ms,
            avg_ms=avg_ms,
            max_ms=max_ms
        )
