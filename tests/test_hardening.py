import io
import os
import gzip
import pytest
import tempfile
import pandas as pd

import unilog
from unilog.parsers.base import BaseParser
from unilog.parsers.json_log import JSONParser
from unilog.parsers.nginx import NginxParser
from unilog.parsers.apache import ApacheParser
from unilog.parsers.syslog import SyslogParser
from unilog.parsers.django import DjangoParser
from unilog.parsers.windows import WindowsParser
from unilog.registry import register_parser, get_parser, list_formats, _registry
from unilog.utils import read_file, safe_int

# ==============================================================================
# TASK 8 - PUBLIC API STABILITY
# ==============================================================================

def test_public_api_exports():
    assert hasattr(unilog, "parse")
    assert hasattr(unilog, "parse_string")
    assert hasattr(unilog, "detect")
    assert hasattr(unilog, "stream")
    assert hasattr(unilog, "stats")
    assert hasattr(unilog, "anomalies")
    assert hasattr(unilog, "register_parser")
    assert hasattr(unilog, "list_formats")


# ==============================================================================
# TASK 7 - PARSER ROBUSTNESS (NO EXCEPTIONS ON MALFORMED INPUT)
# ==============================================================================

@pytest.mark.parametrize("parser_cls", [
    JSONParser, NginxParser, ApacheParser, SyslogParser, DjangoParser, WindowsParser
])
def test_parser_robustness(parser_cls):
    parser = parser_cls()
    malformed_inputs = [
        "",
        "   ",
        "\n",
        "A" * 10000,  # Extremely long line
        "{malformed json}",
        "127.0.0.1 - - [invalid_date] \"GET / HTTP/1.1\" invalid_status invalid_size",
        "<invalid_priority>not a syslog line",
        "[2026-07-10 12:00:00] NOT_A_LEVEL not_a_logger: missing message",
        "Level,Date and Time,Source\nError,2026-07-10,Src",  # short CSV row
        "<Event><MalformedXml>",
    ]
    for inp in malformed_inputs:
        # None of the parsers should raise unexpected exceptions
        try:
            res = parser.parse_line(inp)
            # If the parser did not match, it must return _parse_error = True
            # (or for Windows CSV header it skips/returns error)
            if not parser.match(inp) or res.get("_parse_error"):
                assert res.get("_parse_error") is True
        except Exception as e:
            pytest.fail(f"{parser_cls.__name__} raised unexpected exception {type(e).__name__} on input: {inp}")


# ==============================================================================
# TASK 2 - PARSER EDGE CASES
# ==============================================================================

def test_empty_and_whitespace_files():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write("")
        empty_path = f.name
    try:
        df = unilog.parse(empty_path)
        assert isinstance(df, pd.DataFrame)
        assert df.empty
    finally:
        os.remove(empty_path)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write("   \n\t\n   \n")
        ws_path = f.name
    try:
        df = unilog.parse(ws_path)
        assert isinstance(df, pd.DataFrame)
        assert df.empty
    finally:
        os.remove(ws_path)

def test_latin1_fallback():
    # Write latin-1 character (é = \xe9)
    latin1_data = b"127.0.0.1 - - [10/Jul/2026:12:00:00 +0000] \"GET /caf\xe9 HTTP/1.1\" 200 123\n"
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
        f.write(latin1_data)
        path = f.name
    try:
        # Should fall back to latin-1 and parse successfully
        df = unilog.parse(path)
        assert len(df) == 1
        assert df.loc[0, "path"] == "/café"
    finally:
        os.remove(path)

def test_gzip_compressed_logs():
    log_line = '{"time": "2026-07-10T12:00:00Z", "level": "info", "msg": "started"}\n'
    with tempfile.NamedTemporaryFile(suffix=".log.gz", delete=False) as f:
        path = f.name
    try:
        with gzip.open(path, "wt", encoding="utf-8") as gf:
            gf.write(log_line)
        
        # Test utils read_file on gzip
        lines = list(read_file(path))
        assert len(lines) == 1
        assert "started" in lines[0]

        # Test parse on gzip
        df = unilog.parse(path)
        assert len(df) == 1
        assert df.loc[0, "message"] == "started"
    finally:
        os.remove(path)

