import pytest
import pandas as pd  # type: ignore
from click.testing import CliRunner
from unilog.cli import cli
from unilog.stats import StatsPlugin, aggregate_stats
import unilog

# ==============================================================================
# CLI TESTS
# ==============================================================================

def test_cli_formats():
    runner = CliRunner()
    res = runner.invoke(cli, ["formats"])
    assert res.exit_code == 0
    assert "Registered Log Formats" in res.output
    assert "nginx" in res.output
    assert "json" in res.output

def test_cli_detect():
    runner = CliRunner()
    res = runner.invoke(cli, ["detect", "tests/sample_logs/minimal/nginx.log"])
    assert res.exit_code == 0
    assert "Detected format: nginx" in res.output
    assert "Parser Rankings" in res.output

    # Test threshold
    res_thresh = runner.invoke(cli, ["detect", "tests/sample_logs/minimal/nginx.log", "--threshold", "1.05"])
    assert res_thresh.exit_code == 0
    assert "Could not confidently detect log format" in res_thresh.output

def test_cli_stats():
    runner = CliRunner()
    res = runner.invoke(cli, ["stats", "tests/sample_logs/minimal/nginx.log"])
    assert res.exit_code == 0
    assert "Log Statistics Summary" in res.output
    assert "Total lines: 6" in res.output
    assert "Top Client IPs" in res.output
    assert "127.0.0.1" in res.output

def test_cli_parse_file():
    runner = CliRunner()
    res = runner.invoke(cli, ["parse", "tests/sample_logs/minimal/nginx.log"], env={"COLUMNS": "160"})
    assert res.exit_code == 0
    assert "source_ip" in res.output
    assert "status_code" in res.output

    # JSON output
    res_json = runner.invoke(cli, ["parse", "tests/sample_logs/minimal/nginx.log", "--output", "json"])
    assert res_json.exit_code == 0
    assert "[" in res_json.output
    assert "source_ip" in res_json.output

    # CSV output
    res_csv = runner.invoke(cli, ["parse", "tests/sample_logs/minimal/nginx.log", "--output", "csv"])
    assert res_csv.exit_code == 0
    assert "source_ip," in res_csv.output

def test_cli_parse_stdin():
    runner = CliRunner()
    log_line = '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /api HTTP/1.1" 200 456'
    res = runner.invoke(cli, ["parse", "--stdin", "--format", "nginx"], input=log_line, env={"COLUMNS": "160"})
    assert res.exit_code == 0
    assert "127.0.0.1" in res.output

    # CLI usage error without path/stdin
    res_err = runner.invoke(cli, ["parse"])
    assert res_err.exit_code != 0
    assert "Must provide a log file path or use --stdin flag" in res_err.output

def test_cli_parse_chunksize():
    runner = CliRunner()
    res = runner.invoke(cli, ["parse", "tests/sample_logs/minimal/nginx.log", "--chunksize", "2", "--output", "json"])
    assert res.exit_code == 0
    # Yields JSON lines format
    lines = res.output.strip().split("\n")
    assert len(lines) == 6  # 6 total lines in nginx.log


# ==============================================================================
# STATS PLUGINS AND SYSTEM
# ==============================================================================

def test_custom_stats_plugin():
    # Register custom stats plugin
    class CustomStatsPlugin(StatsPlugin):
        def compute(self, df: pd.DataFrame) -> dict:
            return {"custom_metric": 42}
            
    df = pd.DataFrame([{"raw": "line1"}])
    res = aggregate_stats(df)
    assert "custom_metric" in res
    assert res["custom_metric"] == 42
    
    # Remove custom plugin from registry to avoid polluting other tests
    from unilog.stats import _stats_plugins
    _stats_plugins.remove(CustomStatsPlugin)


# ==============================================================================
# STREAMING & CHUNKING CORE TESTS
# ==============================================================================

def test_parse_chunksize_generator():
    # Test unilog.parse with chunksize
    chunks = unilog.parse("tests/sample_logs/minimal/nginx.log", chunksize=2)
    chunk_list = list(chunks)
    assert len(chunk_list) == 3
    assert all(isinstance(c, pd.DataFrame) for c in chunk_list)
    assert len(chunk_list[0]) == 2
    assert len(chunk_list[1]) == 2
    assert len(chunk_list[2]) == 2

    # Check value validation
    with pytest.raises(ValueError, match="chunksize must be greater than 0"):
        unilog.parse("tests/sample_logs/minimal/nginx.log", chunksize=0)


# ==============================================================================
# DETECTOR RANKINGS & DETAILED API
# ==============================================================================

