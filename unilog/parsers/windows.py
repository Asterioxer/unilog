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

    def _find_el(self, parent: Any, tag: str, ns: dict[str, str]) -> Optional[Any]:
        """Helper to find element with namespace prefix or fallback to plain tag.
        Avoids boolean evaluation of Element objects since empty elements evaluate to False.
        """
        el = parent.find(f"ns:{tag}", ns)
        if el is None:
            el = parent.find(tag)
        return el

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

                system = self._find_el(root, "System", ns)
                if system is None:
                    return {"_parse_error": True, "raw": line}

                provider = self._find_el(system, "Provider", ns)
                source = provider.get("Name") if provider is not None else None

                eid_el = self._find_el(system, "EventID", ns)
                event_id = safe_int(eid_el.text) if eid_el is not None else None

                time_el = self._find_el(system, "TimeCreated", ns)
                raw_ts = time_el.get("SystemTime") if time_el is not None else None
                timestamp = normalize_timestamp(raw_ts) if raw_ts else None

                lvl_el = self._find_el(system, "Level", ns)
                raw_lvl = safe_int(lvl_el.text) if lvl_el is not None else None
                level = {1: "CRITICAL", 2: "ERROR", 3: "WARNING", 4: "INFO"}.get(raw_lvl or 0, "INFO")

                task_el = self._find_el(system, "Task", ns)
                category = task_el.text if task_el is not None else None

                event_data = self._find_el(root, "EventData", ns)
                message = ""
                if event_data is not None:
                    parts = []
                    # Find all Data elements with ns prefix or fallback
                    data_elements = event_data.findall("ns:Data", ns)
                    if not data_elements:
                        data_elements = event_data.findall("Data")
                    for data in data_elements:
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

        # Check if the first line is a Windows Event Viewer CSV header
        first_line = sample_lines[0]
        if self._is_event_viewer_csv(first_line):
            return 0.95

        # Try to parse the sample lines as a CSV block to see if it yields Windows Event rows
        try:
            sample_text = "\n".join(sample_lines)
            reader = csv.reader(io.StringIO(sample_text))
            rows = list(reader)
            if rows:
                valid_rows = 0
                for row in rows[:5]:  # check first few rows
                    if len(row) >= 4:
                        raw_lvl = row[0].strip().upper()
                        event_id = row[3].strip()
                        known_levels = {"INFORMATION", "WARNING", "ERROR", "CRITICAL", "AUDIT SUCCESS", "AUDIT FAILURE"}
                        if raw_lvl in known_levels and (event_id.isdigit() or not event_id):
                            valid_rows += 1
                if valid_rows > 0:
                    return 0.90
        except Exception:
            pass

        # Fallback to line-by-line matching (e.g. for XML)
        return super().confidence_score(sample_lines)
