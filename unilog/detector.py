from typing import Dict, Any, List
from unilog.registry import list_formats, load_entry_points
from unilog.utils import sample_lines

# Configurable threshold for ambiguity detection.
# If the top two parsers are within this margin, the result is flagged as ambiguous.
AMBIGUITY_EPSILON = 0.02

def detect(path_or_stream: Any, threshold: float = 0.6) -> Dict[str, Any]:
    """
    Detect the log format of a path, stream, or line list.
    
    Returns a dictionary:
    {
        "format": "format_name" or "unknown",
        "confidence": 0.0 - 1.0,
        "parser": BaseParser instance or None,
        "rankings": [{"format": str, "confidence": float}, ...],
        "ambiguous": bool,
        "alternatives": [{"format": str, "confidence": float}, ...],
        "confidence_breakdown": dict or None,
        "reason": str
    }
    """
    if isinstance(path_or_stream, str) and path_or_stream != "-":
        import os
        from unilog.utils import validate_path_safety
        clean_path = validate_path_safety(path_or_stream)
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{path_or_stream}'")
        path_or_stream = clean_path

    sample = sample_lines(path_or_stream, n=50)
    if not sample:
        return {
            "format": "unknown",
            "confidence": 0.0,
            "parser": None,
            "rankings": [],
            "ambiguous": False,
            "alternatives": [],
            "confidence_breakdown": None,
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
            # Only apply when the parser already has a non-zero confidence
            if score > 0.0 and (hasattr(path_or_stream, "name") or isinstance(path_or_stream, str)):
                name_str = path_or_stream.name if hasattr(path_or_stream, "name") else str(path_or_stream)
                extensions = fmt_info.get("supported_extensions", [])
                if any(name_str.endswith(ext) for ext in extensions):
                    score = min(1.0, score + 0.05)

            # Retrieve confidence breakdown if available
            breakdown = getattr(parser_inst, "_confidence_breakdown", None)

            rankings_list.append({
                "format": fmt_info["name"],
                "confidence": score,
                "parser_class": parser_cls,
                "priority": fmt_info.get("priority", 0),
                "confidence_breakdown": breakdown,
            })
        except Exception:
            pass

    # Sort rankings:
    # 1. Confidence score descending
    # 2. Priority descending (deterministic tie-breaker)
    # 3. Format name alphabetically ascending (fallback tie-breaker)
    rankings_list.sort(key=lambda r: (-r["confidence"], -r["priority"], r["format"]))

    # Filter out zero-score parsers from the public rankings
    non_zero_rankings = [r for r in rankings_list if r["confidence"] > 0.0]
    api_rankings = [{"format": r["format"], "confidence": r["confidence"]} for r in non_zero_rankings]

    # Ambiguity detection: check if top two parsers are within epsilon
    ambiguous = False
    alternatives: List[Dict[str, Any]] = []

    if len(non_zero_rankings) >= 2:
        top_score = non_zero_rankings[0]["confidence"]
        for alt in non_zero_rankings[1:]:
            if top_score - alt["confidence"] <= AMBIGUITY_EPSILON:
                ambiguous = True
                alternatives.append({
                    "format": alt["format"],
                    "confidence": alt["confidence"],
                })

    if non_zero_rankings and non_zero_rankings[0]["confidence"] >= threshold:
        best = non_zero_rankings[0]
        parser_inst = best["parser_class"]()
        
        reason = f"Detected format '{best['format']}' with confidence {best['confidence']} (threshold: {threshold})."
        if ambiguous:
            alt_names = ", ".join(f"'{a['format']}' ({a['confidence']})" for a in alternatives)
            reason += f" Ambiguous: {alt_names} within margin."

        return {
            "format": best["format"],
            "confidence": best["confidence"],
            "parser": parser_inst,
            "rankings": api_rankings,
            "ambiguous": ambiguous,
            "alternatives": alternatives,
            "confidence_breakdown": best.get("confidence_breakdown"),
            "reason": reason,
        }

    reason_str = "No registered parser exceeded the confidence threshold."
    if non_zero_rankings:
        reason_str = f"Best match '{non_zero_rankings[0]['format']}' scored {non_zero_rankings[0]['confidence']}, which is below threshold {threshold}."
        
    return {
        "format": "unknown",
        "confidence": 0.0,
        "parser": None,
        "rankings": api_rankings,
        "ambiguous": False,
        "alternatives": [],
        "confidence_breakdown": None,
        "reason": reason_str,
    }
