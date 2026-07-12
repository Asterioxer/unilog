import os

# Maximum uploaded file size limit (default: 100 MB)
UNILOG_MAX_FILE_SIZE = int(os.environ.get("UNILOG_MAX_FILE_SIZE", str(100 * 1024 * 1024)))

# Background task processing threshold (default: 1 MB)
UNILOG_BACKGROUND_THRESHOLD = int(os.environ.get("UNILOG_BACKGROUND_THRESHOLD", str(1 * 1024 * 1024)))

# Slowapi rate limit value (default: "100/minute")
UNILOG_RATE_LIMIT = os.environ.get("UNILOG_RATE_LIMIT", "100/minute")

# Safe gzip decompression size limit (default: 200 MB)
UNILOG_MAX_DECOMPRESSED_SIZE = int(os.environ.get("UNILOG_MAX_DECOMPRESSED_SIZE", str(200 * 1024 * 1024)))

# Safe gzip decompression streaming chunk read size (default: 1 MB)
UNILOG_DECOMPRESS_CHUNK_SIZE = int(os.environ.get("UNILOG_DECOMPRESS_CHUNK_SIZE", str(1024 * 1024)))

# Tasks database TTL in seconds (default: 1 hour)
UNILOG_TASK_TTL_SECONDS = int(os.environ.get("UNILOG_TASK_TTL_SECONDS", "3600"))

# Tasks database maximum size queue (default: 100 tasks)
UNILOG_MAX_TASKS = int(os.environ.get("UNILOG_MAX_TASKS", "100"))

# Maximum allowed character length of request log string bodies
UNILOG_MAX_PARSE_TEXT = int(os.environ.get("UNILOG_MAX_PARSE_TEXT", str(10 * 1024 * 1024)))
UNILOG_MAX_DETECT_TEXT = int(os.environ.get("UNILOG_MAX_DETECT_TEXT", str(1 * 1024 * 1024)))
UNILOG_MAX_STATS_TEXT = int(os.environ.get("UNILOG_MAX_STATS_TEXT", str(10 * 1024 * 1024)))

def validate_config() -> None:
    """Validate operational bounds on startup to fail-fast on invalid combinations."""
    if UNILOG_MAX_FILE_SIZE <= 0:
        raise ValueError(f"UNILOG_MAX_FILE_SIZE must be positive, got {UNILOG_MAX_FILE_SIZE}")
    if UNILOG_BACKGROUND_THRESHOLD <= 0:
        raise ValueError(f"UNILOG_BACKGROUND_THRESHOLD must be positive, got {UNILOG_BACKGROUND_THRESHOLD}")
    if UNILOG_MAX_DECOMPRESSED_SIZE <= 0:
        raise ValueError(f"UNILOG_MAX_DECOMPRESSED_SIZE must be positive, got {UNILOG_MAX_DECOMPRESSED_SIZE}")
    if UNILOG_DECOMPRESS_CHUNK_SIZE <= 0:
        raise ValueError(f"UNILOG_DECOMPRESS_CHUNK_SIZE must be positive, got {UNILOG_DECOMPRESS_CHUNK_SIZE}")
    if UNILOG_TASK_TTL_SECONDS <= 0:
        raise ValueError(f"UNILOG_TASK_TTL_SECONDS must be positive, got {UNILOG_TASK_TTL_SECONDS}")
    if UNILOG_MAX_TASKS <= 0:
        raise ValueError(f"UNILOG_MAX_TASKS must be positive, got {UNILOG_MAX_TASKS}")
    if UNILOG_MAX_PARSE_TEXT <= 0:
        raise ValueError(f"UNILOG_MAX_PARSE_TEXT must be positive, got {UNILOG_MAX_PARSE_TEXT}")
    if UNILOG_MAX_DETECT_TEXT <= 0:
        raise ValueError(f"UNILOG_MAX_DETECT_TEXT must be positive, got {UNILOG_MAX_DETECT_TEXT}")
    if UNILOG_MAX_STATS_TEXT <= 0:
        raise ValueError(f"UNILOG_MAX_STATS_TEXT must be positive, got {UNILOG_MAX_STATS_TEXT}")

    # Relational validation
    if UNILOG_MAX_DECOMPRESSED_SIZE < UNILOG_MAX_FILE_SIZE:
        raise ValueError(
            f"UNILOG_MAX_DECOMPRESSED_SIZE ({UNILOG_MAX_DECOMPRESSED_SIZE}) must be >= "
            f"UNILOG_MAX_FILE_SIZE ({UNILOG_MAX_FILE_SIZE}) to permit decompression limits."
        )
