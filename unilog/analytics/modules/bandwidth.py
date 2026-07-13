from typing import Any, Mapping, Sequence
from pydantic import BaseModel
from unilog.analytics.base import BaseAnalyzer, AnalyzerContext
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import BandwidthMetrics, EndpointBandwidth
from unilog.analytics.aliases import RESPONSE_SIZE_FIELDS

from unilog.analytics.helpers import extract_numeric_field, normalize_endpoint

@register_analyzer("bandwidth", produces=BandwidthMetrics, dependencies=["traffic"])
class BandwidthAnalyzer(BaseAnalyzer):
    """Aggregate total bytes transferred, throughput rate, and rank top bandwidth consuming routes."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> BaseModel:
        total_bytes_sent = 0
        endpoint_bytes: dict[str, int] = {}
        
        for record in records:
            bytes_sent = 0
            val = extract_numeric_field(record, RESPONSE_SIZE_FIELDS)
            if val is not None:
                bytes_sent = int(val)
                total_bytes_sent += bytes_sent
                            
            endpoint = normalize_endpoint(record)
            endpoint_bytes[endpoint] = endpoint_bytes.get(endpoint, 0) + bytes_sent
            
        window_seconds = context.window_minutes * 60
        bytes_per_second = float(total_bytes_sent / window_seconds) if window_seconds > 0 else 0.0
        
        sorted_endpoints = sorted(endpoint_bytes.items(), key=lambda x: x[1], reverse=True)
        top_bandwidth_endpoints = []
        for endpoint, val in sorted_endpoints:
            percentage = float((val / total_bytes_sent) * 100.0) if total_bytes_sent > 0 else 0.0
            top_bandwidth_endpoints.append(
                EndpointBandwidth(
                    endpoint=endpoint,
                    bytes_sent=val,
                    percentage=percentage
                )
            )
            
        return BandwidthMetrics(
            total_bytes_sent=total_bytes_sent,
            bytes_per_second=bytes_per_second,
            top_bandwidth_endpoints=top_bandwidth_endpoints[:5]
        )
