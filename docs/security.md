# Security and Configuration Operations Guide

This document describes the operational configuration settings, security parameters, and hardening mechanisms implemented in `unilog` to handle untrusted input payloads safely.

---

## 1. Environment Configurations Reference

All security constraints and resource allocations are fully configurable via the environment variables listed below. Values are validated during application startup, causing the server to fail fast if incorrect values or relational limits are configured.

| Environment Variable | Description | Default Value | Validation Rules |
| :--- | :--- | :--- | :--- |
| `UNILOG_MAX_FILE_SIZE` | Max raw file size allowed for multi-part uploads | 100 MB (`104857600` B) | `> 0` |
| `UNILOG_MAX_DECOMPRESSED_SIZE` | Max uncompressed bytes allowed for Gzip payloads | 200 MB (`209715200` B) | `> UNILOG_MAX_FILE_SIZE` |
| `UNILOG_DECOMPRESS_CHUNK_SIZE` | Chunk read size used during streaming decompression | 1 MB (`1048576` B) | `> 0` |
| `UNILOG_BACKGROUND_THRESHOLD` | File size trigger threshold for asynchronous task queues | 1 MB (`1048576` B) | `> 0` |
| `UNILOG_RATE_LIMIT` | API request rate limit constraint | `"100/minute"` | String |
| `UNILOG_TASK_TTL_SECONDS` | In-memory background task database expiration (TTL) | 1 Hour (`3600` s) | `> 0` |
| `UNILOG_MAX_TASKS` | Max tasks stored in memory before evicting the oldest | 100 tasks | `> 0` |
| `UNILOG_MAX_PARSE_TEXT` | String length limit for log payload parsed via JSON POST | 10 MB (`10485760` chars) | `> 0` |
| `UNILOG_MAX_DETECT_TEXT` | String length limit for format auto-detection payload | 1 MB (`1048576` chars) | `> 0` |
| `UNILOG_MAX_STATS_TEXT` | String length limit for statistics parsing payload | 10 MB (`10485760` chars) | `> 0` |

---

## 2. Hardening Details

### Safe Gzip Decompression (Decompression Bomb Protection)
When compressed Gzip files are uploaded to `/api/v1/log/upload`, `unilog` reads the file chunk-by-chunk using a buffer size of `UNILOG_DECOMPRESS_CHUNK_SIZE`. The decompressed size is tracked dynamically. If the total decompressed size exceeds `UNILOG_MAX_DECOMPRESSED_SIZE`, the parser aborts immediately and raises a `DecompressionLimitExceeded` error, converting to HTTP 413.

### XML Entity Expansion Prevention
The Windows Event Log parser (`WindowsParser`) uses the `defusedxml` package to process Event lines. This ensures DTD entity resolution and recursively nested entities (billion laughs attack) are blocked and result in a clean parsing error (`_parse_error: True`) instead of consuming CPU or crashing the process.

### Tasks Database Resource Eviction
To prevent background task database size growth from causing Out-Of-Memory (OOM) leaks, the API executes `cleanup_tasks()` on task uploads and task detail lookups.
* **TTL Eviction**: Expired tasks older than `UNILOG_TASK_TTL_SECONDS` are purged.
* **Capacity Limit Eviction**: If task count exceeds `UNILOG_MAX_TASKS`, the oldest task records (sorted by their `created_at` timestamp) are evicted immediately.
