import io
import sys
import pandas as pd  # type: ignore
from typing import Generator, Dict, Any, Optional, List, Union

from unilog.detector import detect as detect_format
from unilog.registry import get_parser, register_parser
from unilog.utils import read_file
from unilog.parsers.base import BaseParser
from unilog.stats import aggregate_stats

def stream(path_or_stream: Any, format: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Stream parsed log records one line at a time from a path or stream.
    
    This iterator is lazy, memory efficient, handles exceptions,
    and supports graceful interruption.
    """
    parser_inst: Optional[BaseParser] = None
    buffered_lines: List[str] = []

    # File existence check
    if isinstance(path_or_stream, str) and path_or_stream != "-":
        import os
        from unilog.utils import validate_path_safety
        clean_path = validate_path_safety(path_or_stream)
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path_or_stream}'")
        path_or_stream = clean_path

    try:
        # 1. Determine format and parser
        if not format or format == "auto":
            # For stream or stdin, we must read the sample lines and buffer them
            if isinstance(path_or_stream, io.TextIOBase) or path_or_stream == "-":
                stream_obj = sys.stdin if path_or_stream == "-" else path_or_stream
                for _ in range(50):
                    line = stream_obj.readline()
                    if not line:
                        break
                    buffered_lines.append(line)
                
                det_res = detect_format(buffered_lines)
                parser_inst = det_res["parser"]
            else:
                det_res = detect_format(path_or_stream)
                parser_inst = det_res["parser"]
        else:
            parser_cls = get_parser(format)
            if parser_cls:
                parser_inst = parser_cls()

        # 2. Iterate and parse
        # Yield buffered lines first
        if buffered_lines:
            for line in buffered_lines:
                line_str = line.rstrip("\r\n")
                if not line_str.strip():
                    continue
                if parser_inst:
                    yield parser_inst.parse_line(line_str)
                else:
                    yield {"_parse_error": True, "raw": line_str}

        # Yield rest of the stream
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
            for line in read_file(path_or_stream):
                line_str = line.rstrip("\r\n")
                if not line_str.strip():
                    continue
                if parser_inst:
                    yield parser_inst.parse_line(line_str)
                else:
                    yield {"_parse_error": True, "raw": line_str}

    except KeyboardInterrupt:
        # Graceful interruption
        return
    except (FileNotFoundError, PermissionError):
        raise
    except Exception:
        # Standard iterator safety
        return

def parse(
    path_or_stream: Any,
    format: Optional[str] = None,
    chunksize: Optional[int] = None
) -> Union[pd.DataFrame, Generator[pd.DataFrame, None, None]]:
    """
    Parse a log file or stream and return a pandas DataFrame.
    
    If `chunksize` is specified, returns an iterator yielding DataFrames of size `chunksize`.
    Otherwise, builds the DataFrame using chunked memory construction for speed and low memory.
    """
    gen = stream(path_or_stream, format=format)
    
    if chunksize is not None:
        if chunksize <= 0:
            raise ValueError("chunksize must be greater than 0")
            
        def chunk_generator() -> Generator[pd.DataFrame, None, None]:
            chunk: List[Dict[str, Any]] = []
            try:
                for record in gen:
                    chunk.append(record)
                    if len(chunk) == chunksize:
                        yield pd.DataFrame.from_records(chunk)
                        chunk = []
                if chunk:
                    yield pd.DataFrame.from_records(chunk)
            except KeyboardInterrupt:
                if chunk:
                    yield pd.DataFrame.from_records(chunk)
                return
        return chunk_generator()

    # Performance optimization: Chunked DataFrame construction to avoid huge list overhead
    chunk_size_internal = 50000
    dfs: List[pd.DataFrame] = []
    chunk: List[Dict[str, Any]] = []
    
    for record in gen:
        chunk.append(record)
        if len(chunk) == chunk_size_internal:
            dfs.append(pd.DataFrame.from_records(chunk))
            chunk = []
            
    if chunk:
        dfs.append(pd.DataFrame.from_records(chunk))
        
    if not dfs:
        return pd.DataFrame()
        
    return pd.concat(dfs, ignore_index=True)

def parse_string(log_text: str, format: Optional[str] = None) -> pd.DataFrame:
    """
    Parse a string of log text (multiple lines) and return a DataFrame.

    If the selected parser overrides parse() (e.g. WindowsParser for multi-line
    Event Viewer CSV), it is called directly so the parser can reassemble
    records that span multiple physical lines.  Otherwise falls back to the
    standard stream() / parse_line() path.
    """
    # Resolve parser
    parser_inst: Optional[BaseParser] = None
    if format and format not in ("auto", "unknown", ""):
        parser_cls = get_parser(format)
        if parser_cls:
            parser_inst = parser_cls()

    if parser_inst is None:
        # Auto-detect: first try document-level detection on the full text
        det = detect_format(io.StringIO(log_text))
        if det["format"] != "unknown" and det["parser"]:
            parser_inst = det["parser"]
        else:
            # Fallback: try each parser's parse() directly to find one that succeeds
            from unilog.registry import list_formats
            for fmt in list_formats():
                parser_cls = fmt["class"]
                candidate = parser_cls()
                # Use the candidate with best confidence on a small sample
                sample = log_text[:4096]
                sample_lines = [l for l in sample.splitlines() if l.strip()][:50]
                if sample_lines and candidate.confidence_score(sample_lines) > 0:
                    parser_inst = candidate
                    break

    if parser_inst is not None:
        # Use parser.parse() if the subclass overrides it
        base_parse = getattr(BaseParser, 'parse', None)
        inst_parse = getattr(parser_inst, 'parse', None)
        if inst_parse and inst_parse != base_parse:
            try:
                records = list(parser_inst.parse(log_text))
                if records:
                    return pd.DataFrame.from_records(records)
            except Exception:
                pass  # fall through to stream() path

    # Standard line-by-line path
    stream_obj = io.StringIO(log_text)
    df = parse(stream_obj, format=format)
    if isinstance(df, pd.DataFrame):
        return df
    return pd.concat(list(df), ignore_index=True)


def detect(path_or_stream: Any) -> Dict[str, Any]:
    """
    Detect log format of the given path/stream/list.
    Returns: {"format": str, "confidence": float, "parser": ..., "rankings": [...], "reason": ...}
    """
    return detect_format(path_or_stream)

def stats(path_or_stream: Any) -> Dict[str, Any]:
    """
    Compute aggregate statistics summary of a log file/stream.
    """
    df = parse(path_or_stream)
    if not isinstance(df, pd.DataFrame):
        # Handle chunksize if it accidentally returns a generator
        df = pd.concat(list(df), ignore_index=True)
        
    raw_lines = []
    if not df.empty and "raw" in df.columns:
        raw_lines = df["raw"].dropna().head(50).tolist()
        
    det = detect(raw_lines)
    results = aggregate_stats(df)
    results["format"] = det["format"]
    return results

def anomalies(path_or_stream: Any) -> pd.DataFrame:
    """
    Identify anomalies in the log file.
    (Detailed statistics-based logic to be wired in Phase 5).
    """
    df = parse(path_or_stream)
    if not isinstance(df, pd.DataFrame):
        df = pd.concat(list(df), ignore_index=True)
    # Phase 3: return empty DataFrame with 'anomaly_reason' column to preserve API contract
    if df.empty:
        return pd.DataFrame(columns=["anomaly_reason"])
    df["anomaly_reason"] = None
    return df.iloc[0:0].copy() # Return empty DataFrame with identical columns + anomaly_reason

def register_format(
    name: str,
    pattern: str,
    timestamp_field: Optional[str] = None,
    timestamp_format: Optional[str] = None
):
    """
    Register a custom format by name.
    """
    from unilog.parsers.custom import CustomParser
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
