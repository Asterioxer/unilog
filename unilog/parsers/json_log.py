import json
from typing import Dict, Any, List
from unilog.parsers.base import BaseParser
from unilog.registry import register_parser
from unilog.utils import normalize_timestamp

@register_parser
class JSONParser(BaseParser):
    """Parser for JSON Lines formatted logs."""
    
    name = "json"
    description = "JSON Lines Log Parser"
    priority = 90
    supported_extensions = [".json", ".jsonl"]

    def match(self, line: str) -> bool:
        line = line.strip()
        if not (line.startswith("{") and line.endswith("}")):
            return False
        try:
            json.loads(line)
            return True
        except ValueError:
            return False

    def parse_line(self, line: str) -> Dict[str, Any]:
        line = line.strip()
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                return {"_parse_error": True, "raw": line}
        except ValueError:
            return {"_parse_error": True, "raw": line}

        # Normalize field alias keys
        # ts/time/@timestamp -> timestamp
        # msg/log -> message
        normalized = {}
        for k, v in data.items():
            k_lower = k.lower()
            if k_lower in ["ts", "time", "@timestamp"]:
                normalized["timestamp"] = v
            elif k_lower in ["msg", "log"]:
                normalized["message"] = v
            else:
                normalized[k] = v

        # If we don't have timestamp or message yet, make sure they are set if using standard keys
        if "timestamp" not in normalized and "time" in normalized:
            normalized["timestamp"] = normalized.pop("time")
        if "message" not in normalized and "msg" in normalized:
            normalized["message"] = normalized.pop("msg")
            
        # Parse timestamp if string and normalized
        if "timestamp" in normalized and isinstance(normalized["timestamp"], str):
            normalized["timestamp"] = normalize_timestamp(normalized["timestamp"])

        # Automatic level inference
        # If 'level' or 'lvl' or 'severity' is present, use it.
        # Otherwise, search all values for info/warn/error/debug.
        level = None
        for k in ["level", "lvl", "severity"]:
            if k in normalized:
                level = str(normalized[k]).upper()
                break
        
        if not level:
            # Search string values for log level terms
            for k, v in normalized.items():
                if isinstance(v, str) and v.upper() in ["INFO", "WARNING", "WARN", "ERROR", "DEBUG", "FATAL", "CRITICAL"]:
                    level = v.upper()
                    break
        
        if level:
            # Map WARN -> WARNING
            if level == "WARN":
                level = "WARNING"
            normalized["level"] = level
        else:
            normalized["level"] = None

        normalized["raw"] = line
        return normalized

    def confidence_score(self, sample_lines: List[str]) -> float:
        if not sample_lines:
            return 0.0
        
        valid_json_count = 0
        total_lines = 0
        
        for line in sample_lines:
            line_str = line.strip()
            if not line_str:
                continue
            total_lines += 1
            if self.match(line_str):
                valid_json_count += 1
                
        if total_lines == 0:
            return 0.0
            
        # Ratio of valid JSON lines
        ratio = valid_json_count / total_lines
        
        # If all lines are valid JSON, confidence is high
        return ratio * 0.95
