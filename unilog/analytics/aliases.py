"""Centralized field names and query aliases for structured logs extraction."""

LATENCY_FIELDS = (
    "latency",
    "duration",
    "response_time",
    "request_time",
    "time_taken",
    "latency_ms",
    "duration_ms",
)

REQUEST_SIZE_FIELDS = (
    "request_length",
    "request_size",
    "body_bytes_received",
)

RESPONSE_SIZE_FIELDS = (
    "size",
    "bytes_sent",
    "body_bytes_sent",
    "response_size",
)
