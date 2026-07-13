"""Shared contracts for stateless analytics analyzers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Mapping, Sequence

from pydantic import BaseModel, Field


class AnalyzerContext(BaseModel):
    """Immutable execution settings supplied to every analyzer invocation."""

    window_minutes: int = Field(
        default=5,
        ge=1,
        description="Size of the analysis window in minutes.",
    )
    timezone: str = Field(
        default="UTC",
        min_length=1,
        description="Target evaluation timezone.",
    )
    bucket_seconds: int = Field(
        default=60,
        ge=1,
        description="Granularity of sub-buckets in seconds.",
    )
    parser_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata from the parsed log format.",
    )


class BaseAnalyzer(ABC):
    """Stateless collector that produces one validated metric model."""

    @abstractmethod
    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> BaseModel:
        """Process normalized records and return a metric model instance."""
        raise NotImplementedError("Analyzers must implement analyze.")