"""Built-in rules module aggregation."""

from typing import List
from unilog.analytics.rules.models import Rule
from unilog.analytics.rules.builtin.performance import get_rules as get_perf_rules
from unilog.analytics.rules.builtin.reliability import get_rules as get_rel_rules
from unilog.analytics.rules.builtin.traffic import get_rules as get_traf_rules
from unilog.analytics.rules.builtin.security import get_rules as get_sec_rules


def collect_all_rules() -> List[Rule]:
    """Collect and return all built-in rules across all categories."""
    rules = []
    rules.extend(get_perf_rules())
    rules.extend(get_rel_rules())
    rules.extend(get_traf_rules())
    rules.extend(get_sec_rules())
    return rules
