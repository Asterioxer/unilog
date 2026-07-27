import threading
from fastapi.testclient import TestClient
from api.app import app
from api.observability import recorder, generate_prometheus_metrics
from api.observability.middleware import normalize_endpoint_path

client = TestClient(app)

def test_metrics_endpoint():
    """Verify GET /metrics returns 200 OK with Prometheus exposition content."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    
    text = response.text
    assert "# HELP unilog_requests_total" in text
    assert "# HELP unilog_process_uptime_seconds" in text
    assert "# HELP unilog_logs_processed_total" in text
    assert "# HELP unilog_parser_latency_seconds" in text
    assert "# HELP unilog_rules_triggered_total" in text
    assert "# HELP unilog_incidents_total" in text
    assert "# HELP unilog_system_health_score" in text
    assert "# HELP unilog_active_websockets" in text

def test_path_normalization():
    """Verify dynamic parametric URL paths are normalized to prevent label cardinality explosion."""
    assert normalize_endpoint_path("/api/v1/tasks/task-abc-123") == "/api/v1/tasks/{task_id}"
    assert normalize_endpoint_path("/api/v1/analyze") == "/api/v1/analyze"
    assert normalize_endpoint_path("/health") == "/health"

def test_metric_recorders():
    """Verify recorder helper methods update metrics cleanly."""
    recorder.record_log_parsing("nginx", 25, 0.045)
    recorder.record_triggered_rule("sec-sqli-01", "high", "security")
    recorder.record_incident("critical", "security")
    recorder.update_health_scores(overall=95.0, security=90.0, reliability=100.0)

    metrics_text = generate_prometheus_metrics().decode("utf-8")
    assert 'unilog_logs_processed_total{format="nginx"}' in metrics_text
    assert 'unilog_rules_triggered_total{category="security",rule_id="sec-sqli-01",severity="high"}' in metrics_text
    assert 'unilog_incidents_total{category="security",severity="critical"}' in metrics_text
    assert 'unilog_system_health_score{dimension="overall"} 95.0' in metrics_text
    assert 'unilog_system_health_score{dimension="security"} 90.0' in metrics_text

def test_high_volume_concurrent_scraping():
    """Verify 100 parallel threads updating metrics and scraping exposition concurrently."""
    errors = []

    def worker(thread_idx):
        try:
            for _ in range(100):
                recorder.record_log_parsing("apache", 1, 0.005)
                recorder.record_triggered_rule(f"rule-{thread_idx % 5}", "medium", "traffic")
                if thread_idx % 10 == 0:
                    generate_prometheus_metrics()
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent scrape errors encountered: {errors}"
    final_exposition = generate_prometheus_metrics().decode("utf-8")
    assert "unilog_logs_processed_total" in final_exposition
