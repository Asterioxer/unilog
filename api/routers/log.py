import io
import json
import uuid
import time
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from api.dependencies.rate_limiter import limiter
from typing import Optional

import unilog
from unilog.registry import get_parser
from api.schemas.log import (
    ParseRequest, ParseResponse,
    DetectRequest, DetectResponse,
    StatsRequest, StatsResponse,
    FormatsResponse, FormatDetail,
    UploadResponse
)
from api.services.background_tasks import process_file_task, tasks_db, get_task_status, cleanup_tasks
from api.config import (
    UNILOG_MAX_FILE_SIZE,
    UNILOG_BACKGROUND_THRESHOLD,
    UNILOG_RATE_LIMIT,
    UNILOG_MAX_DECOMPRESSED_SIZE,
    UNILOG_DECOMPRESS_CHUNK_SIZE
)
from api.utils.decompression import decompress_gzip_safe, DecompressionLimitExceeded

router = APIRouter(tags=["Logs"])

# Allowed extensions loaded from configuration
ALLOWED_EXTENSIONS = {".log", ".txt", ".json", ".csv", ".gz"}
RATE_LIMIT_VALUE = UNILOG_RATE_LIMIT

@router.post(
    "/parse",
    response_model=ParseResponse,
    summary="Parse raw log text",
    description="Analyze a payload of log lines and return structured JSON records."
)
@limiter.limit(RATE_LIMIT_VALUE)
async def parse_logs(request: Request, req: ParseRequest):
    if req.format and req.format != "auto" and not get_parser(req.format):
        raise HTTPException(status_code=400, detail=f"Invalid format requested: {req.format}")
    try:
        df = unilog.parse_string(req.log_text, format=req.format)
        records = df.to_dict(orient="records")
        return {"records": records, "total": len(records)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse logs: {e}")


@router.post(
    "/detect",
    response_model=DetectResponse,
    summary="Detect log format",
    description="Detect log format and list confidence scores for registered parsers."
)
@limiter.limit(RATE_LIMIT_VALUE)
async def detect_logs(request: Request, req: DetectRequest):
    try:
        # StringIO stream to avoid string memory duplication
        stream_obj = io.StringIO(req.log_text)
        res = unilog.detect(stream_obj)
        
        # Normalize rankings to schema
        rankings = [{"format": r["format"], "confidence": r["confidence"]} for r in res.get("rankings", [])]
        
        return {
            "format": res["format"],
            "confidence": res["confidence"],
            "rankings": rankings,
            "reason": res["reason"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Format detection failed: {e}")


@router.post(
    "/stats",
    response_model=StatsResponse,
    summary="Generate log statistics",
    description="Compute summary statistics and details (error rates, endpoints, IPs) on the provided log payload."
)
@limiter.limit(RATE_LIMIT_VALUE)
async def stats_logs(request: Request, req: StatsRequest):
    if req.format and req.format != "auto" and not get_parser(req.format):
        raise HTTPException(status_code=400, detail=f"Invalid format requested: {req.format}")
    try:
        stream_obj = io.StringIO(req.log_text)
        s = unilog.stats(stream_obj)
        
        return {
            "format": s.get("format", "unknown"),
            "total_lines": s.get("total_lines", 0),
            "error_rate": s.get("error_rate", 0.0),
            "http_5xx_rate": s.get("http_5xx_rate"),
            "time_range": list(s["time_range"]) if s.get("time_range") is not None else None,
            "top_ips": s.get("top_ips", []),
            "log_levels": s.get("log_levels", {}),
            "top_endpoints": s.get("top_endpoints", []),
            "bytes_transferred": s.get("bytes_transferred", 0),
            "status_codes": s.get("status_codes", {})
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate log statistics: {e}")


@router.post(
    "/formats",
    response_model=FormatsResponse,
    summary="List registered log formats",
    description="Get details of all built-in and pluggable parser formats registered."
)
@limiter.limit(RATE_LIMIT_VALUE)
async def formats_logs(request: Request):
    try:
        fmts = unilog.list_formats()
        result_formats = []
        for f in fmts:
            result_formats.append(FormatDetail(
                name=f["name"],
                description=f["description"],
                priority=f["priority"],
                supported_extensions=f.get("supported_extensions", [])
            ))
        return {"formats": result_formats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve formats: {e}")


@router.post(
    "/stream",
    summary="Stream parsed records",
    description="Stream parsed JSON log records chunked and line-by-line."
)
@limiter.limit(RATE_LIMIT_VALUE)
async def stream_logs(request: Request, req: ParseRequest):
    if req.format and req.format != "auto" and not get_parser(req.format):
        raise HTTPException(status_code=400, detail=f"Invalid format requested: {req.format}")
    try:
        def log_generator():
            stream_obj = io.StringIO(req.log_text)
            for record in unilog.stream(stream_obj, format=req.format):
                yield json.dumps(record, default=str) + "\n"

        return StreamingResponse(log_generator(), media_type="application/x-json-stream")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Streaming parsing failed: {e}")


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload log file for parsing",
    description="Upload a log file (.log, .txt, .json, .csv, or .gz). Large files (>1MB) are parsed asynchronously."
)
@limiter.limit(RATE_LIMIT_VALUE)
async def upload_log_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Log file payload"),
    format: Optional[str] = Form(None, description="Explicit parser format (optional)")
):
    if format and format != "auto" and not get_parser(format):
        raise HTTPException(status_code=400, detail=f"Invalid format requested: {format}")
    # Validate extension
    filename = file.filename or ""
    # Extract extension supporting .gz suffix
    lower_name = filename.lower()
    has_valid_ext = False
    for ext in ALLOWED_EXTENSIONS:
        if lower_name.endswith(ext):
            has_valid_ext = True
            break
            
    if not has_valid_ext:
        raise HTTPException(status_code=400, detail="Invalid file extension. Allowed: .log, .txt, .json, .csv, .gz")

    # Read content
    try:
        content = await file.read()
    except Exception as read_ex:
        raise HTTPException(status_code=400, detail=f"Failed to read file payload: {read_ex}")

    # Validate size and empty check
    size = len(content)
    if size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if size > UNILOG_MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"Uploaded file exceeds maximum limit of {UNILOG_MAX_FILE_SIZE} bytes.")

    resolved_format = format or "auto"

    # Route to background task if file size exceeds threshold
    if size > UNILOG_BACKGROUND_THRESHOLD:
        cleanup_tasks()
        task_id = str(uuid.uuid4())
        tasks_db[task_id] = {
            "status": "processing",
            "filename": filename,
            "result": None,
            "error": None,
            "created_at": time.time()
        }
        background_tasks.add_task(
            process_file_task,
            task_id=task_id,
            content=content,
            filename=filename,
            parser_format=resolved_format
        )
        return {
            "task_id": task_id,
            "status": "processing",
            "filename": filename,
            "size": size,
            "format": resolved_format,
            "records": None
        }

    # Synchronous processing for smaller files
    try:
        # Handle gz decompression safely
        if lower_name.endswith(".gz") or content.startswith(b"\x1f\x8b"):
            try:
                content = decompress_gzip_safe(
                    content,
                    max_size=UNILOG_MAX_DECOMPRESSED_SIZE,
                    chunk_size=UNILOG_DECOMPRESS_CHUNK_SIZE
                )
            except DecompressionLimitExceeded as limit_ex:
                raise HTTPException(status_code=413, detail=str(limit_ex))
            except Exception as dec_ex:
                raise HTTPException(status_code=400, detail=f"Gzip decompression failed: {dec_ex}")

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        if resolved_format == "auto":
            det = unilog.detect(io.StringIO(text))
            resolved_format = det["format"]

        df = unilog.parse_string(text, format=resolved_format)
        records = df.to_dict(orient="records")

        return {
            "task_id": None,
            "status": "completed",
            "filename": filename,
            "size": size,
            "format": resolved_format,
            "records": records
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parsing failed: {e}")


@router.get(
    "/tasks/{task_id}",
    summary="Get background task status",
    description="Retrieve execution state and parsed records of an asynchronous background parsing task."
)
@limiter.limit(RATE_LIMIT_VALUE)
async def check_task(request: Request, task_id: str):
    status_info = get_task_status(task_id)
    if status_info["status"] == "not_found":
        raise HTTPException(status_code=404, detail=status_info["error"])
    return status_info
