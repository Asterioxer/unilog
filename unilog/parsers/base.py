import abc
import re
from typing import Dict, Any, List, Optional, Iterator
from unilog.utils import normalize_timestamp, safe_int

class BaseParser(abc.ABC):
    """Abstract base class that all log parsers must inherit from."""
    
    name: str = "base"
    description: str = "Base Log Parser"
    priority: int = 0
    supported_extensions: List[str] = []

    # Parser field metadata — subclasses should override these to declare
    # which fields they are expected to extract. Used by the confidence scorer
    # to compute extraction completeness without inspecting regex internals.
    required_fields: List[str] = []
    optional_fields: List[str] = []
    _confidence_breakdown: Dict[str, Any] = {}

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
        """Calculate confidence score (0.0 to 1.0) using extraction completeness.
        
        Score breakdown (stored in self._confidence_breakdown):
          - match_score:       30%  Lines matched by the parser
          - parse_quality:     25%  Lines parsed without error
          - extraction:        25%  Ratio of non-null declared fields extracted
          - timestamp_quality: 15%  Timestamps parsed successfully
          - numeric_valid:      5%  Numeric fields are properly typed
        """
        if not sample_lines:
            self._confidence_breakdown = {}
            return 0.0

        matches = 0
        parsed_records: List[Dict[str, Any]] = []

        non_empty_lines = [line.strip() for line in sample_lines if line.strip()]
        total_lines = len(non_empty_lines)

        if total_lines == 0:
            self._confidence_breakdown = {}
            return 0.0

        for line in non_empty_lines:
            if self.match(line):
                matches += 1
                try:
                    res = self.parse_line(line)
                    if res and not res.get("_parse_error"):
                        parsed_records.append(res)
                except Exception:
                    pass

        match_ratio = matches / total_lines

        # Early exit: if no lines matched, score is 0 — no false baselines
        if matches == 0 or not parsed_records:
            self._confidence_breakdown = {
                "match_score": 0.0,
                "parse_quality": 0.0,
                "extraction": 0.0,
                "timestamp_quality": 0.0,
                "numeric_valid": 0.0,
            }
            return 0.0

        parse_ratio = len(parsed_records) / total_lines

        # Extraction completeness: ratio of non-null declared fields per record
        declared_fields = self.required_fields + self.optional_fields
        if declared_fields:
            extraction_scores = []
            for rec in parsed_records:
                present = sum(
                    1 for f in declared_fields
                    if f in rec and rec[f] is not None
                )
                extraction_scores.append(present / len(declared_fields))
            extraction_ratio = sum(extraction_scores) / len(extraction_scores)
        else:
            # Fallback for parsers that haven't declared field metadata yet:
            # use the old required-fields heuristic
            req_count = 0
            for rec in parsed_records:
                has_req = any(
                    k in rec
                    for k in ["message", "path", "status_code", "status", "event_id", "level"]
                )
                if has_req:
                    req_count += 1
            extraction_ratio = req_count / len(parsed_records)

        # Timestamp quality
        ts_count = sum(1 for rec in parsed_records if rec.get("timestamp") is not None)
        ts_ratio = ts_count / len(parsed_records)

        # Numeric field validity
        num_valid_count = 0
        for rec in parsed_records:
            num_fields = [
                k for k in ["status_code", "size", "event_id", "status"]
                if k in rec
            ]
            if num_fields:
                if all(rec[k] is None or isinstance(rec[k], int) for k in num_fields):
                    num_valid_count += 1
            # If no numeric fields declared, don't count — avoids false inflation
        num_ratio = (num_valid_count / len(parsed_records)) if any(
            k in rec for rec in parsed_records
            for k in ["status_code", "size", "event_id", "status"]
        ) else 0.0

        # Weighted composite score
        match_score = match_ratio * 0.30
        parse_quality = parse_ratio * 0.25
        extraction_score = extraction_ratio * 0.25
        timestamp_score = ts_ratio * 0.15
        numeric_score = num_ratio * 0.05

        self._confidence_breakdown = {
            "match_score": round(match_score, 4),
            "parse_quality": round(parse_quality, 4),
            "extraction": round(extraction_score, 4),
            "timestamp_quality": round(timestamp_score, 4),
            "numeric_valid": round(numeric_score, 4),
        }

        score = match_score + parse_quality + extraction_score + timestamp_score + numeric_score
        return min(1.0, score)

    def parse(self, text: str) -> Iterator[Dict[str, Any]]:
        """Parse a full block/document of text, yielding parsed records."""
        for line in text.splitlines():
            line = line.strip()
            if line:
                yield self.parse_line(line)



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
