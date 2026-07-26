# Plugin & Extension Guide

`unilog` is architected for maximum extensibility. Developers can write and register custom **Log Parsers**, **Analytics Observers**, and **Heuristic Rules** without modifying core codebase files.

---

## 1. Writing a Custom Log Parser

A custom parser:
1. Inherits from `BaseParser`, `RegexParser`, or `StructuredRegexParser`.
2. Uses the `@register_parser` class decorator.
3. Implements `parse_line(self, line: str) -> Optional[Dict[str, Any]]`.

### Example: Custom App Parser

```python
from typing import Optional, Dict, Any
from unilog.parsers.base import BaseParser
from unilog.registry import register_parser

@register_parser
class MicroserviceParser(BaseParser):
    name = "microservice_json"
    description = "Internal Microservice Structured Format"
    priority = 90
    supported_extensions = [".log", ".json"]

    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        if not line.strip():
            return None
            
        parts = [p.strip() for p in line.split(" :: ")]
        if len(parts) < 4:
            return {"_parse_error": True, "raw": line}
            
        return {
            "timestamp": parts[0],
            "level": parts[1],
            "service": parts[2],
            "message": parts[3]
        }
```

Importing this module dynamically registers `microservice_json` into auto-detection:

```python
import my_custom_parser
from unilog import parse_log_file

records, metadata = parse_log_file("service.log")
```

---

## 2. Writing a Custom Regex Parser

For pattern-based logs, inherit from `StructuredRegexParser`:

```python
from unilog.parsers.base import StructuredRegexParser
from unilog.registry import register_parser

@register_parser
class CustomProxyParser(StructuredRegexParser):
    name = "custom_proxy"
    description = "Internal Enterprise Proxy Log"
    priority = 80
    supported_extensions = [".log"]
    
    # Named regex groups automatically map to canonical field names
    pattern = r"^(?P<client_ip>[\w\.]+) \[(?P<timestamp>[^\]]+)\] \"(?P<method>\A-Z]+) (?P<request_path>[^\"]+)\" (?P<status_code>\d+) (?P<response_time>\d+)$"
    timestamp_field = "timestamp"
    timestamp_format = "%d/%b/%Y:%H:%M:%S %z"
```

---

## 3. Writing Custom Heuristic Rules

`unilog` allows registering custom rules to evaluate stream anomaly conditions dynamically:

```python
from unilog.analytics.rules import Rule, RuleCategory, RuleSeverity

# Define custom rule instance
high_5xx_spike_rule = Rule(
    id="RULE_CUSTOM_01",
    name="High 5xx Failure Rate",
    category=RuleCategory.RELIABILITY,
    severity=RuleSeverity.CRITICAL,
    description="Fires when HTTP 5xx error percentage exceeds 15% of total volume.",
    evaluator=lambda metrics: (metrics.get("status_codes", {}).get("5xx", 0) / max(metrics.get("total_lines", 1), 1)) > 0.15
)
```
