"""Incident correlator for aggregating related insights into incident objects."""

import hashlib
from datetime import datetime, timezone
from typing import Any, List, Mapping, Optional, Sequence

from unilog.analytics.incidents.timeline import TimelineBuilder
from unilog.analytics.schemas import (
    Incident,
    Insight,
    MetricsBundle,
    ThreatProfile
)


class IncidentCorrelator:
    """Correlates co-occurring insights into consolidated incident objects."""

    def __init__(self) -> None:
        self._timeline_builder = TimelineBuilder()

    def correlate(
        self,
        insights: Sequence[Insight],
        metrics: MetricsBundle,
        records: Optional[Sequence[Mapping[str, Any]]] = None
    ) -> List[Incident]:
        """Group related insights into top-level Incidents."""
        if not insights:
            return []

        rec_list = list(records) if records else []

        # Categorize insights by operational domain
        sec_insights = [i for i in insights if i.category == "security"]
        perf_insights = [i for i in insights if i.category == "performance"]
        traffic_insights = [i for i in insights if i.category == "traffic"]
        rel_insights = [i for i in insights if i.category == "reliability"]

        incidents: List[Incident] = []

        # 1. Correlate Security Incident (Scanner + Bot + Enumeration + Injection + Brute Force)
        if sec_insights or (traffic_insights and any("burst" in i.id for i in traffic_insights)):
            sec_inc = self._build_security_incident(sec_insights, traffic_insights, metrics, rec_list)
            if sec_inc:
                incidents.append(sec_inc)

        # 2. Correlate Performance & Reliability Incident
        if perf_insights or rel_insights:
            perf_inc = self._build_performance_incident(perf_insights, rel_insights, metrics, rec_list)
            if perf_inc:
                incidents.append(perf_inc)

        return incidents

    def _build_security_incident(
        self,
        sec_insights: List[Insight],
        traffic_insights: List[Insight],
        metrics: MetricsBundle,
        records: List[Mapping[str, Any]]
    ) -> Optional[Incident]:
        combined_insights = sec_insights + [i for i in traffic_insights if "burst" in i.id]
        if not combined_insights:
            return None

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y%m%d-%H%M%S")

        # Deterministic Incident ID hash
        hash_input = "".join(sorted([i.id for i in combined_insights]))
        hash_hex = hashlib.md5(hash_input.encode("utf-8")).hexdigest()[:4].upper()
        incident_id = f"INC-{date_str}-{hash_hex}"

        # Determine highest severity
        severities = [i.severity for i in combined_insights]
        if "critical" in severities:
            severity = "CRITICAL"
        elif "high" in severities:
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        # Gather affected IPs, suspected tools, capabilities, and target endpoints
        affected_ips: set[str] = set()
        suspected_tools: set[str] = set()
        capabilities: set[str] = set()
        observed_targets: set[str] = set()
        evidence_checkpoints: List[str] = []

        # Inspect metrics for threat details
        sec_metrics = getattr(metrics, "security", None)
        if sec_metrics:
            # Bot tools
            if sec_metrics.bot_metrics and sec_metrics.bot_metrics.headless_fingerprints_count > 0:
                capabilities.add("Automated Browser Emulation")
                evidence_checkpoints.append("[+] Headless browser fingerprint footprint detected")

            # Scanner probing
            if sec_metrics.scanner_metrics:
                for ip in sec_metrics.scanner_metrics.scanned_ips:
                    affected_ips.add(ip)
                if sec_metrics.scanner_metrics.scanner_hits_count > 0:
                    capabilities.add("Admin & Sensitive File Discovery")
                    evidence_checkpoints.append("[+] Sensitive probe paths (.env, wp-admin, config) accessed")

            # Enumeration
            if sec_metrics.enumeration:
                for ip in sec_metrics.enumeration.distinct_endpoints_per_ip:
                    affected_ips.add(ip)
                if sec_metrics.enumeration.error_404_ratio > 0:
                    capabilities.add("Endpoint Directory Enumeration")
                    evidence_checkpoints.append(f"[+] Abnormally high 404 response ratio ({sec_metrics.enumeration.error_404_ratio * 100:.1f}%)")

            # Brute force
            if sec_metrics.brute_force and sec_metrics.brute_force.failed_logins_per_ip:
                for ip in sec_metrics.brute_force.lockout_candidates:
                    affected_ips.add(ip)
                capabilities.add("Credential Stuffing / Brute Force")
                evidence_checkpoints.append(f"[+] Multiple failed authentication attempts ({len(sec_metrics.brute_force.failed_logins_per_ip)} source IPs)")

        # Inspect raw log records for specific tool User-Agents and target paths
        for r in records:
            ip = r.get("source_ip") or r.get("ip")
            if ip:
                affected_ips.add(str(ip))

            ua = r.get("user_agent", "")
            if "Nikto" in ua:
                suspected_tools.add("Nikto")
                evidence_checkpoints.append("[+] Known security scanner User-Agent (Nikto)")
            if "Playwright" in ua or "Headless" in ua:
                suspected_tools.add("Playwright (headless)")
            if "Go-http-client" in ua:
                suspected_tools.add("Go-http-client")
            if "curl" in ua.lower():
                suspected_tools.add("curl")

            path = r.get("path", "")
            if path in ["/wp-admin", "/.env", "/.git", "/api/v1/auth/login", "/config.php", "backup.zip"]:
                observed_targets.add(path)

        # Deduplicate evidence checkpoints preserving order
        unique_evidence = list(dict.fromkeys(evidence_checkpoints))
        if not unique_evidence:
            unique_evidence = [f"[+] {len(combined_insights)} correlated security rule alerts co-occurring"]


        # Calculate evidence-based confidence
        base_confidence = 0.70 + (min(len(unique_evidence), 5) * 0.05)
        confidence = min(0.99, round(base_confidence, 2))

        # Title determination
        if "Credential Stuffing / Brute Force" in capabilities:
            title = "Credential Stuffing & Authentication Attack Campaign"
        elif "Admin & Sensitive File Discovery" in capabilities:
            title = "Automated Reconnaissance & Probe Campaign"
        elif "Automated Browser Emulation" in capabilities:
            title = "Automated Bot Threat Campaign"
        else:
            title = "Security Anomaly & Threat Incident"

        # Actionable recommendations
        recommendations = [
            f"Block offending IP address(es): {', '.join(sorted(list(affected_ips))[:3])}" if affected_ips else "Enforce WAF IP blocking rules",
            "Enable strict rate-limiting on authentication and API probe endpoints",
            "Inspect web server access logs for unauthorized file access or data leakage",
            "Review WAF security rule thresholds and update blocklist"
        ]

        threat_profile = ThreatProfile(
            suspected_tools=sorted(list(suspected_tools)) if suspected_tools else ["Automated Script / Bot"],
            capabilities=sorted(list(capabilities)) if capabilities else ["Web Probing"],
            observed_targets=sorted(list(observed_targets)) if observed_targets else ["General Web Endpoints"],
            risk_level=severity
        )

        timeline = self._timeline_builder.build_timeline(combined_insights, records)

        return Incident(
            incident_id=incident_id,
            title=title,
            severity=severity,
            confidence=confidence,
            confidence_evidence=unique_evidence,
            affected_ips=sorted(list(affected_ips)),
            timeline=timeline,
            threat_profile=threat_profile,
            sub_findings=[i.id for i in combined_insights],
            evidence_summary={
                "total_insights_correlated": len(combined_insights),
                "affected_ip_count": len(affected_ips),
                "rule_ids": [i.id for i in combined_insights]
            },
            recommendations=recommendations
        )

    def _build_performance_incident(
        self,
        perf_insights: List[Insight],
        rel_insights: List[Insight],
        metrics: MetricsBundle,
        records: List[Mapping[str, Any]]
    ) -> Optional[Incident]:
        combined_insights = perf_insights + rel_insights
        if not combined_insights:
            return None

        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y%m%d-%H%M%S")

        hash_input = "".join(sorted([i.id for i in combined_insights]))
        hash_hex = hashlib.md5(hash_input.encode("utf-8")).hexdigest()[:4].upper()
        incident_id = f"INC-PERF-{date_str}-{hash_hex}"

        severities = [i.severity for i in combined_insights]
        severity = "CRITICAL" if "critical" in severities else ("HIGH" if "high" in severities else "MEDIUM")

        evidence_checkpoints: List[str] = []
        lat = getattr(metrics, "latency", None)
        if lat is not None and getattr(lat, "p99_ms", None):
            evidence_checkpoints.append(f"[+] High P99 Latency ({lat.p99_ms:.1f}ms)")
        err = getattr(metrics, "error", None)
        if err is not None and getattr(err, "total_errors", 0) > 0:
            evidence_checkpoints.append(f"[+] Elevated error rate ({err.error_ratio * 100:.1f}%)")



        if not evidence_checkpoints:
            evidence_checkpoints = [f"[+] {len(combined_insights)} performance/reliability SLA threshold breaches"]


        timeline = self._timeline_builder.build_timeline(combined_insights, records)

        return Incident(
            incident_id=incident_id,
            title="System Performance & Reliability Degradation",
            severity=severity,
            confidence=0.90,
            confidence_evidence=evidence_checkpoints,
            affected_ips=[],
            timeline=timeline,
            threat_profile=None,
            sub_findings=[i.id for i in combined_insights],
            evidence_summary={"total_insights": len(combined_insights)},
            recommendations=[
                "Inspect backend service logs for slow database queries or upstream API latency",
                "Verify auto-scaling policies and worker thread capacity",
                "Review error rate metrics per endpoint"
            ]
        )
