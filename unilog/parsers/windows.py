import csv
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime
from unilog.parsers.base import BaseParser
from unilog.registry import register_parser
from unilog.utils import normalize_timestamp, safe_int

@register_parser
class WindowsParser(BaseParser):
    """Parser for Windows Event Log exports (CSV and XML)."""
    
    name = "windows"
    description = "Windows Event Log (CSV / XML)"
    priority = 55
    supported_extensions = [".csv", ".xml"]

    required_fields = ["timestamp", "level", "source", "event_id"]
    optional_fields = ["category", "message"]

    def _is_csv_header(self, row: List[str]) -> bool:
        if not row:
            return False
        headers = {"level", "date and time", "source", "event id", "task category", "description"}
        return any(cell.strip().lower() in headers for cell in row)

    def match(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return False

        if line.startswith("<Event") and "</Event>" in line:
            return True

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
        line = line.strip()
        if not line or not self.match(line):
            return {"_parse_error": True, "raw": line}

        timestamp: Optional[datetime] = None
        level: str = "INFO"
        source: Optional[str] = None
        event_id: Optional[int] = None
        category: Optional[str] = None
        message: Optional[str] = None

        # Handle XML Event
        if line.startswith("<Event"):
            try:
                root = ET.fromstring(line)
                ns = {'ns': 'http://schemas.microsoft.com/win/2004/08/events/event'}
                
                system = root.find('ns:System', ns)
                if system is None:
                    system = root.find('System')
                
                if system is None:
                    return {"_parse_error": True, "raw": line}

                # Find Provider (Source)
                provider = system.find('ns:Provider', ns)
                if provider is None:
                    provider = system.find('Provider')
                source = provider.get('Name') if provider is not None else None

                # Find EventID
                event_id_el = system.find('ns:EventID', ns)
                if event_id_el is None:
                    event_id_el = system.find('EventID')
                event_id = safe_int(event_id_el.text) if event_id_el is not None else None

                # Find TimeCreated
                time_el = system.find('ns:TimeCreated', ns)
                if time_el is None:
                    time_el = system.find('TimeCreated')
                raw_ts = time_el.get('SystemTime') if time_el is not None else None
                timestamp = normalize_timestamp(raw_ts) if raw_ts else None

                # Find Level
                level_el = system.find('ns:Level', ns)
                if level_el is None:
                    level_el = system.find('Level')
                raw_lvl = safe_int(level_el.text) if level_el is not None else None
                
                level = "INFO"
                if raw_lvl == 1:
                    level = "CRITICAL"
                elif raw_lvl == 2:
                    level = "ERROR"
                elif raw_lvl == 3:
                    level = "WARNING"
                elif raw_lvl == 4:
                    level = "INFO"

                # Find Task (Category)
                task_el = system.find('ns:Task', ns)
                if task_el is None:
                    task_el = system.find('Task')
                category = task_el.text if task_el is not None else None

                # Get description/message from EventData
                event_data = root.find('ns:EventData', ns)
                if event_data is None:
                    event_data = root.find('EventData')
                
                message = ""
                if event_data is not None:
                    data_elements = event_data.findall('ns:Data', ns)
                    if not data_elements:
                        data_elements = event_data.findall('Data')
                    message_parts = []
                    for data in data_elements:
                        name = data.get('Name')
                        val = data.text or ""
                        if name:
                            message_parts.append(f"{name}={val}")
                        else:
                            message_parts.append(val)
                    message = "; ".join(message_parts)

                return {
                    "timestamp": timestamp,
                    "level": level,
                    "source": source,
                    "event_id": event_id,
                    "category": category,
                    "message": message or None,
                    "raw": line
                }
            except Exception:
                return {"_parse_error": True, "raw": line}

        # Handle CSV line
        try:
            reader = csv.reader([line])
            row = next(reader)
            if self._is_csv_header(row):
                return {"_parse_error": True, "raw": line}
            
            while len(row) < 6:
                row.append("")

            raw_csv_lvl = row[0].strip()
            level = raw_csv_lvl.upper()
            if level == "INFORMATION":
                level = "INFO"
            elif level == "WARNING":
                level = "WARNING"
            elif level == "ERROR":
                level = "ERROR"
            elif level == "CRITICAL":
                level = "CRITICAL"
                
            raw_ts = row[1].strip()
            timestamp = normalize_timestamp(raw_ts)

            source = row[2].strip() or None
            event_id = safe_int(row[3])
            category = row[4].strip() or None
            message = row[5].strip() or None

            return {
                "timestamp": timestamp,
                "level": level,
                "source": source,
                "event_id": event_id,
                "category": category,
                "message": message,
                "raw": line
            }
        except Exception:
            return {"_parse_error": True, "raw": line}

    def confidence_score(self, sample_lines: List[str]) -> float:
        if not sample_lines:
            return 0.0
        
        matches = 0
        total_lines = 0
        for line in sample_lines:
            line_str = line.strip()
            if not line_str:
                continue
            total_lines += 1
            if self.match(line_str):
                matches += 1

        if total_lines == 0:
            return 0.0

        ratio = matches / total_lines
        return ratio * 0.80
