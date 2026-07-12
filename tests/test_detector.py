from unilog.parsers.base import BaseParser, RegexParser, StructuredRegexParser
from unilog.registry import register_parser, get_parser, list_formats

def test_registry():
    # Define a mock parser
    @register_parser
    class MockParser(BaseParser):
        name = "mock_format"
        description = "Mock format for testing"
        priority = 99
        supported_extensions = [".log"]

        def match(self, line: str) -> bool:
            return line.startswith("MOCK:")

        def parse_line(self, line: str) -> dict:
            if not self.match(line):
                return {"_parse_error": True, "raw": line}
            return {"level": "info", "message": line[5:], "timestamp": None}

    assert get_parser("mock_format") is MockParser
    
    fmts = list_formats()
    names = [f["name"] for f in fmts]
    assert "mock_format" in names

    # Clean up mock_format from registry for subsequent tests
    from unilog.registry import _registry
    if "mock_format" in _registry:
        del _registry["mock_format"]

def test_regex_parser():
    import re
    class SimpleRegexParser(RegexParser):
        name = "simple_regex"
        description = "Simple Regex"
        priority = 10
        _pattern = re.compile(r"^\[(?P<level>\w+)\] (?P<message>.+)$")

    parser = SimpleRegexParser()
    assert parser.match("[INFO] hello world")
    assert not parser.match("hello world")

    res = parser.parse_line("[INFO] hello world")
    assert res["level"] == "INFO"
    assert res["message"] == "hello world"
    assert res["raw"] == "[INFO] hello world"

def test_structured_regex_parser():
    import re
    class StructuredMockParser(StructuredRegexParser):
        name = "structured_mock"
        description = "Structured Mock"
        priority = 20
        _pattern = re.compile(r"^(?P<timestamp>\d{4}-\d{2}-\d{2}) (?P<status_code>\d+) (?P<message>.+)$")
        timestamp_field = "timestamp"
        timestamp_format = "%Y-%m-%d"

    parser = StructuredMockParser()
    res = parser.parse_line("2026-07-10 200 OK")
    assert res["timestamp"].year == 2026
    assert res["status_code"] == 200
    assert res["message"] == "OK"
    assert res["raw"] == "2026-07-10 200 OK"


# ==============================================================================
# Detection Accuracy Tests
# ==============================================================================

def test_nginx_combined_detection():
    """Nginx Combined format (with referer + UA) should be detected with high confidence."""
    from unilog.detector import detect

    result = detect("tests/sample_logs/minimal/nginx.log")
    assert result["format"] == "nginx"
    assert result["confidence"] >= 0.9
    assert result["parser"] is not None


def test_apache_nginx_ambiguity_flagged():
    """When Apache and Nginx parsers tie, ambiguity should be flagged."""
    from unilog.detector import detect

    # Both minimal log files should trigger ambiguity since both parsers
    # share the same regex and produce identical extraction completeness
    result = detect("tests/sample_logs/minimal/apache.log")
    assert result["ambiguous"] is True
    assert len(result["alternatives"]) >= 1
    alt_formats = [a["format"] for a in result["alternatives"]]
    assert "apache" in alt_formats or "nginx" in alt_formats


def test_zero_score_parsers_omitted_from_rankings():
    """Parsers with zero confidence should not appear in rankings."""
    from unilog.detector import detect

    result = detect("tests/sample_logs/minimal/nginx.log")
    for ranking in result["rankings"]:
        assert ranking["confidence"] > 0.0, (
            f"Parser '{ranking['format']}' has zero confidence but appears in rankings"
        )


def test_garbage_input_no_rankings():
    """Garbage input should produce no rankings (all parsers score 0)."""
    from unilog.detector import detect
    import tempfile
    import os

    # Create a temp garbage file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write("this is just random text\nno structure here\nnothing to parse\n")
        f.flush()
        path = f.name

    try:
        result = detect(path)
        assert result["format"] == "unknown"
        assert result["confidence"] == 0.0
        assert result["rankings"] == []
        assert result["ambiguous"] is False
    finally:
        os.unlink(path)


def test_confidence_breakdown_present():
    """Detector should include confidence_breakdown for the winning parser."""
    from unilog.detector import detect

    result = detect("tests/sample_logs/minimal/nginx.log")
    breakdown = result.get("confidence_breakdown")
    assert breakdown is not None
    expected_keys = {"match_score", "parse_quality", "extraction", "timestamp_quality", "numeric_valid"}
    assert set(breakdown.keys()) == expected_keys
    # All components should be non-negative
    for key, value in breakdown.items():
        assert value >= 0.0, f"Breakdown component '{key}' is negative: {value}"


def test_field_metadata_declared():
    """All built-in parsers should declare required_fields metadata."""
    from unilog.registry import list_formats

    for fmt in list_formats():
        parser_cls = fmt["class"]
        name = fmt["name"]
        # Skip custom parser which is user-provided
        if name == "custom":
            continue
        assert hasattr(parser_cls, "required_fields"), f"{name} missing required_fields"
        assert len(parser_cls.required_fields) > 0, f"{name} has empty required_fields"


def test_detection_determinism():
    """Running detection on the same file twice should produce identical results."""
    from unilog.detector import detect

    r1 = detect("tests/sample_logs/minimal/nginx.log")
    r2 = detect("tests/sample_logs/minimal/nginx.log")

    assert r1["format"] == r2["format"]
    assert r1["confidence"] == r2["confidence"]
    assert r1["ambiguous"] == r2["ambiguous"]
    assert r1["rankings"] == r2["rankings"]


def test_extraction_completeness_scoring():
    """Parser with declared fields should get extraction completeness score > 0
    when fields are present in parsed output."""
    from unilog.parsers.nginx import NginxParser
    from unilog.utils import sample_lines

    parser = NginxParser()
    sample = sample_lines("tests/sample_logs/minimal/nginx.log", n=50)
    score = parser.confidence_score(sample)

    assert score > 0.0
    assert hasattr(parser, "_confidence_breakdown")
    assert parser._confidence_breakdown["extraction"] > 0.0


def test_no_match_returns_zero():
    """Parser should return exactly 0.0 when no lines match."""
    from unilog.parsers.nginx import NginxParser

    parser = NginxParser()
    garbage = ["random text", "no structure", "nothing here"]
    score = parser.confidence_score(garbage)
    assert score == 0.0
    assert parser._confidence_breakdown["match_score"] == 0.0

