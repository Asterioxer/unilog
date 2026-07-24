"""Timeline builder for chronological incident event tracking."""

from typing import Any, List, Mapping, Sequence
from datetime import datetime
from unilog.analytics.schemas import Insight, TimelineEvent


class TimelineBuilder:
    """Constructs a chronological event timeline from insights and records."""

    def build_timeline(
        self,
        insights: Sequence[Insight],
        records: Sequence[Mapping[str, Any]],
    ) -> List[TimelineEvent]:
        """Synthesize and order events chronologically."""
        events: List[TimelineEvent] = []

        # Add insight triggers as timeline events
        for ins in insights:
            ts_str = ins.timestamp.isoformat().replace("+00:00", "Z") if isinstance(ins.timestamp, datetime) else str(ins.timestamp)
            event_type = ins.id.split("-")[0] if "-" in ins.id else ins.category
            
            events.append(
                TimelineEvent(
                    timestamp=ts_str,
                    event_type=event_type,
                    description=ins.description,
                    severity=ins.severity.upper()
                )
            )

        # Sort timeline events chronologically
        events.sort(key=lambda x: x.timestamp)
        return events
