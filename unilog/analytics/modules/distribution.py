from typing import Any, Mapping, Sequence
from pydantic import BaseModel
from unilog.analytics.base import BaseAnalyzer, AnalyzerContext
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import DistributionMetrics, IPMetric
from unilog.analytics.aliases import REQUEST_SIZE_FIELDS, RESPONSE_SIZE_FIELDS
from unilog.analytics.math_helpers import compute_size_distribution

@register_analyzer("distribution", produces=DistributionMetrics)
class DistributionAnalyzer(BaseAnalyzer):
    """Summarize IP address query volumes and payload body size distributions."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> BaseModel:
        ip_counts: dict[str, int] = {}
        request_sizes = []
        response_sizes = []
        
        for record in records:
            # IP address frequency
            ip = record.get("source_ip") or record.get("ip")
            if ip and ip != "-":
                ip_counts[ip] = ip_counts.get(ip, 0) + 1
                
            # Request sizes
            for field in REQUEST_SIZE_FIELDS:
                if field in record:
                    val = record[field]
                    if val is not None and val != "-":
                        try:
                            request_sizes.append(int(float(val)))
                            break
                        except (ValueError, TypeError):
                            pass
                            
            # Response sizes
            for field in RESPONSE_SIZE_FIELDS:
                if field in record:
                    val = record[field]
                    if val is not None and val != "-":
                        try:
                            response_sizes.append(int(float(val)))
                            break
                        except (ValueError, TypeError):
                            pass
                            
        # Sort IP metrics descending
        sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)
        top_ips = [IPMetric(ip=ip, requests=count) for ip, count in sorted_ips]
        
        req_dist = compute_size_distribution(request_sizes, context.histogram_bucket_size)
        resp_dist = compute_size_distribution(response_sizes, context.histogram_bucket_size)
        
        return DistributionMetrics(
            top_ips=top_ips,
            request_sizes=req_dist,
            response_sizes=resp_dist
        )
