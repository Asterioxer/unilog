"""System health score matrix calculator."""

from typing import Sequence, Tuple
from unilog.analytics.schemas import (
    HealthSubScore,
    Incident,
    Insight,
    MetricsBundle,
    SystemHealthScore
)


class HealthCalculator:
    """Calculates multi-dimensional environment system health scores (0-100)."""

    def calculate(
        self,
        metrics: MetricsBundle,
        insights: Sequence[Insight],
        incidents: Sequence[Incident]
    ) -> SystemHealthScore:
        """Compute overall system health and sub-domain scores."""
        sec_score, sec_status, sec_sum = self._compute_security_health(metrics, insights, incidents)
        rel_score, rel_status, rel_sum = self._compute_reliability_health(metrics, insights, incidents)
        perf_score, perf_status, perf_sum = self._compute_performance_health(metrics, insights, incidents)
        traf_score, traf_status, traf_sum = self._compute_traffic_health(metrics, insights, incidents)

        # Overall score is heavily weighted by the minimum sub-score to ensure critical security/reliability issues pull down the main indicator
        weighted_avg = int(sec_score * 0.35 + rel_score * 0.30 + perf_score * 0.20 + traf_score * 0.15)
        overall_score = max(0, min(100, min(weighted_avg, min(sec_score, rel_score))))

        if overall_score >= 85:
            overall_status = "HEALTHY"
        elif overall_score >= 60:
            overall_status = "WARNING"
        else:
            overall_status = "CRITICAL"

        return SystemHealthScore(
            overall_score=overall_score,
            status=overall_status,
            security=HealthSubScore(score=sec_score, status=sec_status, summary=sec_sum),
            reliability=HealthSubScore(score=rel_score, status=rel_status, summary=rel_sum),
            performance=HealthSubScore(score=perf_score, status=perf_status, summary=perf_sum),
            traffic=HealthSubScore(score=traf_score, status=traf_status, summary=traf_sum)
        )

    def _compute_security_health(
        self,
        metrics: MetricsBundle,
        insights: Sequence[Insight],
        incidents: Sequence[Incident]
    ) -> Tuple[int, str, str]:
        score = 100
        sec_incidents = [inc for inc in incidents if inc.threat_profile is not None or "Security" in inc.title or "Attack" in inc.title]

        for inc in sec_incidents:
            if inc.severity == "CRITICAL":
                score -= 40
            elif inc.severity == "HIGH":
                score -= 25
            elif inc.severity == "MEDIUM":
                score -= 15

        sec_insights = [i for i in insights if i.category == "security"]
        score -= len(sec_insights) * 5

        score = max(0, min(100, score))
        if score >= 85:
            status, summary = "HEALTHY", "No active security threats or scanner probes detected."
        elif score >= 60:
            status, summary = "WARNING", f"Security probes or automated bot traffic detected ({len(sec_incidents)} incidents)."
        else:
            status, summary = "CRITICAL", f"Active high-severity security threat campaign underway ({len(sec_incidents)} incidents)."

        return score, status, summary

    def _compute_reliability_health(
        self,
        metrics: MetricsBundle,
        insights: Sequence[Insight],
        incidents: Sequence[Incident]
    ) -> Tuple[int, str, str]:
        score = 100
        err_metrics = getattr(metrics, "error", None)
        status_metrics = getattr(metrics, "status", None)

        if status_metrics and status_metrics.http_5xx_rate is not None:
            rate = status_metrics.http_5xx_rate
            if rate > 0.05:
                score -= 40
            elif rate > 0.02:
                score -= 20

        if err_metrics:
            if err_metrics.error_ratio > 0.10:
                score -= 30
            elif err_metrics.error_ratio > 0.05:
                score -= 15

        rel_insights = [i for i in insights if i.category == "reliability"]
        score -= len(rel_insights) * 10

        score = max(0, min(100, score))
        if score >= 85:
            status, summary = "HEALTHY", "Optimal service reliability; error ratios within nominal thresholds."
        elif score >= 60:
            status, summary = "WARNING", "Elevated HTTP error ratios or 5xx server responses observed."
        else:
            status, summary = "CRITICAL", "Severe service disruption or high 5xx error rate breach."

        return score, status, summary

    def _compute_performance_health(
        self,
        metrics: MetricsBundle,
        insights: Sequence[Insight],
        incidents: Sequence[Incident]
    ) -> Tuple[int, str, str]:
        score = 100
        lat_metrics = getattr(metrics, "latency", None)

        if lat_metrics:
            if lat_metrics.p99_ms and lat_metrics.p99_ms > 1000:
                score -= 40
            elif lat_metrics.p99_ms and lat_metrics.p99_ms > 500:
                score -= 25

            if lat_metrics.p95_ms and lat_metrics.p95_ms > 300:
                score -= 15

        perf_insights = [i for i in insights if i.category == "performance"]
        score -= len(perf_insights) * 10

        score = max(0, min(100, score))
        if score >= 85:
            status, summary = "HEALTHY", "Response latency SLAs met (P95 < 300ms, P99 < 500ms)."
        elif score >= 60:
            status, summary = "WARNING", "Response latency degradation observed on key routes."
        else:
            status, summary = "CRITICAL", "High latency breach impacting user experience."

        return score, status, summary

    def _compute_traffic_health(
        self,
        metrics: MetricsBundle,
        insights: Sequence[Insight],
        incidents: Sequence[Incident]
    ) -> Tuple[int, str, str]:
        score = 100
        burst_metrics = getattr(metrics, "traffic_burst", None)

        if burst_metrics and burst_metrics.is_bursting:
            score -= 20

        traf_insights = [i for i in insights if i.category == "traffic"]
        score -= len(traf_insights) * 10

        score = max(0, min(100, score))
        if score >= 85:
            status, summary = "HEALTHY", "Traffic throughput and request distributions stable."
        elif score >= 60:
            status, summary = "WARNING", "Traffic burst anomaly or bandwidth spike detected."
        else:
            status, summary = "CRITICAL", "Extreme traffic volume or endpoint overload detected."

        return score, status, summary