def test_unicode_and_special_chars():
    # Test message with emoji and unicode
    log_text = '{"time": "2026-07-10T12:00:00Z", "level": "info", "msg": "🚀 success \u4e2d\u6587"}'
    df = unilog.parse_string(log_text)
    assert len(df) == 1
    assert df.loc[0, "message"] == "🚀 success 中文"

def test_numeric_edge_cases():
    # Large numbers, negatives, nulls
    assert safe_int("999999999999999999") == 999999999999999999
    assert safe_int("-123") == -123
    assert safe_int("0") == 0
    assert safe_int(None) is None
    assert safe_int("-") is None
    assert safe_int("not_a_number") is None

def test_escaped_quotes_and_commas_csv():
    # Windows CSV parsing testing commas in quotes
    line = '"Error","2026-07-10 12:00:00","Disk, Controller",7,"None","Failed, error code: ""0x8000""."'
    parser = WindowsParser()
    res = parser.parse_line(line)
    assert not res.get("_parse_error")
    assert res["source"] == "Disk, Controller"
    assert res["message"] == 'Failed, error code: "0x8000".'

def test_mixed_format_log_files():
    # Mixed formats: Nginx, then Django, then garbage
    lines = [
        '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /api HTTP/1.1" 200 456',
        '[2026-07-10 12:00:00] INFO django.request: GET /api 200 45ms',
        'completely malformed garbage line'
    ]
    # If format is "nginx" (or auto-detected as nginx)
    # The django line and the garbage line should parse to _parse_error: True
    df = unilog.parse_string("\n".join(lines), format="nginx")
    assert len(df) == 3
    assert df.loc[0, "status_code"] == 200
    assert df.loc[1, "_parse_error"] is True
    assert df.loc[2, "_parse_error"] is True


# ==============================================================================
# TASK 3 - STREAMING VALIDATION
# ==============================================================================

def test_streaming_validation():
    # Test lazy generation
    lines = [
        '{"time": "2026-07-10T12:00:00Z", "level": "info", "msg": "line1"}',
        '{"time": "2026-07-10T12:00:01Z", "level": "warn", "msg": "line2"}'
    ]
    log_text = "\n".join(lines)
    
    # Check that stream yields records correctly
    stream_generator = unilog.stream(io.StringIO(log_text), format="json")
    
    records = []
    # Fetch first record
    records.append(next(stream_generator))
    assert records[0]["message"] == "line1"
    
    # Fetch second
    records.append(next(stream_generator))
    assert records[1]["message"] == "line2"
    
    # Assert termination
    with pytest.raises(StopIteration):
        next(stream_generator)

    # Assert parse() produces the same records as stream()
    df = unilog.parse_string(log_text, format="json")
    assert len(df) == 2
    assert df.loc[0, "message"] == "line1"
    assert df.loc[1, "message"] == "line2"


# ==============================================================================
# TASK 4 - DETECTOR VALIDATION
# ==============================================================================

def test_detector_validation():
    # Unknown formats
    assert unilog.detect(io.StringIO("garbage string that matches nothing"))["format"] == "unknown"
    
    # Threshold behavior
    # Low match ratio should result in unknown
    sample = [
        '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /api HTTP/1.1" 200 456',
        'random line',
        'random line',
        'random line'
    ]
    # Only 1 out of 4 matches (25% match ratio) -> below 0.6 threshold -> unknown
    stream_obj = io.StringIO("\n".join(sample))
    assert unilog.detect(stream_obj)["format"] == "unknown"

    # Extension heuristic
    # Check that detector gives a slight confidence bump for file extension
    # We create a dummy file with nginx logs named test.log
    with tempfile.NamedTemporaryFile(suffix=".log", mode="w", delete=False) as f:
        f.write('127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /api HTTP/1.1" 200 456\n')
        path_log = f.name
    with tempfile.NamedTemporaryFile(suffix=".dat", mode="w", delete=False) as f:
        f.write('127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /api HTTP/1.1" 200 456\n')
        path_dat = f.name
    try:
        res_log = unilog.detector.detect(path_log)
        res_dat = unilog.detector.detect(path_dat)
        assert res_log["format"] == "nginx"
        assert res_dat["format"] == "nginx"
        # .log has extension bump (+0.05)
        assert res_log["confidence"] > res_dat["confidence"]
    finally:
        os.remove(path_log)
        os.remove(path_dat)


