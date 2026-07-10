import io
import sys
import pandas as pd  # type: ignore
from typing import Generator, Dict, Any, Optional, List

from unilog.detector import detect as detect_format
from unilog.registry import get_parser, register_parser
from unilog.utils import read_file
from unilog.parsers.base import BaseParser

def stream(path_or_stream: Any, format: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Stream parsed log records one line at a time.
    """
    # 1. Determine format and parser
    parser_inst: Optional[BaseParser] = None
    buffered_lines: List[str] = []

    # Check if we need auto-detection
    if not format or format == "auto":
        # We need to sample lines to detect
        if isinstance(path_or_stream, io.TextIOBase) or path_or_stream == "-":
            # For stream or stdin, we must read the sample lines and buffer them
            stream_obj = sys.stdin if path_or_stream == "-" else path_or_stream
            for _ in range(50):
                line = stream_obj.readline()
                if not line:
                    break
                buffered_lines.append(line)
            
            # Detect using the buffer
            det_res = detect_format(buffered_lines)
            parser_inst = det_res["parser_instance"]
        else:
            # For standard files, we can sample without consuming the main stream
            det_res = detect_format(path_or_stream)
            parser_inst = det_res["parser_instance"]
    else:
        # Load from registry
        parser_cls = get_parser(format)
        if parser_cls:
            parser_inst = parser_cls()

    # If no parser found, we'll return raw logs with _parse_error = True or use fallback
    # In core, let's fall back to a generic parser or raw dict representation
    
    # 2. Iterate and parse
    # If we have buffered lines, yield them first
    if buffered_lines:
        for line in buffered_lines:
            line_str = line.rstrip("\r\n")
            if not line_str.strip():
                continue
            if parser_inst:
                yield parser_inst.parse_line(line_str)
            else:
                yield {"_parse_error": True, "raw": line_str}

    # Now read the rest of the stream/file
    # If path_or_stream was stdin/stream, we just read the rest of it.
    # Otherwise, we open the file path from start.
    if isinstance(path_or_stream, io.TextIOBase) or path_or_stream == "-":
        stream_obj = sys.stdin if path_or_stream == "-" else path_or_stream
        for line in stream_obj:
            line_str = line.rstrip("\r\n")
            if not line_str.strip():
                continue
            if parser_inst:
                yield parser_inst.parse_line(line_str)
            else:
                yield {"_parse_error": True, "raw": line_str}
    else:
        # For standard files, read from the beginning
        for line in read_file(path_or_stream):
            line_str = line.rstrip("\r\n")
            if not line_str.strip():
                continue
            if parser_inst:
                yield parser_inst.parse_line(line_str)
            else:
                yield {"_parse_error": True, "raw": line_str}

def parse(path_or_stream: Any, format: Optional[str] = None) -> pd.DataFrame:
    """
    Parse log file/stream and return a pandas DataFrame.
    """
    records = list(stream(path_or_stream, format=format))
    if not records:
        return pd.DataFrame()
    return pd.DataFrame.from_records(records)

def parse_string(log_text: str, format: Optional[str] = None) -> pd.DataFrame:
    """
    Parse a string of log text (multiple lines) and return a DataFrame.
    """
    stream_obj = io.StringIO(log_text)
    return parse(stream_obj, format=format)

def detect(path_or_stream: Any) -> Dict[str, Any]:
    """
    Detect log format of the given path/stream.
    Returns: {"format": str, "confidence": float}
    """
    res = detect_format(path_or_stream)
    return {
        "format": res["format"],
        "confidence": res["confidence"]
    }

def stats(path_or_stream: Any) -> Dict[str, Any]:
    """
    Quick statistics summary of the log file.
    We will fully implement this once stats plugins are wired.
    """
    # Simple default stats for now
    df = parse(path_or_stream)
    if df.empty:
        return {"total_lines": 0, "format": "unknown", "error_rate": 0.0}
    
    total_lines = len(df)
    errors = df.get("_parse_error", pd.Series([False]*total_lines))
    error_rate = errors.sum() / total_lines if total_lines else 0.0
    
    # Try to find format name
    det = detect(path_or_stream)
    
    return {
        "total_lines": total_lines,
        "format": det["format"],
        "error_rate": round(error_rate, 4)
    }

def anomalies(path_or_stream: Any) -> pd.DataFrame:
    """
    Analyze log file and return a DataFrame of anomalies.
    Will be implemented in anomaly module.
    """
    return pd.DataFrame()

def register_format(name: str, pattern: str, timestamp_field: Optional[str] = None, timestamp_format: Optional[str] = None):
    """
    Public API to register a custom format with registry.
    """
    from unilog.parsers.custom import CustomParser
    # Dynamically build a class and register it
    class_name = f"Custom_{name}"
    custom_class = type(
        class_name,
        (CustomParser,),
        {
            "name": name,
            "description": f"Custom format: {name}",
            "priority": 50,
            "supported_extensions": [],
            "pattern_str": pattern,
            "timestamp_field": timestamp_field,
            "timestamp_format": timestamp_format
        }
    )
    # Instantiate to validate regex and named groups immediately
    custom_class()
    register_parser(custom_class)
