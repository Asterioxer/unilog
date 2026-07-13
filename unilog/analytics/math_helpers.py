"""Mathematical and statistical summarizers for analytics data."""

import math
from typing import List, Optional
from unilog.analytics.schemas import SizeDistribution


def calculate_percentile(values: List[float], percentile: float) -> Optional[float]:
    """Gracefully calculate percentile values, returning None on empty lists."""
    if not values:
        return None
    
    values_sorted = sorted(values)
    length = len(values_sorted)
    
    if length == 1:
        return float(values_sorted[0])
    
    # Standard linear interpolation
    k = (length - 1) * (percentile / 100.0)
    idx_floor = math.floor(k)
    idx_ceil = math.ceil(k)
    
    if idx_floor == idx_ceil:
        return float(values_sorted[int(k)])
        
    val_floor = values_sorted[idx_floor]
    val_ceil = values_sorted[idx_ceil]
    
    return float(val_floor + (val_ceil - val_floor) * (k - idx_floor))


def compute_size_distribution(values: List[int], bucket_size: int) -> SizeDistribution:
    """Summarize a list of integer sizes into a structured SizeDistribution."""
    count = len(values)
    if count == 0:
        return SizeDistribution(count=0)
        
    float_values = [float(v) for v in values]
    average = float(sum(values) / count)
    minimum = int(min(values))
    maximum = int(max(values))
    
    p50 = calculate_percentile(float_values, 50.0)
    p95 = calculate_percentile(float_values, 95.0)
    
    # Generate straightforward fixed-bin histogram binnings
    histogram: dict[str, int] = {}
    for val in values:
        bucket_idx = int(val // bucket_size)
        bucket_start = bucket_idx * bucket_size
        bucket_end = bucket_start + bucket_size - 1
        bucket_label = f"{bucket_start}-{bucket_end}"
        histogram[bucket_label] = histogram.get(bucket_label, 0) + 1
        
    return SizeDistribution(
        count=count,
        average=average,
        minimum=minimum,
        maximum=maximum,
        p50=p50,
        p95=p95,
        histogram=histogram
    )