def test_detector_rankings():
    # Verify detect returns rankings and reason
    res = unilog.detect("tests/sample_logs/minimal/nginx.log")
    assert "rankings" in res
    assert "reason" in res
    assert res["format"] == "nginx"
    assert len(res["rankings"]) > 0
    # First ranking must be nginx
    assert res["rankings"][0]["format"] == "nginx"

def test_cli_error_paths():
    runner = CliRunner()
    # Non-existent file for stats
    res = runner.invoke(cli, ["stats", "non_existent_file.log"])
    assert res.exit_code != 0
    assert "Error generating stats" in res.output

    # Non-existent file for detect
    res_det = runner.invoke(cli, ["detect", "non_existent_file.log"])
    assert res_det.exit_code != 0
    assert "Error detecting format" in res_det.output

    # Non-existent file for parse
    res_prs = runner.invoke(cli, ["parse", "non_existent_file.log"])
    assert res_prs.exit_code != 0
    assert "Error parsing log" in res_prs.output

def test_cli_parse_empty():
    runner = CliRunner()
    # Create empty file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".log", mode="w", delete=False) as f:
        path = f.name
    try:
        res = runner.invoke(cli, ["parse", path])
        assert res.exit_code == 0
        assert "No log records parsed" in res.output
    finally:
        import os
        os.remove(path)

def test_cli_parse_tail_and_chunk_options():
    runner = CliRunner()
    # Test tail in standard parsing
    res = runner.invoke(cli, ["parse", "tests/sample_logs/minimal/nginx.log", "--tail", "2"])
    assert res.exit_code == 0
    
    # Test head/tail combination in chunked parsing
    res_chunk = runner.invoke(cli, ["parse", "tests/sample_logs/minimal/nginx.log", "--chunksize", "2", "--head", "1"])
    assert res_chunk.exit_code == 0

def test_core_generator_fallbacks():
    # Test stats and anomalies when parse returns a generator (chunksize specified)
    # unilog.stats and anomalies internally handle this by concatenating the chunks
    s = unilog.stats("tests/sample_logs/minimal/nginx.log") # standard
    assert s["total_lines"] == 6

    # Test anomalies formatting for non-empty dataframe
    anom = unilog.anomalies("tests/sample_logs/minimal/nginx.log")
    assert isinstance(anom, pd.DataFrame)
    # In Phase 3, anomalies returns empty DataFrame with 'anomaly_reason' column
    assert "anomaly_reason" in anom.columns

def test_stats_plugins_edge_cases():
    # Call stats plugins with completely empty DataFrame
    df_empty = pd.DataFrame()
    s = aggregate_stats(df_empty)
    assert s["total_lines"] == 0
    assert s["top_ips"] == []
    assert s["bytes_transferred"] == 0
    assert s["time_range"] is None

    # Call with missing columns
    df_missing = pd.DataFrame([{"raw": "line1"}])
    s2 = aggregate_stats(df_missing)
    assert s2["total_lines"] == 1
    assert s2["time_range"] is None
    assert s2["top_ips"] == []

def test_generator_fallbacks_mocked():
    from unittest.mock import patch
    import pandas as pd
    
    def dummy_gen():
        yield pd.DataFrame([{"col": 1, "raw": '{"time": "2026-07-10T12:00:00Z", "level": "info", "msg": "ok"}'}])
        yield pd.DataFrame([{"col": 2, "raw": '{"time": "2026-07-10T12:00:01Z", "level": "info", "msg": "ok2"}'}])
        
    with patch("unilog.core.parse", side_effect=lambda *args, **kwargs: dummy_gen()):
        # Call parse_string
        df = unilog.parse_string("dummy string")
        assert len(df) == 2
        assert list(df["col"]) == [1, 2]

        # Call stats
        s = unilog.stats("dummy")
        assert s["total_lines"] == 2

        # Call anomalies
        anom = unilog.anomalies("dummy")
        assert "anomaly_reason" in anom.columns

def test_stream_keyboard_interrupt():
    from unittest.mock import patch
    # Mock read_file to raise KeyboardInterrupt
    with patch("unilog.core.read_file", side_effect=KeyboardInterrupt):
        gen = unilog.stream("tests/sample_logs/minimal/nginx.log", format="nginx")
        res = list(gen)
        assert len(res) == 0

def test_chunk_generator_keyboard_interrupt():
    from unittest.mock import patch
    # Mock stream to raise KeyboardInterrupt during iteration
    def dummy_gen():
        yield {"col": 1}
        raise KeyboardInterrupt
        
    with patch("unilog.core.stream", return_value=dummy_gen()):
        chunks = unilog.parse("dummy_file", chunksize=1)
        res = list(chunks)
        assert len(res) == 1
        assert res[0].loc[0, "col"] == 1

