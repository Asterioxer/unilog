import io
import time
import logging
from typing import Dict, Any

import unilog
from api.config import (
    UNILOG_MAX_DECOMPRESSED_SIZE,
    UNILOG_DECOMPRESS_CHUNK_SIZE,
    UNILOG_TASK_TTL_SECONDS,
    UNILOG_MAX_TASKS
)
from api.utils.decompression import decompress_gzip_safe, DecompressionLimitExceeded

logger = logging.getLogger("unilog-api")

# In-memory database of tasks
# Schema: task_id -> {"status": str, "filename": str, "result": Any, "error": str, "created_at": float}
tasks_db: Dict[str, Dict[str, Any]] = {}

def cleanup_tasks() -> None:
    """Evict task records that are expired or exceed the maximum task storage queue limit."""
    now = time.time()
    
    # 1. Evict tasks exceeding TTL
    expired_ids = [
        tid for tid, task in tasks_db.items()
        if now - task.get("created_at", 0) > UNILOG_TASK_TTL_SECONDS
    ]
    for tid in expired_ids:
        tasks_db.pop(tid, None)

    # 2. Evict oldest tasks if limit is exceeded
    if len(tasks_db) > UNILOG_MAX_TASKS:
        sorted_tasks = sorted(
            tasks_db.items(),
            key=lambda x: x[1].get("created_at", 0.0)
        )
        excess = len(tasks_db) - UNILOG_MAX_TASKS
        for i in range(excess):
            tasks_db.pop(sorted_tasks[i][0], None)

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Retrieve status and results of a background task, after cleaning expired records."""
    cleanup_tasks()
    return tasks_db.get(task_id, {"status": "not_found", "error": f"Task '{task_id}' does not exist."})

def process_file_task(task_id: str, content: bytes, filename: str, parser_format: str):
    """Background task processor for log file parsing with safe decompression limits."""
    existing_task = tasks_db.get(task_id, {})
    created_at = existing_task.get("created_at", time.time())
    metadata = existing_task.get("metadata")
    client_ip = metadata.get("client_ip", "unknown") if metadata else "unknown"

    try:
        # Handle gzip decompression
        if filename.endswith(".gz") or content.startswith(b"\x1f\x8b"):
            try:
                content = decompress_gzip_safe(
                    content,
                    max_size=UNILOG_MAX_DECOMPRESSED_SIZE,
                    chunk_size=UNILOG_DECOMPRESS_CHUNK_SIZE
                )
            except DecompressionLimitExceeded as size_ex:
                logger.error(
                    "Background tasks decompression limit exceeded: %s",
                    str(size_ex),
                    extra={"task_id": task_id, "client_ip": client_ip}
                )
                tasks_db[task_id] = {
                    "status": "failed",
                    "filename": filename,
                    "result": None,
                    "error": "Gzip decompression limit exceeded.",
                    "created_at": created_at,
                    "metadata": metadata
                }
                return
            except Exception as ex:
                logger.error(
                    "Background tasks decompression failed: %s",
                    str(ex),
                    exc_info=True,
                    extra={"task_id": task_id, "client_ip": client_ip}
                )
                tasks_db[task_id] = {
                    "status": "failed",
                    "filename": filename,
                    "result": None,
                    "error": "Gzip decompression failed.",
                    "created_at": created_at,
                    "metadata": metadata
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
            "error": None,
            "created_at": created_at,
            "metadata": metadata
        }

    except Exception as e:
        logger.error(
            "Background task execution failed: %s",
            str(e),
            exc_info=True,
            extra={"task_id": task_id, "client_ip": client_ip}
        )
        tasks_db[task_id] = {
            "status": "failed",
            "filename": filename,
            "result": None,
            "error": "Failed to parse log file.",
            "created_at": created_at,
            "metadata": metadata
        }
