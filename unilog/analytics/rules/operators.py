"""Operator registry mapping string identifiers to callable comparators."""

import operator as op
from typing import Callable, Dict

OPERATORS: Dict[str, Callable[[float, float], bool]] = {
    "gt": op.gt,
    "lt": op.lt,
    "gte": op.ge,
    "lte": op.le,
    "eq": op.eq,
}


def get_operator(name: str) -> Callable[[float, float], bool]:
    """Resolve an operator name to its callable, raising ValueError on unknown names."""
    if name not in OPERATORS:
        raise ValueError(f"Unknown operator '{name}'. Valid operators: {list(OPERATORS)}")
    return OPERATORS[name]
