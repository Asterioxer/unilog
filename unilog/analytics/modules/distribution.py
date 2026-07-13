from typing import Any, Mapping, Sequence
from pydantic import BaseModel
from unilog.analytics.base import BaseAnalyzer, AnalyzerContext
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import DistributionMetrics, IPMetric
from unilog.analytics.aliases import REQUEST_SIZE_FIELDS, RESPONSE_SIZE_FIELDS
from unilog.analytics.math_helpers import compute_size_distribution

from unilog.analytics.helpers import extract_numeric_field

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
            req_size = extract_numeric_field(record, REQUEST_SIZE_FIELDS)
            if req_size is not None:
                request_sizes.append(int(req_size))
                            
            # Response sizes
            resp_size = extract_numeric_field(record, RESPONSE_SIZE_FIELDS)
            if resp_size is not None:
                response_sizes.append(int(resp_size))
                            
        # Sort IP metrics descending and limit
        sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)
        top_ips = [
            IPMetric(ip=ip, requests=count) 
            for ip, count in sorted_ips[:context.top_ips_limit]
        ]
        
        req_dist = compute_size_distribution(request_sizes, context.histogram_bucket_size)
        resp_dist = compute_size_distribution(response_sizes, context.histogram_bucket_size)
        
        return DistributionMetrics(
            top_ips=top_ips,
            request_sizes=req_dist,
            response_sizes=resp_dist
        )
