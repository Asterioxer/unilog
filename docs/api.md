# REST API Reference

The `unilog` REST API is versioned under the `/api/v1` path prefix. Health check endpoints are located at the root level.

## Health Check Endpoints

### Liveness Check
- **Endpoint**: `GET /live`
- **Response**: `{"status": "live"}`

### Readiness Check
- **Endpoint**: `GET /ready`
- **Response**: `{"status": "ready"}`

---

## REST Core API Endpoints

### 1. Parse Log Text
- **Endpoint**: `POST /api/v1/parse`
- **Request Body**:
  ```json
  {
    "log_text": "127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] \"GET /index.html HTTP/1.1\" 200 1043",
    "format": "nginx"
  }
  ```
- **Response (200)**:
  ```json
  {
    "records": [
      {
        "source_ip": "127.0.0.1",
        "timestamp": "2026-07-10T20:53:59+05:30",
        "method": "GET",
        "path": "/index.html",
        "http_version": "1.1",
        "status_code": 200,
        "bytes_sent": 1043
      }
    ],
    "total": 1
  }
  ```

### 2. Detect Log Format
- **Endpoint**: `POST /api/v1/detect`
- **Request Body**:
  ```json
  {
    "log_text": "127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] \"GET /index.html HTTP/1.1\" 200 1043"
  }
  ```
- **Response (200)**:
  ```json
  {
    "format": "nginx",
    "confidence": 1.0,
    "rankings": [
      { "format": "nginx", "confidence": 1.0 },
      { "format": "apache", "confidence": 0.95 }
    ],
    "reason": "Successfully matched regex pattern for nginx"
  }
  ```

### 3. File Uploads (Asynchronous / Synchronous)
- **Endpoint**: `POST /api/v1/upload`
- **Request Form Parameters**:
  - `file`: Log file payload (`.log`, `.txt`, `.json`, `.csv`, `.gz`).
  - `format`: Explicit log format (optional, e.g. `nginx`, `json`).
- **Response (200 - Sync for <= 1MB)**:
  ```json
  {
    "task_id": null,
    "status": "completed",
    "filename": "test.log",
    "size": 1024,
    "format": "nginx",
    "records": [...]
  }
  ```
- **Response (200 - Async for > 1MB)**:
  ```json
  {
    "task_id": "b3f07a0c-60b6-4552-a5b1-213970bcf476",
    "status": "processing",
    "filename": "huge_access.log",
    "size": 5242880,
    "format": "auto",
    "records": null
  }
  ```

### 4. Background Job Status
- **Endpoint**: `GET /api/v1/tasks/{task_id}`
- **Response (200 - Completed)**:
  ```json
  {
    "status": "completed",
    "filename": "huge_access.log",
    "result": {
      "records": [...],
      "total": 45000
    },
    "error": null
  }
  ```

---

## Global Error Response Model

All API errors return a standard JSON model:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_LOG",
    "message": "Invalid format requested: invalid_format_name",
    "details": {}
  }
}
```

Common error codes:
- `INVALID_LOG`: Parse validation or schema matching error.
- `NOT_FOUND`: Task/resource not found.
- `FILE_TOO_LARGE`: Uploaded payload size exceeds server threshold.
- `RATE_LIMIT_EXCEEDED`: API rate limit triggered (100 req/min).
- `INTERNAL_SERVER_ERROR`: Unhandled backend exception.
