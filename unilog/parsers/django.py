import re
from typing import Dict, Any, List
from unilog.parsers.base import StructuredRegexParser
from unilog.registry import register_parser
from unilog.utils import normalize_timestamp

@register_parser
class DjangoParser(StructuredRegexParser):
    """Parser for Django request logs and standard Python logging format."""
    
    name = "django"
    description = "Django / Python Logging Parser"
    priority = 65
    supported_extensions = [".log", ".txt"]

    # Pattern for [2026-07-10 12:00:00] INFO django.request: message
    _django_pattern = re.compile(
        r'^\[(?P<timestamp_raw>[^\]]+)\]\s+(?P<level>\w+)\s+(?P<logger>[\w\.]+):\s+(?P<message>.*)$'
    )

    # Pattern for 2026-07-10 12:00:00,123 - app.views - WARNING - message
    _python_pattern = re.compile(
        r'^(?P<timestamp_raw>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+-\s+'
        r'(?P<logger>[\w\.]+)\s+-\s+(?P<level>\w+)\s+-\s+(?P<message>.*)$'
    )

    def match(self, line: str) -> bool:
        line = line.strip()
        return bool(self._django_pattern.match(line) or self._python_pattern.match(line))

    def parse_line(self, line: str) -> Dict[str, Any]:
        line = line.strip()
        m = self._django_pattern.match(line)
        if not m:
            m = self._python_pattern.match(line)

        if not m:
            return {"_parse_error": True, "raw": line}

        res = m.groupdict()
        res["raw"] = line

        # Normalize log level
        if "level" in res:
            res["level"] = res["level"].upper()
            if res["level"] == "WARN":
                res["level"] = "WARNING"

        # Normalize timestamp
        if "timestamp_raw" in res:
            # Python logging sometimes uses ',' for millisec, e.g. "2026-07-10 12:00:00,123"
            # Dateutil can handle this, but let's replace comma with dot just in case
            raw_ts = res["timestamp_raw"].replace(",", ".")
            res["timestamp"] = normalize_timestamp(raw_ts)
            del res["timestamp_raw"]

        return res

    def confidence_score(self, sample_lines: List[str]) -> float:
        if not sample_lines:
            return 0.0
        
        matches = 0
        total_lines = 0
        for line in sample_lines:
            line_str = line.strip()
            if not line_str:
                continue
            total_lines += 1
            if self.match(line_str):
                matches += 1

        if total_lines == 0:
            return 0.0

        ratio = matches / total_lines
        return ratio * 0.85
