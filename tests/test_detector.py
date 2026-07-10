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
