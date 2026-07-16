"""Severity-aware recommendation generation."""

from unilog.analytics.rules.models import Rule


# Severity escalation thresholds for common rule categories.
_SEVERITY_RECOMMENDATIONS: dict[str, dict[str, str]] = {
    "performance": {
        "low": "Monitor latency trends over the next analysis window.",
        "medium": "Review slow endpoints and consider query optimization.",
        "high": "Investigate slow endpoints immediately — latency is impacting users.",
        "critical": "Scale deployment immediately — critical latency detected.",
    },
    "reliability": {
        "low": "Monitor error rates for upward trends.",
        "medium": "Investigate recurring errors in application logs.",
        "high": "Elevated error rate detected — review recent deployments.",
        "critical": "Critical failure rate — initiate incident response.",
    },
    "traffic": {
        "low": "Traffic levels are slightly above normal.",
        "medium": "Traffic spike detected — verify auto-scaling is active.",
        "high": "Significant traffic surge — check load balancer health.",
        "critical": "Extreme traffic volume — possible DDoS or viral event.",
    },
    "security": {
        "low": "Log the event for future auditing.",
        "medium": "Review access logs for suspicious patterns.",
        "high": "Block the offending source and alert the security team.",
        "critical": "Active attack detected — engage incident response immediately.",
    },
}

_DEFAULT_RECOMMENDATION = "Review the triggered metric and take appropriate action."


class RecommendationProvider:
    """Generate context-sensitive recommendations based on rule category and severity."""

    def recommend(self, rule: Rule, value: float, severity: str) -> str:
        """Return a severity-aware recommendation string."""
        category_recs = _SEVERITY_RECOMMENDATIONS.get(rule.category)
        if category_recs:
            rec = category_recs.get(severity)
            if rec:
                return rec
        return _DEFAULT_RECOMMENDATION
