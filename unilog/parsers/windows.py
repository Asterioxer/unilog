import csv
import io
import defusedxml  # type: ignore
import defusedxml.ElementTree as ET  # type: ignore
from typing import Dict, Any, List, Optional, Iterator
from datetime import datetime
from unilog.parsers.base import BaseParser
from unilog.registry import register_parser
from unilog.utils import normalize_timestamp, safe_int


@register_parser
class WindowsParser(BaseParser):
    """Parser for Windows Event Log exports (CSV and XML).

    Supports two input shapes:
    - Windows Event Viewer CSV export (multi-line quoted message field)
    - Windows Event Log XML (one <Event>...</Event> per line)
    """

    name = "windows"
    description = "Windows Event Log (CSV / XML)"
    priority = 55
    supported_extensions = [".csv", ".xml"]

    required_fields = ["timestamp", "level", "source", "event_id"]
    optional_fields = ["category", "message"]

    # Columns present in a Windows Event Viewer CSV header row
    _CSV_HEADERS = {"keywords", "date and time", "source", "event id", "task category"}

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────

    def _is_csv_header(self, row: List[str]) -> bool:
        if not row:
            return False
        known = {"level", "date and time", "source", "event id", "task category",
                 "description", "keywords"}
        return any(cell.strip().lower() in known for cell in row)

    def _is_event_viewer_csv(self, text: str) -> bool:
        """Return True when the first line looks like an Event Viewer CSV header."""
        first_line = text.strip().splitlines()[0] if text.strip() else ""
        try:
            row = next(csv.reader([first_line]))
            cols = {c.strip().lower() for c in row}
            return bool(cols & self._CSV_HEADERS)
        except Exception:
            return False

    def _parse_csv_row(self, row: List[str]) -> Dict[str, Any]:
        """Turn a fully-assembled CSV row into a structured record dict."""
        while len(row) < 6:
            row.append("")

        raw_lvl = row[0].strip().upper()
        if raw_lvl == "INFORMATION":
            level = "INFO"
        elif raw_lvl == "AUDIT SUCCESS":
            level = "AUDIT_SUCCESS"
        elif raw_lvl == "AUDIT FAILURE":
            level = "AUDIT_FAILURE"
        elif raw_lvl in ("WARNING", "ERROR", "CRITICAL"):
            level = raw_lvl
        else:
            level = "INFO"

        raw_ts = row[1].strip()
        timestamp = normalize_timestamp(raw_ts)

        source = row[2].strip() or None
        event_id = safe_int(row[3].strip())
        category = row[4].strip() or None
        # Column 5 holds the full event message (may be very long / multi-line)
        message = row[5].strip() if len(row) > 5 else None

        if timestamp is None and source is None and event_id is None:
            return {"_parse_error": True, "raw": ",".join(row)}

        return {
            "timestamp": timestamp,
            "level": level,
            "source": source,
            "event_id": event_id,
            "category": category,
            "message": message or None,
            "raw": ",".join(row),
        }

    # ──────────────────────────────────────────────────────────────
    # Core parsing interface
    # ──────────────────────────────────────────────────────────────

    def parse(self, text: str) -> Iterator[Dict[str, Any]]:
        """Override base parse() to handle Windows Event Viewer CSV exports.

        The Event Viewer CSV stores the full event message as a multi-line quoted
        field, so one logical record can span 40+ physical lines.  Python's
        csv.reader handles quoted multi-line fields natively — feed it the whole
        text block instead of line-by-line.

        For XML format (one <Event>…</Event> per physical line) and other inputs
        fall back to the standard line-by-line parse_line() path.
        """
        text = text.strip()
        if not text:
            return

        if self._is_event_viewer_csv(text):
            reader = csv.reader(io.StringIO(text))
            for i, row in enumerate(reader):
                if i == 0:
                    continue  # skip header
                if not any(cell.strip() for cell in row):
                    continue  # skip blank rows
                yield self._parse_csv_row(row)
            return

        # XML or other line-based formats
        for line in text.splitlines():
            line = line.strip()
            if line:
                yield self.parse_line(line)

    def match(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return False

        # Single-line XML event
        if line.startswith("<Event") and "</Event>" in line:
            return True

        # CSV line (header or data)
        if "," in line:
            try:
                reader = csv.reader([line])
                row = next(reader)
                if len(row) >= 4:
                    if self._is_csv_header(row):
                        return True
                    event_id = row[3].strip() if len(row) > 3 else ""
                    if event_id.isdigit() or not event_id:
                        return True
            except Exception:
                pass

        return False

    def parse_line(self, line: str) -> Dict[str, Any]:
        """Parse a single physical log line (XML event or single-line CSV row)."""
        line = line.strip()
        if not line or not self.match(line):
            return {"_parse_error": True, "raw": line}

        timestamp: Optional[datetime] = None
        level: str = "INFO"
        source: Optional[str] = None
        event_id: Optional[int] = None
        category: Optional[str] = None
        message: Optional[str] = None

        # ── XML event ────────────────────────────────────────────
        if line.startswith("<Event"):
            try:
                root = ET.fromstring(line)
                ns = {"ns": "http://schemas.microsoft.com/win/2004/08/events/event"}

                system = root.find("ns:System", ns) or root.find("System")
                if system is None:
                    return {"_parse_error": True, "raw": line}

                provider = system.find("ns:Provider", ns) or system.find("Provider")
                source = provider.get("Name") if provider is not None else None

                eid_el = system.find("ns:EventID", ns) or system.find("EventID")
                event_id = safe_int(eid_el.text) if eid_el is not None else None

                time_el = system.find("ns:TimeCreated", ns) or system.find("TimeCreated")
                raw_ts = time_el.get("SystemTime") if time_el is not None else None
                timestamp = normalize_timestamp(raw_ts) if raw_ts else None

                lvl_el = system.find("ns:Level", ns) or system.find("Level")
                raw_lvl = safe_int(lvl_el.text) if lvl_el is not None else None
                level = {1: "CRITICAL", 2: "ERROR", 3: "WARNING", 4: "INFO"}.get(raw_lvl or 0, "INFO")

                task_el = system.find("ns:Task", ns) or system.find("Task")
                category = task_el.text if task_el is not None else None

                event_data = root.find("ns:EventData", ns) or root.find("EventData")
                message = ""
                if event_data is not None:
                    parts = []
                    for data in (event_data.findall("ns:Data", ns) or event_data.findall("Data")):
                        name = data.get("Name")
                        val = data.text or ""
                        parts.append(f"{name}={val}" if name else val)
                    message = "; ".join(parts)

                if timestamp is None and source is None and event_id is None:
                    return {"_parse_error": True, "raw": line}

                return {
                    "timestamp": timestamp,
                    "level": level,
                    "source": source,
                    "event_id": event_id,
                    "category": category,
                    "message": message or None,
                    "raw": line,
                }
            except (defusedxml.common.DefusedXmlException, Exception):
                return {"_parse_error": True, "raw": line}

        # ── Single-line CSV ──────────────────────────────────────
        try:
            row = next(csv.reader([line]))
            if self._is_csv_header(row):
                return {"_parse_error": True, "raw": line}
            return self._parse_csv_row(row)
        except Exception:
            return {"_parse_error": True, "raw": line}

    def confidence_score(self, sample_lines: List[str]) -> float:
        if not sample_lines:
            return 0.0
        matches = 0
        total = 0
        for line in sample_lines:
            s = line.strip()
            if not s:
                continue
            total += 1
            if self.match(s):
                matches += 1
        if total == 0:
            return 0.0
        return (matches / total) * 0.80
