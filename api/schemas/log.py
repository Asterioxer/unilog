from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ParseRequest(BaseModel):
    log_text: str = Field(..., description="Raw log lines to parse")
    format: Optional[str] = Field(None, description="Explicit format to parse (auto-detect if omitted)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "log_text": '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043\n192.168.1.1 - - [10/Jul/2026:20:54:00 +0530] "POST /login HTTP/1.1" 401 230',
                "format": "nginx"
            }
        }
    }

class ParseResponse(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="List of parsed log records")
    total: int = Field(..., description="Total count of records parsed")

class DetectRequest(BaseModel):
    log_text: str = Field(..., description="Raw log lines to analyze for format detection")

    model_config = {
        "json_schema_extra": {
            "example": {
                "log_text": '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
            }
        }
    }

class RankingItem(BaseModel):
    format: str = Field(..., description="Parser format name")
    confidence: float = Field(..., description="Matching confidence score (0.0 to 1.0)")

class DetectResponse(BaseModel):
    format: str = Field(..., description="Best matched log format or 'unknown'")
    confidence: float = Field(..., description="Highest confidence score")
    rankings: List[RankingItem] = Field(..., description="Ranking score for each registered parser")
    reason: str = Field(..., description="Detailed explanation of the detection decision")

    model_config = {
        "json_schema_extra": {
            "example": {
                "format": "nginx",
                "confidence": 1.0,
                "rankings": [
                    {"format": "nginx", "confidence": 1.0},
                    {"format": "apache", "confidence": 0.95}
                ],
                "reason": "Detected format 'nginx' with confidence 1.0."
            }
        }
    }

class StatsRequest(BaseModel):
    log_text: str = Field(..., description="Raw log lines to compute statistics for")
    format: Optional[str] = Field(None, description="Parser format name (auto-detect if omitted)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "log_text": '127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] "GET /index.html HTTP/1.1" 200 1043'
            }
        }
    }

class StatsResponse(BaseModel):
    format: str = Field(..., description="Detected format")
    total_lines: int = Field(..., description="Total log lines parsed")
    error_rate: float = Field(..., description="Log parser failure rate")
    http_5xx_rate: Optional[float] = Field(None, description="HTTP 5xx error rate if status code is present")
    time_range: Optional[List[str]] = Field(None, description="Start and end timestamps (ISO 8601 strings)")
    top_ips: List[List[Any]] = Field(..., description="Top 5 source IPs and their counts")
    log_levels: Dict[str, int] = Field(..., description="Log level counts")
    top_endpoints: List[List[Any]] = Field(..., description="Top 5 request endpoints and their counts")
    bytes_transferred: int = Field(..., description="Sum of transferred bytes")
    status_codes: Dict[str, int] = Field(default_factory=dict, description="HTTP status code distribution")

    model_config = {
        "json_schema_extra": {
            "example": {
                "format": "nginx",
                "total_lines": 1,
                "error_rate": 0.0,
                "http_5xx_rate": 0.0,
                "time_range": ["2026-07-10T20:53:59+05:30", "2026-07-10T20:53:59+05:30"],
                "top_ips": [["127.0.0.1", 1]],
                "log_levels": {},
                "top_endpoints": [["/index.html", 1]],
                "bytes_transferred": 1043
            }
        }
    }

class FormatDetail(BaseModel):
    name: str = Field(..., description="Unique format name")
    description: str = Field(..., description="Human-readable parser description")
    priority: int = Field(..., description="Parsing resolution priority order")
    supported_extensions: List[str] = Field(..., description="Associated file extensions")

class FormatsResponse(BaseModel):
    formats: List[FormatDetail] = Field(..., description="List of all registered log formats")

class UploadResponse(BaseModel):
    task_id: Optional[str] = Field(None, description="Task ID if file is processed in background")
    status: str = Field(..., description="Status of the file parsing request ('completed' or 'processing')")
    filename: str = Field(..., description="Uploaded file name")
    size: int = Field(..., description="Uploaded file size in bytes")
    format: Optional[str] = Field(None, description="Detected or specified format name")
    records: Optional[List[Dict[str, Any]]] = Field(None, description="Parsed records if processed synchronously")
