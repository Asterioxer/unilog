"""User journey path mapping analyzer."""

from typing import Any, Dict, List, Mapping, Sequence
from pydantic import BaseModel

from unilog.analytics.base import AnalyzerContext, BaseAnalyzer
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import JourneyMetrics, Session


def map_path_to_stage(path: str) -> str:
    """Heuristic stage mapping for standard e-commerce or website logs."""
    p_lower = path.lower().split("?")[0].rstrip("/")
    if not p_lower or p_lower in ["", "/home", "/index.html", "/index.htm", "/index"]:
        return "Landing"
    if p_lower.startswith(("/products", "/catalog", "/category", "/search")):
        return "Products"
    if p_lower.startswith(("/product", "/item", "/details")):
        return "Product"
    if p_lower == "/cart" or p_lower.endswith(("/cart", "/shopping-cart")):
        return "Cart"
    if p_lower.startswith(("/checkout", "/pay", "/billing", "/purchase")):
        return "Checkout"
    return "Other"


@register_analyzer("journey", version="1.0", dependencies=["session"], produces=JourneyMetrics)
class JourneyAnalyzer(BaseAnalyzer):
    """Enriches sessions with web journey stages and computes aggregate conversion funnels."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> JourneyMetrics:
        # Retrieve computed sessions from shared parser_metadata cache
        sessions: List[Session] = context.parser_metadata.get("reconstructed_sessions", [])

        stage_counts: Dict[str, int] = {
            "Landing": 0,
            "Products": 0,
            "Product": 0,
            "Cart": 0,
            "Checkout": 0,
            "Other": 0
        }

        funnel_reach: Dict[str, int] = {
            "Landing": 0,
            "Products": 0,
            "Product": 0,
            "Cart": 0,
            "Checkout": 0
        }

        journeys_list: List[List[str]] = []

        for s in sessions:
            collapsed_journey: List[str] = []
            visited_stages = set()

            for req in s.requests:
                stage = map_path_to_stage(req.path)
                req.journey_stage = stage
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
                visited_stages.add(stage)

                if not collapsed_journey or collapsed_journey[-1] != stage:
                    collapsed_journey.append(stage)

            s.journey = collapsed_journey
            journeys_list.append(collapsed_journey)

            for stage in funnel_reach:
                if stage in visited_stages:
                    funnel_reach[stage] += 1

        return JourneyMetrics(
            journeys=journeys_list,
            stage_counts=stage_counts,
            funnel=funnel_reach
        )
