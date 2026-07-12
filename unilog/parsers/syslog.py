import re
from typing import Dict, Any, List
from unilog.parsers.base import StructuredRegexParser
from unilog.registry import register_parser
from unilog.utils import normalize_timestamp, safe_int

@register_parser
class SyslogParser(StructuredRegexParser):
    """Parser for Syslog RFC 3164 and RFC 5424 formats."""
    
    name = "syslog"
    description = "Syslog (RFC 3164 / RFC 5424)"
    priority = 60
    supported_extensions = [".log", ".syslog"]

    required_fields = ["timestamp", "hostname", "process", "message", "level"]
    optional_fields = ["priority", "pid", "syslog_version", "msgid", "structured_data"]

    # RFC 3164 pattern: <PRI>MMM DD HH:MM:SS hostname process[pid]: message
    _rfc3164_pattern = re.compile(
        r'^<(?P<priority>\d+)>(?P<timestamp_raw>[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+'
        r'(?P<hostname>\S+)\s+(?P<process>[^:\[\s]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)$'
    )

    # RFC 5424 pattern: <PRI>1 TIMESTAMP HOSTNAME APP PROCID MSGID [STRUCTURED_DATA] MSG
    _rfc5424_pattern = re.compile(
        r'^<(?P<priority>\d+)>1\s+(?P<timestamp_raw>\S+)\s+(?P<hostname>\S+)\s+'
        r'(?P<process>\S+)\s+(?P<pid>\d+|-)\s+(?P<msgid>\S+)\s+'
        r'(?P<structured_data>-|(?:\[[^\]]+\])+)(?:\s+(?P<message>.*))?$'
    )

    # Syslog severity mapping
    SEVERITY_LEVELS = {
        0: "CRITICAL",  # Emergency
        1: "CRITICAL",  # Alert
        2: "CRITICAL",  # Critical
        3: "ERROR",     # Error
        4: "WARNING",   # Warning
        5: "NOTICE",    # Notice
        6: "INFO",      # Informational
        7: "DEBUG"      # Debug-level
    }

    def match(self, line: str) -> bool:
        line = line.strip()
        return bool(self._rfc3164_pattern.match(line) or self._rfc5424_pattern.match(line))

    def parse_line(self, line: str) -> Dict[str, Any]:
        line = line.strip()
        
        # Try RFC 5424 first (more structured)
        m = self._rfc5424_pattern.match(line)
        version = "5424"
        if not m:
            m = self._rfc3164_pattern.match(line)
            version = "3164"

        if not m:
            return {"_parse_error": True, "raw": line}

        res = m.groupdict()
        res["syslog_version"] = version
        res["raw"] = line

        # Normalize priority and extract severity level
        pri = safe_int(res.get("priority"))
        res["priority"] = pri
        if pri is not None:
            severity = pri % 8
            res["level"] = self.SEVERITY_LEVELS.get(severity, "INFO")
        else:
            res["level"] = "INFO"

        # Normalize pid
        if "pid" in res:
            if res["pid"] == "-":
                res["pid"] = None
            else:
                res["pid"] = safe_int(res["pid"])

        # Clean structured data or msgid if hyphen
        for field in ["msgid", "structured_data"]:
            if field in res and res[field] == "-":
                res[field] = None

        # Normalize timestamp
        if "timestamp_raw" in res:
            raw_ts = res["timestamp_raw"]
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
        # Syslog is relatively specific but can sometimes match other formats if we're not careful.
        # We give it a high confidence if almost all lines match, but scale it slightly.
        return ratio * 0.90
