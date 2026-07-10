import abc
import re
from typing import Dict, Any, List, Optional
from unilog.utils import normalize_timestamp, safe_int

class BaseParser(abc.ABC):
    """Abstract base class that all log parsers must inherit from."""
    
    name: str = "base"
    description: str = "Base Log Parser"
    priority: int = 0
    supported_extensions: List[str] = []

    @abc.abstractmethod
    def match(self, line: str) -> bool:
        """Return True if the line matches the expected format format."""
        pass

    @abc.abstractmethod
    def parse_line(self, line: str) -> Dict[str, Any]:
        """Parse a single line of log. Returns a dictionary of parsed fields.
        If parsing fails, returns a dict with '_parse_error': True, 'raw': line.
        """
        pass

    def confidence_score(self, sample_lines: List[str]) -> float:
        """Calculate confidence score (0.0 to 1.0) that these sample lines match this parser."""
        if not sample_lines:
            return 0.0
        
        matches = 0
        timestamp_parsed = 0
        required_fields_present = 0
        numeric_valid = 0
        
        parsed_records = []
        for line in sample_lines:
            line = line.strip()
            if not line:
                continue
            if self.match(line):
                matches += 1
                try:
                    res = self.parse_line(line)
                    if res and not res.get("_parse_error"):
                        parsed_records.append(res)
                except Exception:
                    pass
                    
        total_lines = len([line for line in sample_lines if line.strip()])
        if total_lines == 0 or not parsed_records:
            return 0.0

        match_ratio = matches / total_lines
        
        # Scoring Weights:
        # - 40% Regex/Match ratio
        # - 25% Timestamp parsed correctly
        # - 20% Required fields present
        # - 10% Numeric fields valid
        # - 5% Bonus heuristics
        
        # Calculate individual score components
        for rec in parsed_records:
            # 1. Timestamp validation
            if rec.get("timestamp") is not None:
                timestamp_parsed += 1
                
            # 2. Required fields present
            # We check if at least message or some key fields are present
            has_req = any(k in rec for k in ["message", "path", "status_code", "status", "event_id", "level"])
            if has_req:
                required_fields_present += 1
                
            # 3. Numeric fields check
            # e.g., status_code, size, event_id
            num_fields = [k for k in ["status_code", "size", "event_id", "status"] if k in rec]
            if num_fields:
                if all(rec[k] is None or isinstance(rec[k], int) for k in num_fields):
                    numeric_valid += 1
            else:
                numeric_valid += 1 # Default to valid if no numeric fields defined

        ts_ratio = timestamp_parsed / total_lines
        req_ratio = required_fields_present / total_lines
        num_ratio = numeric_valid / total_lines
        
        score = (
            (match_ratio * 0.40) +
            (ts_ratio * 0.25) +
            (req_ratio * 0.20) +
            (num_ratio * 0.10)
        )
        
        # Add 5% bonus for extensions
        # (usually checked in detector but included here as heuristic)
        return min(1.0, score)


class RegexParser(BaseParser):
    """Base class for regex-based parsers."""
    
    _pattern: Optional[re.Pattern] = None

    def match(self, line: str) -> bool:
        if self._pattern is None:
            return False
        return bool(self._pattern.search(line))

    def parse_line(self, line: str) -> Dict[str, Any]:
        if self._pattern is None:
            return {"_parse_error": True, "raw": line}
        
        m = self._pattern.search(line)
        if not m:
            return {"_parse_error": True, "raw": line}
        
        res = m.groupdict()
        res["raw"] = line
        return res


class StructuredRegexParser(RegexParser):
    """RegexParser with timestamp normalization and field typing."""
    
    timestamp_field: Optional[str] = None
    timestamp_format: Optional[str] = None
    
    def parse_line(self, line: str) -> Dict[str, Any]:
        res = super().parse_line(line)
        if res.get("_parse_error"):
            return res
        
        # Normalize timestamp if field exists
        if self.timestamp_field and self.timestamp_field in res:
            raw_ts = res[self.timestamp_field]
            if raw_ts:
                res["timestamp"] = normalize_timestamp(raw_ts, self.timestamp_format)
            else:
                res["timestamp"] = None
        
        # Convert standard numeric fields if present
        for field in ["status_code", "status", "size", "bytes_sent", "body_bytes_sent", "event_id"]:
            if field in res and res[field] is not None:
                res[field] = safe_int(res[field])
                
        return res
