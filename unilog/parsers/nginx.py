import re
from typing import Dict, Any
from unilog.parsers.base import StructuredRegexParser
from unilog.registry import register_parser

@register_parser
class NginxParser(StructuredRegexParser):
    """Parser for Nginx access logs (combined and common formats)."""
    
    name = "nginx"
    description = "Nginx Combined/Common Access Log"
    priority = 80
    supported_extensions = [".log", ".txt"]

    # Pattern supporting both Common and Combined formats, and handling IPv4/IPv6 IPs
    _pattern = re.compile(
        r'^(?P<source_ip>\S+) - (?P<remote_user>\S+) \[(?P<timestamp_raw>[^\]]+)\] '
        r'"(?:(?P<method>[A-Z]+)\s+(?P<path>[^"\s]+)(?:\s+(?P<protocol>HTTP/[0-9.]+))?|(?P<request>[^"]*))" '
        r'(?P<status_code>\d+) (?P<size>\d+|-)'
        r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<user_agent>[^"]*)")?\s*$'
    )

    timestamp_field = "timestamp_raw"
    # Nginx timestamp: 10/Jul/2026:20:53:59 +0530
    # Note: StructuredRegexParser/normalize_timestamp will handle this
    timestamp_format = None

    def parse_line(self, line: str) -> Dict[str, Any]:
        res = super().parse_line(line)
        if res.get("_parse_error"):
            return res
        
        # Clean up optional fields or '-' values
        if "remote_user" in res and res["remote_user"] == "-":
            res["remote_user"] = None
        if "referer" in res and res["referer"] == "-":
            res["referer"] = None
        if "user_agent" in res and res["user_agent"] == "-":
            res["user_agent"] = None
            
        # Remove raw timestamp field to clean up output
        if "timestamp_raw" in res:
            del res["timestamp_raw"]
            
        return res
