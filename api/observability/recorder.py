import time
from api.observability.metrics import (
    LOGS_PROCESSED_TOTAL,
    PARSER_ERRORS_TOTAL,
    PARSER_LATENCY_SECONDS,
    RULES_TRIGGERED_TOTAL,
    INCIDENTS_TOTAL,
    AI_REQUESTS_TOTAL,
    AI_FALLBACK_INVOCATIONS_TOTAL,
    AI_LATENCY_SECONDS,
    BACKGROUND_TASKS,
    TASK_QUEUE_DEPTH,
    TASK_DURATION_SECONDS,
    ACTIVE_WEBSOCKETS,
    WEBSOCKET_MESSAGES_TOTAL,
    WEBSOCKET_DISCONNECTS_TOTAL,
    WEBSOCKET_RATE_RECORDS_PER_SECOND,
    SYSTEM_HEALTH_SCORE,
    PROCESS_UPTIME,
    START_TIME,
)

class TelemetryRecorder:
    """High-level thread-safe recorder for unilog operational and intelligence telemetry."""

    def update_uptime(self) -> None:
        """Update process uptime gauge."""
        PROCESS_UPTIME.set(time.time() - START_TIME)

    def record_log_parsing(
        self, format_name: str, record_count: int, duration_seconds: float, is_error: bool = False
    ) -> None:
        fmt = (format_name or "auto").lower()
        if is_error:
            PARSER_ERRORS_TOTAL.labels(format=fmt).inc()
        else:
            LOGS_PROCESSED_TOTAL.labels(format=fmt).inc(record_count)
            PARSER_LATENCY_SECONDS.labels(format=fmt).observe(max(0.0, duration_seconds))

    def record_triggered_rule(
        self, rule_id: str, severity: str, category: str, count: int = 1
    ) -> None:
        RULES_TRIGGERED_TOTAL.labels(
            rule_id=rule_id or "unknown",
            severity=(severity or "info").lower(),
            category=(category or "general").lower(),
        ).inc(count)

    def record_incident(self, severity: str, category: str, count: int = 1) -> None:
        INCIDENTS_TOTAL.labels(
            severity=(severity or "medium").lower(),
            category=(category or "uncategorized").lower(),
        ).inc(count)

    def update_health_scores(
        self,
        overall: float = 100.0,
        security: float = 100.0,
        reliability: float = 100.0,
        performance: float = 100.0,
        traffic: float = 100.0,
    ) -> None:
        SYSTEM_HEALTH_SCORE.labels(dimension="overall").set(overall)
        SYSTEM_HEALTH_SCORE.labels(dimension="security").set(security)
        SYSTEM_HEALTH_SCORE.labels(dimension="reliability").set(reliability)
        SYSTEM_HEALTH_SCORE.labels(dimension="performance").set(performance)
        SYSTEM_HEALTH_SCORE.labels(dimension="traffic").set(traffic)

    def record_ai_request(self, duration_seconds: float, fallback_used: bool = False) -> None:
        AI_REQUESTS_TOTAL.inc()
        if fallback_used:
            AI_FALLBACK_INVOCATIONS_TOTAL.inc()
        AI_LATENCY_SECONDS.observe(max(0.0, duration_seconds))

    def record_websocket_connection(self, delta: int = 1) -> None:
        if delta > 0:
            ACTIVE_WEBSOCKETS.inc(delta)
        elif delta < 0:
            ACTIVE_WEBSOCKETS.dec(abs(delta))

    def record_websocket_stream(self, messages_count: int, rate_per_second: float = 0.0) -> None:
        WEBSOCKET_MESSAGES_TOTAL.inc(messages_count)
        if rate_per_second >= 0.0:
            WEBSOCKET_RATE_RECORDS_PER_SECOND.set(rate_per_second)

    def record_websocket_disconnect(self) -> None:
        WEBSOCKET_DISCONNECTS_TOTAL.inc()

    def record_task_metrics(self, task_type: str, duration_seconds: float, status: str = "completed") -> None:
        TASK_DURATION_SECONDS.labels(task_type=task_type or "general").observe(max(0.0, duration_seconds))

    def update_task_queue(
        self, depth: int = 0, running: int = 0, completed: int = 0, failed: int = 0
    ) -> None:
        TASK_QUEUE_DEPTH.set(max(0, depth))
        BACKGROUND_TASKS.labels(status="running").set(max(0, running))
        BACKGROUND_TASKS.labels(status="completed").set(max(0, completed))
        BACKGROUND_TASKS.labels(status="failed").set(max(0, failed))

recorder = TelemetryRecorder()
