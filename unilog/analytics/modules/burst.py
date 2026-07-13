from datetime import datetime
from typing import Any, Mapping, Sequence
from pydantic import BaseModel

from unilog.analytics.base import BaseAnalyzer, AnalyzerContext
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import TrafficBurstMetrics, BurstWindow

from unilog.analytics.helpers import extract_timestamp

@register_analyzer("traffic_burst", produces=TrafficBurstMetrics, dependencies=["traffic"])
class TrafficBurstAnalyzer(BaseAnalyzer):
    """Detect sudden traffic spikes and compile a timeline of burst windows."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> BaseModel:
        total_requests = len(records)
        if total_requests == 0:
            return TrafficBurstMetrics(
                average_rps=0.0,
                peak_rps=0.0,
                burst_ratio=0.0,
                burst_windows=[],
                is_bursting=False
            )
            
        # Group by second timestamp
        rps_counts: dict[datetime, int] = {}
        for record in records:
            dt = extract_timestamp(record)
            if dt:
                try:
                    second_bucket = dt.replace(microsecond=0)
                    rps_counts[second_bucket] = rps_counts.get(second_bucket, 0) + 1
                except Exception:
                    pass
                    
        window_seconds = context.window_minutes * 60
        average_rps = float(total_requests / window_seconds) if window_seconds > 0 else 0.0
        
        peak_rps = float(max(rps_counts.values())) if rps_counts else 0.0
        burst_ratio = float(peak_rps / average_rps) if average_rps > 0.0 else 0.0
        
        # Determine burst windows: where RPS > 3 * average_rps and at least 2
        burst_threshold = max(3.0 * average_rps, 2.0)
        burst_windows = []
        
        for dt, count in sorted(rps_counts.items()):
            if count >= burst_threshold:
                ratio = float(count / average_rps) if average_rps > 0 else 0.0
                burst_windows.append(
                    BurstWindow(
                        timestamp=dt,
                        requests_per_second=float(count),
                        ratio=ratio
                    )
                )
                
        is_bursting = burst_ratio > 3.0 and peak_rps >= 5.0
        
        return TrafficBurstMetrics(
            average_rps=average_rps,
            peak_rps=peak_rps,
            burst_ratio=burst_ratio,
            burst_windows=burst_windows,
            is_bursting=is_bursting
        )
