import time
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

# Custom registry for unilog metrics to guarantee clean metric exposition
REGISTRY = CollectorRegistry(auto_describe=True)

# Explicit latency buckets: 1ms, 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s
LATENCY_BUCKETS = (0.001, 0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500, 1.0, 2.5, 5.0, 10.0)

START_TIME = time.time()

# 1. HTTP API & Middleware Telemetry
REQUESTS_TOTAL = Counter(
    "unilog_requests_total",
    "Total HTTP API requests handled",
    ["method", "endpoint", "status", "exception"],
    registry=REGISTRY,
)

PROCESS_UPTIME = Gauge(
    "unilog_process_uptime_seconds",
    "Process uptime in seconds",
    registry=REGISTRY,
)

# 2. Parsing Engine & Performance
LOGS_PROCESSED_TOTAL = Counter(
    "unilog_logs_processed_total",
    "Total log records parsed by syntax format",
    ["format"],
    registry=REGISTRY,
)

PARSER_ERRORS_TOTAL = Counter(
    "unilog_parser_errors_total",
    "Total parsing errors encountered by format",
    ["format"],
    registry=REGISTRY,
)

PARSER_LATENCY_SECONDS = Histogram(
    "unilog_parser_latency_seconds",
    "Distribution of log parsing & compilation duration in seconds",
    ["format"],
    buckets=LATENCY_BUCKETS,
    registry=REGISTRY,
)

# 3. Rules & Threat Intelligence
RULES_TRIGGERED_TOTAL = Counter(
    "unilog_rules_triggered_total",
    "Total heuristic rules triggered",
    ["rule_id", "severity", "category"],
    registry=REGISTRY,
)

INCIDENTS_TOTAL = Counter(
    "unilog_incidents_total",
    "Total security and operational incidents correlated",
    ["severity", "category"],
    registry=REGISTRY,
)

# 4. AI Diagnostics SRE Subsystem
AI_REQUESTS_TOTAL = Counter(
    "unilog_ai_requests_total",
    "Total AI explanation requests",
    registry=REGISTRY,
)

AI_FALLBACK_INVOCATIONS_TOTAL = Counter(
    "unilog_ai_fallback_invocations_total",
    "Total graceful AI fallback invocations",
    registry=REGISTRY,
)

AI_LATENCY_SECONDS = Histogram(
    "unilog_ai_latency_seconds",
    "AI response latency distribution in seconds",
    buckets=LATENCY_BUCKETS,
    registry=REGISTRY,
)

# 5. Background Worker Task Engine & WebSockets
BACKGROUND_TASKS = Gauge(
    "unilog_background_tasks",
    "Background worker task count by status",
    ["status"],
    registry=REGISTRY,
)

TASK_QUEUE_DEPTH = Gauge(
    "unilog_task_queue_depth",
    "Active background task queue depth",
    registry=REGISTRY,
)

TASK_DURATION_SECONDS = Histogram(
    "unilog_task_duration_seconds",
    "Background task execution duration in seconds",
    ["task_type"],
    buckets=LATENCY_BUCKETS,
    registry=REGISTRY,
)

ACTIVE_WEBSOCKETS = Gauge(
    "unilog_active_websockets",
    "Current active live monitoring WebSocket connections",
    registry=REGISTRY,
)

WEBSOCKET_MESSAGES_TOTAL = Counter(
    "unilog_websocket_messages_total",
    "Total streamed WebSocket log records",
    registry=REGISTRY,
)

WEBSOCKET_DISCONNECTS_TOTAL = Counter(
    "unilog_websocket_disconnects_total",
    "Total WebSocket client disconnections",
    registry=REGISTRY,
)

WEBSOCKET_RATE_RECORDS_PER_SECOND = Gauge(
    "unilog_websocket_rate_records_per_second",
    "Current live stream record throughput rate",
    registry=REGISTRY,
)

# 6. System Health Matrix
SYSTEM_HEALTH_SCORE = Gauge(
    "unilog_system_health_score",
    "Real-time system health matrix scores (0-100)",
    ["dimension"],
    registry=REGISTRY,
)
