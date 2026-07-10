# Custom Plugin Development

`unilog` features an extensible registry allowing developers to add proprietary log formats seamlessly without hacking core code.

## Creating a Parser Plugin

A custom parser must:
1. Inherit from `BaseParser` (or `RegexParser` / `StructuredRegexParser`).
2. Be decorated with `@register_parser`.
3. Expose configuration metadata properties:
   - `name`: Unique parser string identifier.
   - `description`: Human-readable label.
   - `priority`: Scoring weight (higher means evaluated first; standard range `1-100`).
   - `supported_extensions`: File suffixes matched during file type detection.
4. Implement `parse_line(self, line: str) -> Optional[Dict[str, Any]]`.

---

## Code Example: Standard Custom Parser

Save the following file in a custom directory (e.g. `my_parsers.py`):

```python
from typing import Optional, Dict, Any
from unilog.parsers.base import BaseParser
from unilog.registry import register_parser

@register_parser
class CustomAppParser(BaseParser):
    name = "custom_app"
    description = "Internal Custom Application Log Format"
    priority = 85
    supported_extensions = [".log", ".txt"]

    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        # Example line format: "2026-07-10 | ERROR | user_auth | login failed"
        if not line.strip():
            return None
            
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            return {"_parse_error": True, "raw": line}
            
        return {
            "timestamp": parts[0],
            "level": parts[1],
            "module": parts[2],
            "message": parts[3]
        }
```

Importing this module anywhere before running `unilog` auto-registers it:

```python
import my_parsers
import unilog

# 'custom_app' is now active in auto-detection and parsing!
df = unilog.parse("app_internal.log")
```

---

## Code Example: Custom Regex Parser

You can inherit from `StructuredRegexParser` to define regex-based parsers with automated normalization:

```python
from unilog.parsers.base import StructuredRegexParser
from unilog.registry import register_parser

@register_parser
class CustomWebParser(StructuredRegexParser):
    name = "custom_web"
    description = "Custom Web access log"
    priority = 75
    supported_extensions = [".log"]
    
    # regex captures normalized fields like client_ip, timestamp, request_path, status_code
    pattern = r"^(?P<client_ip>[\w\.]+) - \[(?P<timestamp>[^\]]+)\] \"(?P<request_path>[^\"]+)\" (?P<status_code>\d+)$"
    timestamp_field = "timestamp"
    timestamp_format = "%d/%b/%Y:%H:%M:%S %z"
```
