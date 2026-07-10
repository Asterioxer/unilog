from typing import Dict, Any, List
from unilog.registry import list_formats, load_entry_points
from unilog.utils import sample_lines

def detect(path_or_stream: Any, threshold: float = 0.6) -> Dict[str, Any]:
    """
    Detect the log format of a path, stream, or line list.
    
    Returns a dictionary:
    {
        "format": "format_name" or "unknown",
        "confidence": 0.0 - 1.0,
        "parser": BaseParser instance or None,
        "rankings": [{"format": str, "confidence": float}, ...],
        "reason": str
    }
    """
    if isinstance(path_or_stream, str) and path_or_stream != "-":
        import os
        if not os.path.exists(path_or_stream):
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path_or_stream}'")

    sample = sample_lines(path_or_stream, n=50)
    if not sample:
        return {
            "format": "unknown",
            "confidence": 0.0,
            "parser": None,
            "rankings": [],
            "reason": "Input is empty or could not be read."
        }

    # Load registry plugins
    load_entry_points()

    formats = list_formats()
    rankings_list: List[Dict[str, Any]] = []

    for fmt_info in formats:
        parser_cls = fmt_info["class"]
        try:
            parser_inst = parser_cls()
            score = parser_inst.confidence_score(sample)
            
            # File extension heuristic (+0.05 score, max 1.0)
            if hasattr(path_or_stream, "name") or isinstance(path_or_stream, str):
                name_str = path_or_stream.name if hasattr(path_or_stream, "name") else str(path_or_stream)
                extensions = fmt_info.get("supported_extensions", [])
                if any(name_str.endswith(ext) for ext in extensions):
                    score = min(1.0, score + 0.05)

            rankings_list.append({
                "format": fmt_info["name"],
                "confidence": round(score, 4),
                "parser_class": parser_cls,
                "priority": fmt_info.get("priority", 0)
            })
        except Exception:
            pass

    # Sort rankings:
    # 1. Confidence score descending
    # 2. Priority descending (deterministic tie-breaker)
    # 3. Format name alphabetically ascending (fallback tie-breaker)
    rankings_list.sort(key=lambda r: (-r["confidence"], -r["priority"], r["format"]))

    # Map rankings to final API format
    api_rankings = [{"format": r["format"], "confidence": r["confidence"]} for r in rankings_list]

    if rankings_list and rankings_list[0]["confidence"] >= threshold:
        best = rankings_list[0]
        parser_inst = best["parser_class"]()
        return {
            "format": best["format"],
            "confidence": best["confidence"],
            "parser": parser_inst,
            "rankings": api_rankings,
            "reason": f"Detected format '{best['format']}' with confidence {best['confidence']} (threshold: {threshold})."
        }

    reason_str = "No registered parser exceeded the confidence threshold."
    if rankings_list:
        reason_str = f"Best match '{rankings_list[0]['format']}' scored {rankings_list[0]['confidence']}, which is below threshold {threshold}."
        
    return {
        "format": "unknown",
        "confidence": 0.0,
        "parser": None,
        "rankings": api_rankings,
        "reason": reason_str
    }
