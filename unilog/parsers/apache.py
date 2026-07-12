from unilog.parsers.nginx import NginxParser
from unilog.registry import register_parser

@register_parser
class ApacheParser(NginxParser):
    """Parser for Apache access logs. Reuses Nginx Combined pattern structure."""
    
    name = "apache"
    description = "Apache Combined/Common Access Log"
    priority = 75
    supported_extensions = [".log", ".txt", ".conf"]

    required_fields = ["source_ip", "timestamp", "method", "path", "status_code", "size"]
    optional_fields = ["remote_user", "protocol", "referer", "user_agent"]
