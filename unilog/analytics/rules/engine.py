"""Rule engine: orchestrates rule evaluation across a MetricsBundle."""

from typing import List

from unilog.analytics.rules.evaluator import RuleEvaluator
from unilog.analytics.rules.models import RuleContext, RuleSet
from unilog.analytics.schemas import Insight, MetricsBundle


class RuleEngine:
    """Iterate rules in a RuleSet and delegate each to the RuleEvaluator."""

    def __init__(self) -> None:
        self._evaluator = RuleEvaluator()

    def evaluate(
        self,
        bundle: MetricsBundle,
        ruleset: RuleSet,
        context: RuleContext,
    ) -> List[Insight]:
        """Evaluate all enabled rules and return triggered insights."""
        insights: List[Insight] = []
        for rule in ruleset.rules:
            insight = self._evaluator.evaluate(rule, bundle, context)
            if insight is not None:
                insights.append(insight)
        return insights
