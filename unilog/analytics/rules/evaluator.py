"""Single-rule evaluator: resolves selector, applies operator, computes confidence."""

import uuid
from typing import Any, Optional

from pydantic import BaseModel

from unilog.analytics.rules.models import Rule, RuleContext
from unilog.analytics.rules.operators import get_operator
from unilog.analytics.rules.recommendations import RecommendationProvider
from unilog.analytics.schemas import Insight, MetricsBundle


class RuleEvaluator:
    """Evaluate a single rule against a MetricsBundle."""

    def __init__(self) -> None:
        self._recommender = RecommendationProvider()

    def evaluate(
        self,
        rule: Rule,
        bundle: MetricsBundle,
        context: RuleContext,
    ) -> Optional[Insight]:
        """Resolve the metric selector, apply the operator, and return an Insight if triggered."""
        if not rule.enabled:
            return None

        value = self._resolve_selector(bundle, rule.metric_selector)
        if value is None:
            return None

        # Coerce booleans to float for operator comparison (e.g. is_bursting=True → 1.0)
        if isinstance(value, bool):
            value = 1.0 if value else 0.0

        compare = get_operator(rule.operator)
        if not compare(value, rule.threshold):
            return None

        # Compute confidence: sample_factor × rule_weight
        sample_factor = min(1.0, context.analyzed_records / 100.0) if context.analyzed_records > 0 else 0.0
        confidence = round(sample_factor * rule.weight, 4)

        # Generate description from template
        description = rule.description_template.format(
            value=round(value, 2),
            threshold=round(rule.threshold, 2),
        )

        # Severity-aware recommendation
        recommendation = self._recommender.recommend(rule, value, rule.severity)

        return Insight(
            id=f"{rule.id}-{uuid.uuid4().hex[:8]}",
            category=rule.category,
            severity=rule.severity,
            confidence=confidence,
            timestamp=context.timestamp,
            description=description,
            recommendation=recommendation,
            evidence={
                "metric_selector": rule.metric_selector,
                "observed_value": round(value, 4),
                "threshold": rule.threshold,
                "operator": rule.operator,
            },
            metadata={
                "rule_id": rule.id,
                "rule_name": rule.name,
                "rule_weight": rule.weight,
                "sample_factor": round(sample_factor, 4),
            },
        )

    @staticmethod
    def _resolve_selector(bundle: MetricsBundle, selector: str) -> Optional[float]:
        """Walk a dotted selector path into the MetricsBundle, returning the leaf value."""
        parts = selector.split(".")
        current: Any = bundle

        for part in parts:
            if current is None:
                return None
            if isinstance(current, BaseModel):
                current = getattr(current, part, None)
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        if current is None:
            return None
        if isinstance(current, bool):
            return 1.0 if current else 0.0
        try:
            return float(current)
        except (ValueError, TypeError):
            return None
