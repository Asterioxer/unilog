import pandas as pd  # type: ignore
from typing import Dict, Any, List, Type

# Registry of stats plugins
_stats_plugins: List[Type["StatsPlugin"]] = []

class StatsPlugin:
    """Base interface for all statistics plugins."""
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        _stats_plugins.append(cls)

    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute statistics on the DataFrame. Returns a dict."""
        raise NotImplementedError


# ==============================================================================
# PUBLIC AGGREGATOR FUNCTION
# ==============================================================================

def aggregate_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute aggregate statistics on the DataFrame by running built-in metrics and custom plugins."""
    results: Dict[str, Any] = {}

    if df.empty:
        results.update({
            "total_lines": 0,
            "error_rate": 0.0,
            "http_5xx_rate": 0.0,
            "time_range": None,
            "top_ips": [],
            "log_levels": {},
            "status_codes": {},
            "request_methods": {},
            "top_endpoints": [],
            "bytes_transferred": 0,
        })
    else:
        total = len(df)
        results["total_lines"] = total

        # Error rate & 5xx rate
        parse_errors = 0
        if "_parse_error" in df.columns:
            parse_errors = int(df["_parse_error"].fillna(False).sum())
        
        http_errors = 0
        if "status_code" in df.columns:
            http_errors = int(((df["status_code"] >= 500) & (df["status_code"] < 600)).sum())
            
        results["error_rate"] = round(parse_errors / total, 4) if total else 0.0
        results["http_5xx_rate"] = round(http_errors / total, 4) if total else 0.0

        # Time range
        if "timestamp" in df.columns:
            ts_series = df["timestamp"].dropna()
            if not ts_series.empty:
                try:
                    min_ts = ts_series.min()
                    max_ts = ts_series.max()
                    min_str = min_ts.isoformat() if hasattr(min_ts, "isoformat") else str(min_ts)
                    max_str = max_ts.isoformat() if hasattr(max_ts, "isoformat") else str(max_ts)
                    results["time_range"] = (min_str, max_str)
                except Exception:
                    results["time_range"] = None
            else:
                results["time_range"] = None
        else:
            results["time_range"] = None

        # Top IPs
        ip_col = None
        for col in ["source_ip", "ip", "client_ip"]:
            if col in df.columns:
                ip_col = col
                break
        if ip_col:
            counts = df[ip_col].dropna().value_counts().head(5)
            results["top_ips"] = [[ip, int(count)] for ip, count in counts.items()]
        else:
            results["top_ips"] = []

        # Log Levels
        if "level" in df.columns:
            counts = df["level"].dropna().value_counts()
            results["log_levels"] = {str(lvl): int(cnt) for lvl, cnt in counts.items()}
        else:
            results["log_levels"] = {}

        # Status Code Distribution
        status_col = None
        for col in ["status_code", "status"]:
            if col in df.columns:
                status_col = col
                break
        if status_col:
            counts = df[status_col].dropna().value_counts()
            results["status_codes"] = {
                str(int(sc) if isinstance(sc, (int, float)) else sc): int(cnt)
                for sc, cnt in counts.items()
            }
        else:
            results["status_codes"] = {}

        # Request Methods
        if "method" in df.columns:
            counts = df["method"].dropna().value_counts()
            results["request_methods"] = {str(m): int(cnt) for m, cnt in counts.items()}
        else:
            results["request_methods"] = {}

        # Top Endpoints
        path_col = None
        for col in ["path", "request_path", "uri", "endpoint"]:
            if col in df.columns:
                path_col = col
                break
        if path_col:
            counts = df[path_col].dropna().value_counts().head(5)
            results["top_endpoints"] = [[path, int(count)] for path, count in counts.items()]
        else:
            results["top_endpoints"] = []

        # Bytes Transferred
        size_col = None
        for col in ["size", "bytes_sent", "body_bytes_sent"]:
            if col in df.columns:
                size_col = col
                break
        if size_col:
            try:
                total_bytes = int(pd.to_numeric(df[size_col], errors="coerce").fillna(0).sum())
                results["bytes_transferred"] = total_bytes
            except Exception:
                results["bytes_transferred"] = 0
        else:
            results["bytes_transferred"] = 0

    # Custom stats plugins execution
    for plugin_cls in _stats_plugins:
        try:
            plugin_inst = plugin_cls()
            results.update(plugin_inst.compute(df))
        except Exception:
            pass

    return results