def test_custom_parser_empty_pattern_edge_cases():
    from unilog.parsers.custom import CustomParser
    parser = CustomParser() # pattern_str is empty
    assert parser._pattern is None
    assert parser.match("any line") is False
    assert parser.parse_line("any line") == {"_parse_error": True, "raw": "any line"}
    assert parser.confidence_score([]) == 0.0
    assert parser.confidence_score(["   ", "\t"]) == 0.0
    assert parser.confidence_score(["line"]) == 0.0

def test_windows_parser_xml_fallbacks():
    from unilog.parsers.windows import WindowsParser
    parser = WindowsParser()
    
    # 1. Namespace-less XML Level=1 (CRITICAL) and unnamed Data element
    xml_lvl1 = '<Event><System><Provider Name="MySource"/><EventID>1001</EventID><TimeCreated SystemTime="2026-07-10T12:00:00Z"/><Level>1</Level><Task>10</Task></System><EventData><Data Name="Param1">val1</Data><Data>unnamed_val</Data></EventData></Event>'
    res1 = parser.parse_line(xml_lvl1)
    assert res1.get("_parse_error") is not True
    assert res1["level"] == "CRITICAL"
    assert res1["source"] == "MySource"
    assert res1["event_id"] == 1001
    assert "Param1=val1; unnamed_val" in res1["message"]

    # 2. Namespace-less XML Level=2 (ERROR)
    xml_lvl2 = '<Event><System><Provider Name="MySource"/><EventID>1002</EventID><TimeCreated SystemTime="2026-07-10T12:00:00Z"/><Level>2</Level></System></Event>'
    res2 = parser.parse_line(xml_lvl2)
    assert res2["level"] == "ERROR"

    # 3. Namespace-less XML Level=3 (WARNING)
    xml_lvl3 = '<Event><System><Provider Name="MySource"/><EventID>1003</EventID><TimeCreated SystemTime="2026-07-10T12:00:00Z"/><Level>3</Level></System></Event>'
    res3 = parser.parse_line(xml_lvl3)
    assert res3["level"] == "WARNING"

    # 4. XML with System element missing
    xml_no_sys = '<Event><SystemOther></SystemOther></Event>'
    res_err = parser.parse_line(xml_no_sys)
    assert res_err.get("_parse_error") is True

def test_registry_load_entry_points_exceptions():
    from unittest.mock import patch, MagicMock
    from unilog.registry import load_entry_points, register_parser
    
    # Mock entry_points to raise an exception
    with patch("importlib.metadata.entry_points", side_effect=Exception("Failed to load group")):
        load_entry_points() # should handle exception and pass
        
    # Mock entry_points to return a broken entry point
    mock_ep = MagicMock()
    mock_ep.load.side_effect = Exception("Broken ep")
    
    with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
        load_entry_points() # should handle exception in ep.load() and pass

    # TypeError on invalid class
    import pytest
    with pytest.raises(TypeError, match="Parser class must inherit from BaseParser"):
        register_parser(object) # type: ignore

    # ValueError on missing name
    from unilog.parsers.base import BaseParser
    class MissingNameParser(BaseParser):
        name = ""
    with pytest.raises(ValueError, match="Parser class must define a valid non-base name attribute"):
        register_parser(MissingNameParser)

def test_registry_import_error_reset():
    from unittest.mock import patch
    import unilog.registry
    unilog.registry._loaded = False
    with patch("builtins.__import__", side_effect=ImportError("Mocked import error")):
        unilog.registry._ensure_loaded()
    assert unilog.registry._loaded is True

def test_utils_edge_cases():
    from unilog.utils import normalize_timestamp, read_file, sample_lines
    from unittest.mock import patch
    import io
    
    # normalize_timestamp falsy values
    assert normalize_timestamp("") is None
    assert normalize_timestamp(None) is None # type: ignore
    assert normalize_timestamp(" - ") is None
    
    # specific format fails parse
    assert normalize_timestamp("bad_ts", fmt="%Y-%m-%d") is None
    
    # complex fallback parse fails
    assert normalize_timestamp("10/Jul/2026:bad:time", fmt=None) is None

    # read_file with stdin mock
    mock_stdin = io.StringIO("stdin log line\n")
    with patch("sys.stdin", mock_stdin):
        lines = list(read_file("-"))
        assert len(lines) == 1
        assert lines[0] == "stdin log line\n"

    # sample_lines general exception handler trigger
    res_lines = sample_lines(12345) # type: ignore # passing integer causes exception in sample_lines
    assert res_lines == []
