import gzip
import io
import os
import sys
from typing import Generator, List, Optional, Union, Any
from datetime import datetime
from dateutil import parser as date_parser  # type: ignore

def safe_int(val: Any) -> Optional[int]:
    """Safely convert a value to an integer, returning None on failure."""
    if val is None:
        return None
    try:
        # Strip string of quotes, spaces
        if isinstance(val, str):
            val = val.strip().strip('"\'')
            if not val or val == '-':
                return None
        return int(val)
    except (ValueError, TypeError):
        return None

def normalize_timestamp(raw: str, fmt: Optional[str] = None) -> Optional[datetime]:
    """Parse raw timestamp string to datetime object using dateutil or specific format."""
    if not raw:
        return None
    
    # Strip brackets or quotes commonly surrounding timestamps
    raw = raw.strip('[]"\' ')
    if not raw or raw == '-':
        return None

    if fmt:
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            pass

    # Try common fallback logic
    try:
        return date_parser.parse(raw)
    except Exception:
        # Custom logic for some common complex formats (e.g., Apache/Nginx '%d/%b/%Y:%H:%M:%S %z')
        try:
            # e.g., "10/Jul/2026:20:53:59 +0530" -> replace first colon to space
            if ':' in raw and '/' in raw:
                parts = raw.split(':', 1)
                modified_raw = ' '.join(parts)
                return date_parser.parse(modified_raw)
        except Exception:
            pass
        return None

def validate_path_safety(path: str) -> str:
    """
    Normalizes the path using realpath. If UNILOG_SANDBOX_ROOT environment variable
    is defined, validates that the path resolves to a location within the sandbox.
    """
    resolved = os.path.realpath(path)
    sandbox_root = os.getenv("UNILOG_SANDBOX_ROOT")
    if sandbox_root:
        allowed_dir = os.path.realpath(sandbox_root)
        try:
            common = os.path.commonpath([resolved, allowed_dir])
            if os.path.realpath(common) != allowed_dir:
                raise PermissionError(f"Access denied: path '{path}' escapes the sandbox root '{sandbox_root}'.")
        except ValueError:
            # Different drives on Windows mean it's definitely not inside the sandbox
            raise PermissionError(f"Access denied: path '{path}' escapes the sandbox root '{sandbox_root}'.")
    return resolved


def read_file(path: Union[str, io.TextIOBase]) -> Generator[str, None, None]:
    """
    Reads a file handle or path line-by-line, handling gzip compression,
    encoding detection (UTF-8, fall back to latin-1), and stdin if specified.
    """
    if isinstance(path, io.TextIOBase):
        for line in path:
            yield line
        return

    if path == "-" or path is sys.stdin:
        for line in sys.stdin:
            yield line
        return

    # Resolve real path and enforce sandbox security constraints
    clean_path = validate_path_safety(path)
    is_gzip = str(clean_path).endswith(".gz")
    open_func = gzip.open if is_gzip else open

    try:
        with open_func(clean_path, "rt", encoding="utf-8") as f:
            for line in f:
                yield line
    except UnicodeDecodeError:
        with open_func(clean_path, "rt", encoding="latin-1") as f:
            for line in f:
                yield line

def sample_lines(path: Union[str, io.TextIOBase, List[str]], n: int = 50) -> List[str]:
    """Read first n lines from path/stream/list for detection."""
    if isinstance(path, list):
        return path[:n]
    lines = []
    try:
        # If it's stdin/stream and we consume from it, we might lose lines.
        # But for files, we open it, read N lines, and close.
        # If it is a string path, we can re-open it. If it is already a stream, we just read from it.
        if isinstance(path, io.TextIOBase) or path == "-":
            # For stream/stdin, we read up to n lines but we cannot "unread" them.
            # However, during detection we need these lines.
            # We can store them in a buffer if needed, but simple reading is fine.
            # In CLI we might read stdin fully or sample it.
            # We'll just read from it.
            stream = sys.stdin if path == "-" else path
            for _ in range(n):
                line = stream.readline()  # type: ignore
                if not line:
                    break
                lines.append(line)
        else:
            clean_path = validate_path_safety(path)
            is_gzip = str(clean_path).endswith(".gz")
            open_func = gzip.open if is_gzip else open
            try:
                with open_func(clean_path, "rt", encoding="utf-8") as f:
                    for _ in range(n):
                        line = f.readline()
                        if not line:
                            break
                        lines.append(line)
            except UnicodeDecodeError:
                with open_func(clean_path, "rt", encoding="latin-1") as f:
                    for _ in range(n):
                        line = f.readline()
                        if not line:
                            break
                        lines.append(line)
    except Exception:
        pass
    return lines
