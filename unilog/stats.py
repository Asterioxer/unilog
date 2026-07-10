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
# BUILT-IN PLUGINS
# ==============================================================================

class TotalLinesPlugin(StatsPlugin):
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {"total_lines": len(df)}


class ErrorRatePlugin(StatsPlugin):
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {"error_rate": 0.0}
        
        # Check parsing errors
        parse_errors = 0
        if "_parse_error" in df.columns:
            parse_errors = int(df["_parse_error"].fillna(False).sum())
        
        # Check HTTP 5xx errors if status_code is present
        http_errors = 0
        if "status_code" in df.columns:
            # Match 5xx statuses
            http_errors = int(((df["status_code"] >= 500) & (df["status_code"] < 600)).sum())
            
        total = len(df)
        return {
            "error_rate": round(parse_errors / total, 4) if total else 0.0,
            "http_5xx_rate": round(http_errors / total, 4) if total else 0.0
        }


class TimeRangePlugin(StatsPlugin):
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "timestamp" not in df.columns:
            return {"time_range": None}
        
        # Drop null timestamps
        ts_series = df["timestamp"].dropna()
        if ts_series.empty:
            return {"time_range": None}
            
        try:
            min_ts = ts_series.min()
            max_ts = ts_series.max()
            
            # Format nicely
            min_str = min_ts.isoformat() if hasattr(min_ts, "isoformat") else str(min_ts)
            max_str = max_ts.isoformat() if hasattr(max_ts, "isoformat") else str(max_ts)
            return {"time_range": (min_str, max_str)}
        except Exception:
            return {"time_range": None}


class TopIPsPlugin(StatsPlugin):
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        ip_col = None
        for col in ["source_ip", "ip", "client_ip"]:
            if col in df.columns:
                ip_col = col
                break
                
        if not ip_col or df.empty:
            return {"top_ips": []}
            
        # Get top 5 value counts
        counts = df[ip_col].dropna().value_counts().head(5)
        # Convert to list of [ip, count]
        return {"top_ips": [[ip, int(count)] for ip, count in counts.items()]}


class LogLevelsPlugin(StatsPlugin):
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "level" not in df.columns:
            return {"log_levels": {}}
            
        counts = df["level"].dropna().value_counts()
        return {"log_levels": {str(lvl): int(cnt) for lvl, cnt in counts.items()}}


class StatusCodeDistributionPlugin(StatsPlugin):
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        status_col = None
        for col in ["status_code", "status"]:
            if col in df.columns:
                status_col = col
                break
                
        if not status_col or df.empty:
            return {"status_codes": {}}
            
        counts = df[status_col].dropna().value_counts()
        return {"status_codes": {str(int(sc) if isinstance(sc, (int, float)) else sc): int(cnt) for sc, cnt in counts.items()}}


class RequestMethodsPlugin(StatsPlugin):
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "method" not in df.columns:
            return {"request_methods": {}}
            
        counts = df["method"].dropna().value_counts()
        return {"request_methods": {str(m): int(cnt) for m, cnt in counts.items()}}


class TopEndpointsPlugin(StatsPlugin):
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        path_col = None
        for col in ["path", "request_path", "uri", "endpoint"]:
            if col in df.columns:
                path_col = col
                break
                
        if not path_col or df.empty:
            return {"top_endpoints": []}
            
        counts = df[path_col].dropna().value_counts().head(5)
        return {"top_endpoints": [[path, int(count)] for path, count in counts.items()]}


class BytesTransferredPlugin(StatsPlugin):
    def compute(self, df: pd.DataFrame) -> Dict[str, Any]:
        size_col = None
        for col in ["size", "bytes_sent", "body_bytes_sent"]:
            if col in df.columns:
                size_col = col
                break
                
        if not size_col or df.empty:
            return {"bytes_transferred": 0}
            
        # Sum size, handling strings safely if necessary
        try:
            total_bytes = int(pd.to_numeric(df[size_col], errors="coerce").fillna(0).sum())
            return {"bytes_transferred": total_bytes}
        except Exception:
            return {"bytes_transferred": 0}


# ==============================================================================
# PUBLIC AGGREGATOR FUNCTION
# ==============================================================================

def aggregate_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute aggregate statistics on the DataFrame by running all registered plugins."""
    results = {}
    for plugin_cls in _stats_plugins:
        try:
            plugin_inst = plugin_cls()
            results.update(plugin_inst.compute(df))
        except Exception:
            pass
    return results
