import io
import gzip
from typing import Dict, Any
import unilog

# In-memory database of tasks
# Schema: task_id -> {"status": str, "filename": str, "result": Any, "error": str}
tasks_db: Dict[str, Dict[str, Any]] = {}

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Retrieve status and results of a background task."""
    return tasks_db.get(task_id, {"status": "not_found", "error": f"Task '{task_id}' does not exist."})

def process_file_task(task_id: str, content: bytes, filename: str, parser_format: str):
    """Background task processor for log file parsing."""
    try:
        # Handle gzip decompression
        if filename.endswith(".gz") or content.startswith(b"\x1f\x8b"):
            try:
                content = gzip.decompress(content)
            except Exception as ex:
                tasks_db[task_id] = {
                    "status": "failed",
                    "filename": filename,
                    "result": None,
                    "error": f"Gzip decompression failed: {ex}"
                }
                return

        # Decode contents safely
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        # Automatically resolve format if required
        resolved_format = parser_format
        if resolved_format == "auto" or not resolved_format:
            det = unilog.detect(io.StringIO(text))
            resolved_format = det["format"]

        # Parse string contents
        df = unilog.parse_string(text, format=resolved_format)
        records = df.to_dict(orient="records")

        # Extract basic statistics to return alongside records
        total_records = len(records)
        tasks_db[task_id] = {
            "status": "completed",
            "filename": filename,
            "result": {
                "format": resolved_format,
                "total": total_records,
                "records": records
            },
            "error": None
        }

    except Exception as e:
        tasks_db[task_id] = {
            "status": "failed",
            "filename": filename,
            "result": None,
            "error": str(e)
        }
