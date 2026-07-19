import io
import json
import uuid
import time
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import StreamingResponse

from api.dependencies.rate_limiter import limiter
from api.security.network import resolve_client_ip
from typing import Any, Optional

import unilog
from unilog.registry import get_parser
from api.schemas.log import (
    ParseRequest, ParseResponse,
    DetectRequest, DetectResponse,
    StatsRequest, StatsResponse,
    FormatsResponse, FormatDetail,
    UploadResponse
)
from api.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from api.services.background_tasks import process_file_task, tasks_db, get_task_status, cleanup_tasks
from api.config import (
    UNILOG_MAX_FILE_SIZE,
    UNILOG_BACKGROUND_THRESHOLD,
    UNILOG_RATE_LIMIT,
    UNILOG_MAX_DECOMPRESSED_SIZE,
    UNILOG_DECOMPRESS_CHUNK_SIZE
)
from api.utils.decompression import decompress_gzip_safe, DecompressionLimitExceeded

logger = logging.getLogger("unilog-api")

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
        logger.error(
            "Failed to parse logs: %s",
            str(e),
            exc_info=True,
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": resolve_client_ip(request)
            }
        )
        raise HTTPException(status_code=400, detail="Failed to parse logs.")


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
        logger.error(
            "Format detection failed: %s",
            str(e),
            exc_info=True,
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": resolve_client_ip(request)
            }
        )
        raise HTTPException(status_code=400, detail="Format detection failed.")


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
        logger.error(
            "Failed to generate log statistics: %s",
            str(e),
            exc_info=True,
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": resolve_client_ip(request)
            }
        )
        raise HTTPException(status_code=400, detail="Failed to generate log statistics.")


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Run full analytics pipeline",
    description="Parse log text, compile the MetricsBundle via all registered analyzers, "
                "optionally evaluate the built-in rule set, and return the complete AnalysisResult.",
)
@limiter.limit(RATE_LIMIT_VALUE)
async def analyze_logs(request: Request, req: AnalyzeRequest):
    if req.format and req.format != "auto" and not get_parser(req.format):
        raise HTTPException(status_code=400, detail=f"Invalid format requested: {req.format}")
    try:
        # Parse log text into records
        stream_obj = io.StringIO(req.log_text)
        records = list(unilog.stream(stream_obj, format=req.format))

        # Compile metrics
        from unilog.analytics import MetricsEngine, AnalyzerContext
        context = AnalyzerContext(window_minutes=req.window_minutes)
        engine = MetricsEngine()
        result = engine.compile(records, context=context)

        # Optionally evaluate rules
        insights_response: list[dict[str, Any]] = []
        if req.enable_rules:
            from unilog.analytics.rules import RuleEngine as InsightRuleEngine
            from unilog.analytics.rules.builtin import collect_all_rules
            from unilog.analytics.rules.models import RuleSet, RuleContext
            from datetime import datetime, timezone

            ruleset = RuleSet(rules=collect_all_rules())
            rule_context = RuleContext(
                timestamp=datetime.now(timezone.utc),
                window_minutes=req.window_minutes,
                analyzed_records=result.metadata.analyzed_records,
                skipped_records=result.metadata.skipped_records,
            )
            rule_engine = InsightRuleEngine()
            triggered_insights = rule_engine.evaluate(
                bundle=result.metrics,
                ruleset=ruleset,
                context=rule_context,
            )
            insights_response = [
                {
                    "id": ins.id,
                    "category": ins.category,
                    "severity": ins.severity,
                    "confidence": ins.confidence,
                    "description": ins.description,
                    "recommendation": ins.recommendation,
                    "evidence": ins.evidence,
                }
                for ins in triggered_insights
            ]

        return {
            "metrics": result.metrics.model_dump(exclude_none=True),
            "insights": insights_response,
            "metadata": {
                "analyzed_records": result.metadata.analyzed_records,
                "skipped_records": result.metadata.skipped_records,
                "missing_latency_fields": result.metadata.missing_latency_fields,
                "execution_time_ms": result.metadata.execution_time_ms,
                "analyzers": [
                    {"name": a.name, "version": a.version}
                    for a in result.metadata.analyzers
                ],
            },
            "ruleset_version": result.ruleset_version,
        }
    except Exception as e:
        logger.error(
            "Analytics pipeline failed: %s",
            str(e),
            exc_info=True,
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": resolve_client_ip(request),
            },
        )
        raise HTTPException(status_code=400, detail="Analytics pipeline failed.")


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
        logger.error(
            "Failed to retrieve formats: %s",
            str(e),
            exc_info=True,
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": resolve_client_ip(request)
            }
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve formats.")


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
        logger.error(
            "Streaming parsing failed: %s",
            str(e),
            exc_info=True,
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": resolve_client_ip(request)
            }
        )
        raise HTTPException(status_code=400, detail="Streaming parsing failed.")


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload log file for parsing",
    description=(
        "Upload a log file (.log, .txt, .json, .csv, or .gz). "
        "Large files (>1MB) are parsed asynchronously and return a task_id. "
        "Leave **format** empty (or set to 'auto') to let unilog auto-detect the format. "
        "Valid explicit values: nginx, apache, syslog, syslog5424, json, django, windows_event."
    )
)
@limiter.limit(RATE_LIMIT_VALUE)
async def upload_log_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Log file payload"),
    format: Optional[str] = Form(
        None,
        description="Parser format: leave blank or use 'auto' to auto-detect. Valid values: nginx, apache, syslog, syslog5424, json, django, windows_event."
    )
):
    # Treat Swagger UI placeholder sentinel and 'auto' as no explicit format
    if format in ("string", "auto", ""):
        format = None
    if format and not get_parser(format):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown format '{format}'. Leave blank for auto-detect, or use: nginx, apache, syslog, syslog5424, json, django, windows_event."
        )
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
        logger.error(
            "Failed to read file payload: %s",
            str(read_ex),
            exc_info=True,
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": resolve_client_ip(request)
            }
        )
        raise HTTPException(status_code=400, detail="Failed to read file payload.")

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
        
        from api.schemas.task import TaskMetadata
        metadata = TaskMetadata(
            created_at=time.time(),
            client_ip=resolve_client_ip(request),
            owner_id=None
        )
        
        tasks_db[task_id] = {
            "status": "processing",
            "filename": filename,
            "result": None,
            "error": None,
            "metadata": metadata.model_dump()
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
                logger.error(
                    "Gzip decompression failed: %s",
                    str(dec_ex),
                    exc_info=True,
                    extra={
                        "request_id": getattr(request.state, "request_id", "unknown"),
                        "client_ip": resolve_client_ip(request)
                    }
                )
                raise HTTPException(status_code=400, detail="Gzip decompression failed.")

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        if resolved_format == "auto":
            det = unilog.detect(io.StringIO(text))
            resolved_format = det["format"]
            # Event Viewer CSV has multi-line quoted fields — line-sampling returns 'unknown'.
            # Explicitly try 'windows' parser when we have a .csv that didn't resolve.
            if resolved_format == "unknown" and lower_name.endswith(".csv"):
                from unilog.parsers.windows import WindowsParser
                wp = WindowsParser()
                if wp._is_event_viewer_csv(text):
                    resolved_format = "windows"

        # parse_string uses parser.parse() directly for parsers that override it (e.g. windows)
        parse_format = None if resolved_format == "unknown" else resolved_format
        df = unilog.parse_string(text, format=parse_format)
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
        logger.error(
            "Parsing failed: %s",
            str(e),
            exc_info=True,
            extra={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "client_ip": resolve_client_ip(request)
            }
        )
        raise HTTPException(status_code=400, detail="Parsing failed.")


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
