"""Security indicators analyzer."""

import re
import urllib.parse
from typing import Any, Dict, Mapping, Sequence
from unilog.analytics.base import AnalyzerContext, BaseAnalyzer
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import (
    SecurityMetrics,
    BruteForceMetrics,
    EnumerationMetrics,
    BotMetrics,
    ScannerMetrics,
    InjectionMetrics,
    Session
)


@register_analyzer("security", version="1.0", dependencies=["session"], produces=SecurityMetrics)
class SecurityAnalyzer(BaseAnalyzer):
    """Computes aggregate security signatures and threat profiles from logs."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> SecurityMetrics:
        # Retrieve computed sessions from shared parser_metadata cache
        sessions: list[Session] = context.parser_metadata.get("reconstructed_sessions", [])

        # 1. Brute Force variables
        failed_logins_per_ip: Dict[str, int] = {}
        total_logins = 0
        total_failed_logins = 0
        lockout_candidates = []

        # 2. Enumeration variables
        distinct_endpoints_per_ip: Dict[str, set] = {}
        total_requests = len(records)
        total_404 = 0

        # 3. Bot metrics variables
        missing_user_agent_count = 0
        headless_fingerprints_count = 0
        # 4. Scanner probing variables
        scanned_ips: Dict[str, int] = {}
        scanner_hits_count = 0

        # Probe paths regex patterns
        scanner_patterns = [
            r"\.env",
            r"\.git",
            r"wp-admin",
            r"wp-login\.php",
            r"config\.php",
            r"backup\.zip",
            r"phpinfo",
            r"cgi-bin",
            r"setup\.php",
            r"admin/config"
        ]
        scanner_rx = re.compile("|".join(scanner_patterns), re.IGNORECASE)

        # 5. Injection variables
        sql_injection_count = 0
        xss_injection_count = 0
        path_traversal_count = 0
        rce_cmd_injection_count = 0

        # Injection signatures
        sqli_rx = re.compile(r"union\s+select|union\s+all\s+select|or\s+1\s*=\s*1|or\s+'1'\s*=\s*'1'", re.IGNORECASE)
        xss_rx = re.compile(r"<script|javascript:|onerror\s*=|onload\s*=", re.IGNORECASE)
        traversal_rx = re.compile(r"\.\./|\.\.\\|%2e%2e", re.IGNORECASE)
        rce_rx = re.compile(r"\$\{jndi:|cmd\s*=|powershell|base64", re.IGNORECASE)

        # Loop through raw records to compute baseline counts
        for r in records:
            if "_parse_error" in r:
                continue

            ip = r.get("source_ip") or r.get("client_ip") or r.get("ip") or r.get("remote_addr") or "-"
            path = r.get("path") or ""
            _ = str(r.get("method") or "GET").upper()
            status_code = int(r.get("status_code") or 200)
            user_agent = r.get("user_agent") or ""

            # Check 404 Status
            if status_code == 404:
                total_404 += 1

            # Count distinct endpoints
            if ip != "-":
                distinct_endpoints_per_ip.setdefault(ip, set()).add(path)

            # Check Scanner probe hits
            if scanner_rx.search(path):
                scanned_ips[ip] = scanned_ips.get(ip, 0) + 1
                scanner_hits_count += 1

            # Check User Agent anomalies
            if not user_agent or user_agent == "-":
                missing_user_agent_count += 1
            else:
                ua_lower = user_agent.lower()
                if any(f in ua_lower for f in ["headlesschrome", "phantomjs", "puppeteer", "selenium", "playwright"]):
                    headless_fingerprints_count += 1

            # Check Code Injections (Path + Query Params + Raw)
            raw_payload = f"{path} {r.get('query_string') or ''} {r.get('raw') or ''}"
            combined_payload = urllib.parse.unquote(raw_payload)
            if sqli_rx.search(combined_payload):
                sql_injection_count += 1
            if xss_rx.search(combined_payload):
                xss_injection_count += 1
            if traversal_rx.search(combined_payload):
                path_traversal_count += 1
            if rce_rx.search(combined_payload):
                rce_cmd_injection_count += 1

        # Process session aggregations (to evaluate brute force and bot rates per session)
        for s in sessions:
            if s.client_ip == "-":
                continue

            failed_logins = 0
            for req in s.requests:
                is_login_path = any(x in req.path.lower() for x in ["login", "auth", "signin"])
                if req.method == "POST" and is_login_path:
                    total_logins += 1

                is_fail = req.status_code in [401, 403] or (req.method == "POST" and is_login_path and req.status_code >= 400)
                if is_fail:
                    failed_logins += 1
                    total_failed_logins += 1

            if failed_logins > 0:
                failed_logins_per_ip[s.client_ip] = failed_logins_per_ip.get(s.client_ip, 0) + failed_logins
                if failed_logins > 40:
                    lockout_candidates.append(s.client_ip)

        # Format distinct endpoints count
        formatted_endpoints = {ip: len(paths) for ip, paths in distinct_endpoints_per_ip.items()}

        # Compute requests per minute per IP using timestamps
        requests_per_minute: Dict[str, float] = {}
        for s in sessions:
            if s.client_ip == "-" or s.request_count == 0:
                continue
            duration_min = max(s.duration_seconds / 60.0, 0.05) # clamp min to 3s
            rpm = s.request_count / duration_min
            if rpm > requests_per_minute.get(s.client_ip, 0.0):
                requests_per_minute[s.client_ip] = round(rpm, 2)

        # Build sub-metrics
        unique_lockout_candidates = list(set(lockout_candidates))
        brute_force = BruteForceMetrics(
            failed_logins_per_ip=failed_logins_per_ip,
            failure_ratio=round((total_failed_logins / total_logins * 100.0) if total_logins > 0 else 0.0, 2),
            lockout_candidates=unique_lockout_candidates,
            lockout_candidates_count=len(unique_lockout_candidates)
        )

        enumeration = EnumerationMetrics(
            distinct_endpoints_per_ip=formatted_endpoints,
            error_404_ratio=round((total_404 / total_requests * 100.0) if total_requests > 0 else 0.0, 2)
        )

        bot_metrics = BotMetrics(
            requests_per_minute=requests_per_minute,
            missing_user_agent_count=missing_user_agent_count,
            headless_fingerprints_count=headless_fingerprints_count
        )

        scanner_metrics = ScannerMetrics(
            scanned_ips=scanned_ips,
            scanner_hits_count=scanner_hits_count
        )

        injection_metrics = InjectionMetrics(
            sql_injection_count=sql_injection_count,
            xss_injection_count=xss_injection_count,
            path_traversal_count=path_traversal_count,
            rce_cmd_injection_count=rce_cmd_injection_count
        )

        return SecurityMetrics(
            brute_force=brute_force,
            enumeration=enumeration,
            bot_metrics=bot_metrics,
            scanner_metrics=scanner_metrics,
            injection_metrics=injection_metrics
        )
