from typing import Dict, Any, List, Optional, Tuple
from unilog.registry import list_formats
from unilog.utils import sample_lines
from unilog.parsers.base import BaseParser

def detect(path_or_stream: Any, threshold: float = 0.6) -> Dict[str, Any]:
    """
    Read first 50 lines of log, compute confidence scores for all registered parsers,
    and return the format with the highest score above threshold.
    """
    sample = sample_lines(path_or_stream, n=50)
    if not sample:
        return {"format": "unknown", "confidence": 0.0, "parser_instance": None}

    best_format: Optional[str] = None
    best_score: float = 0.0
    best_parser_cls: Optional[type] = None

    # Load entry points in case plugins have registered new parsers
    from unilog.registry import load_entry_points
    load_entry_points()

    # Query all registered formats
    formats = list_formats()
    for fmt_info in formats:
        parser_cls = fmt_info["class"]
        try:
            parser_inst = parser_cls()
            score = parser_inst.confidence_score(sample)
            
            # Check if file extension matches as a bonus heuristic (adds 0.05 up to 1.0)
            if hasattr(path_or_stream, "name") or isinstance(path_or_stream, str):
                name_str = path_or_stream.name if hasattr(path_or_stream, "name") else str(path_or_stream)
                extensions = fmt_info.get("supported_extensions", [])
                if any(name_str.endswith(ext) for ext in extensions):
                    score = min(1.0, score + 0.05)

            if score > best_score:
                best_score = score
                best_format = fmt_info["name"]
                best_parser_cls = parser_cls
        except Exception:
            pass

    if best_format and best_score >= threshold:
        return {
            "format": best_format,
            "confidence": round(best_score, 4),
            "parser_instance": best_parser_cls() if best_parser_cls else None
        }

    return {"format": "unknown", "confidence": 0.0, "parser_instance": None}
