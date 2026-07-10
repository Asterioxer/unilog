import re
from typing import Dict, Any, List
from unilog.parsers.base import StructuredRegexParser

class CustomParser(StructuredRegexParser):
    """Custom parser for user-defined patterns."""
    
    name = "custom"
    description = "Custom User-Defined Regex Parser"
    priority = 10
    
    pattern_str: str = ""

    def __init__(self):
        super().__init__()
        if self.pattern_str:
            try:
                compiled = re.compile(self.pattern_str)
                if not compiled.groupindex:
                    raise ValueError("Custom pattern must contain at least one named group (?P<name>...)")
                self._pattern = compiled
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        else:
            self._pattern = None

    def match(self, line: str) -> bool:
        if not self._pattern:
            return False
        return super().match(line)

    def parse_line(self, line: str) -> Dict[str, Any]:
        if not self._pattern:
            return {"_parse_error": True, "raw": line}
        return super().parse_line(line)

    def confidence_score(self, sample_lines: List[str]) -> float:
        # Custom parser confidence score:
        # Since it is manually registered and user-defined, we check matches.
        if not self._pattern or not sample_lines:
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
        return ratio * 0.95
