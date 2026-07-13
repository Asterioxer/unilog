"""Shared extraction and normalization helper functions for record attributes."""

from datetime import datetime
from typing import Any, Mapping, Optional, Sequence
from unilog.utils import normalize_timestamp


def extract_numeric_field(record: Mapping[str, Any], aliases: Sequence[str]) -> Optional[float]:
    """Safely extract the first matching numerical field value from aliases."""
    for field in aliases:
        if field in record:
            val = record[field]
            if val is not None and val != "-":
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
    return None


def normalize_endpoint(record: Mapping[str, Any]) -> str:
    """Extract and normalize the endpoint path consistently across analyzers."""
    path = record.get("path") or record.get("request_path") or record.get("request")
    if not path:
        return "unknown"
    path_str = str(path).strip()
    parts = path_str.split()
    if len(parts) >= 2:
        # Match "GET /path HTTP/1.1" -> "/path"
        return parts[1]
    elif len(parts) == 1:
        return parts[0]
    return "unknown"


def extract_timestamp(record: Mapping[str, Any]) -> Optional[datetime]:
    """Safely extract and normalize record timestamp to a datetime object."""
    ts_val = record.get("timestamp")
    if not ts_val:
        return None
    if isinstance(ts_val, datetime):
        return ts_val
    if isinstance(ts_val, str):
        return normalize_timestamp(ts_val)
    return None