# ==============================================================================
# TASK 5 - REGISTRY VALIDATION
# ==============================================================================

def test_registry_validation():
    # Duplicate registration (should overwrite/succeed)
    @register_parser
    class TempParser(BaseParser):
        name = "temp_format"
        description = "Temp Parser"
        priority = 5
        def match(self, line): return False
        def parse_line(self, line): return {}

    assert get_parser("temp_format") is TempParser

    # Register second parser with same name
    @register_parser
    class TempParser2(BaseParser):
        name = "temp_format"
        description = "Temp Parser 2"
        priority = 6
        def match(self, line): return False
        def parse_line(self, line): return {}

    assert get_parser("temp_format") is TempParser2

    # Cleanup from registry
    if "temp_format" in _registry:
        del _registry["temp_format"]

    # Rejection of invalid parser names or metadata
    with pytest.raises(ValueError, match="valid non-base name"):
        @register_parser
        class InvalidNameParser(BaseParser):
            name = ""
            def match(self, line): return False
            def parse_line(self, line): return {}

    with pytest.raises(TypeError, match="must inherit from BaseParser"):
        register_parser(dict) # Not a subclass


# ==============================================================================
# TASK 6 - CUSTOM PARSER VALIDATION
# ==============================================================================

def test_custom_parser_invalid_cases():
    # Invalid regex syntax
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        unilog.register_format(name="invalid_regex", pattern=r"[unclosed bracket")

    # Missing named capture groups
    with pytest.raises(ValueError, match="must contain at least one named group"):
        unilog.register_format(name="no_groups", pattern=r"\S+ \w+")

def test_core_stats_and_anomalies():
    # Test unilog.stats
    with tempfile.NamedTemporaryFile(suffix=".log", mode="w", delete=False) as f:
        f.write('{"time": "2026-07-10T12:00:00Z", "level": "info", "msg": "ok"}\n')
        f.write('{"time": "2026-07-10T12:00:01Z", "level": "info", "msg": "ok2"}\n')
        f.write('invalid raw line\n')
        path = f.name
    try:
        s = unilog.stats(path)
        assert s["total_lines"] == 3
        assert s["format"] == "json"
        assert s["error_rate"] == round(1/3, 4)

        # Test unilog.anomalies
        anom = unilog.anomalies(path)
        assert isinstance(anom, pd.DataFrame)
        assert anom.empty
    finally:
        os.remove(path)

    # Empty stats
    s_empty = unilog.stats(io.StringIO(""))
    assert s_empty["total_lines"] == 0
    assert s_empty["error_rate"] == 0.0

def test_stream_unknown_fallback():
    # Test stream on a file with format="auto" but it's unknown/garbage
    log_text = "some random log line\nanother random line"
    df = unilog.parse_string(log_text)
    assert len(df) == 2
    assert bool(df.loc[0, "_parse_error"]) is True
    assert df.loc[0, "raw"] == "some random log line"

def test_registry_metadata_ordering():
    # Verify metadata sorting: priority desc, then name asc
    formats = list_formats()
    assert len(formats) >= 3
    priorities = [f["priority"] for f in formats]
    # Check that priorities are sorted descending
    assert priorities == sorted(priorities, reverse=True)

def test_utils_read_file_stream():
    # Test read_file with stream object
    stream_obj = io.StringIO("line1\nline2\n")
    lines = list(read_file(stream_obj))
    assert lines == ["line1\n", "line2\n"]
