"""Session metrics analyzer."""

from datetime import datetime
from typing import Any, Dict, List, Mapping, Sequence

from unilog.analytics.base import AnalyzerContext, BaseAnalyzer
from unilog.analytics.registry import register_analyzer
from unilog.analytics.schemas import SessionMetrics, Session, SessionRequest


@register_analyzer("session", version="1.0", produces=SessionMetrics)
class SessionAnalyzer(BaseAnalyzer):
    """Reconstructs user sessions from logs by grouping client IPs and split windows."""

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: AnalyzerContext,
    ) -> SessionMetrics:
        # Group records by client IP address
        ip_groups: Dict[str, List[Mapping[str, Any]]] = {}
        for r in records:
            if "_parse_error" in r:
                continue
            ip = r.get("source_ip") or r.get("client_ip") or r.get("ip") or r.get("remote_addr") or "-"
            ip_groups.setdefault(ip, []).append(r)

        sessions: List[Session] = []
        possible_bot = 0
        credential_stuffing = 0
        endpoint_enumeration = 0

        # Inactivity timeout split threshold (30 minutes)
        timeout_seconds = 1800.0

        for ip, group in ip_groups.items():
            if ip == "-":
                # Do not group anonymous placeholder IPs into a single massive session
                # Treat each as its own individual session
                for idx, r in enumerate(group):
                    ts = r.get("timestamp")
                    if not isinstance(ts, datetime):
                        continue
                    req = SessionRequest(
                        timestamp=ts,
                        method=str(r.get("method") or "GET").upper(),
                        path=str(r.get("path") or "/"),
                        status_code=int(r.get("status_code") or 200),
                        size=int(r.get("size") or r.get("bytes_sent") or 0),
                        journey_stage="Other"
                    )
                    s_id = f"session_anon_{idx}_{datetime.now().microsecond}"
                    sessions.append(Session(
                        session_id=s_id,
                        client_ip="-",
                        start_time=ts,
                        end_time=ts,
                        duration_seconds=0.0,
                        request_count=1,
                        requests=[req],
                        journey=[]
                    ))
                continue

            # Sort IP records chronologically
            valid_group = []
            for r in group:
                ts = r.get("timestamp")
                if isinstance(ts, datetime):
                    valid_group.append((ts, r))
            
            if not valid_group:
                continue

            valid_group.sort(key=lambda x: x[0])

            # Group chronologically sorted records into distinct sessions using timeout threshold
            current_session_reqs: List[SessionRequest] = []
            session_start_time = valid_group[0][0]
            last_time = valid_group[0][0]
            session_index = 0

            for ts, r in valid_group:
                if (ts - last_time).total_seconds() > timeout_seconds:
                    # Flush current session and start a new one
                    if current_session_reqs:
                        s_id = f"session_{ip.replace('.', '_')}_{session_index}"
                        duration = (last_time - session_start_time).total_seconds()
                        sessions.append(Session(
                            session_id=s_id,
                            client_ip=ip,
                            start_time=session_start_time,
                            end_time=last_time,
                            duration_seconds=duration,
                            request_count=len(current_session_reqs),
                            requests=current_session_reqs,
                            journey=[]
                        ))
                        session_index += 1
                    current_session_reqs = []
                    session_start_time = ts

                req = SessionRequest(
                    timestamp=ts,
                    method=str(r.get("method") or "GET").upper(),
                    path=str(r.get("path") or "/"),
                    status_code=int(r.get("status_code") or 200),
                    size=int(r.get("size") or r.get("bytes_sent") or 0),
                    journey_stage="Other"
                )
                current_session_reqs.append(req)
                last_time = ts

            # Flush final session
            if current_session_reqs:
                s_id = f"session_{ip.replace('.', '_')}_{session_index}"
                duration = (last_time - session_start_time).total_seconds()
                sessions.append(Session(
                    session_id=s_id,
                    client_ip=ip,
                    start_time=session_start_time,
                    end_time=last_time,
                    duration_seconds=duration,
                    request_count=len(current_session_reqs),
                    requests=current_session_reqs,
                    journey=[]
                ))

        # Sort sessions by start_time descending for presentation in list
        sessions.sort(key=lambda s: s.start_time, reverse=True)

        # Compute aggregate metrics
        total_sessions = len(sessions)
        if total_sessions > 0:
            total_duration = sum(s.duration_seconds for s in sessions)
            avg_duration = total_duration / total_sessions
            longest_duration = max(s.duration_seconds for s in sessions)
            bounces = sum(1 for s in sessions if s.request_count == 1)
            bounce_rate = (bounces / total_sessions) * 100.0
            
            total_pages = 0
            total_requests = 0
            for s in sessions:
                total_pages += len(set(req.path for req in s.requests))
                total_requests += s.request_count

                # Detect behavioral indicators
                is_bot = False
                if s.request_count > 500:
                    is_bot = True
                elif s.duration_seconds > 10.0 and (s.request_count / (s.duration_seconds / 60.0)) > 100.0:
                    is_bot = True
                if is_bot:
                    possible_bot += 1

                failed_logins = 0
                for req in s.requests:
                    is_login_path = any(x in req.path.lower() for x in ["login", "auth", "signin"])
                    is_fail = req.status_code in [401, 403] or (req.method == "POST" and is_login_path and req.status_code >= 400)
                    if is_fail:
                        failed_logins += 1
                if failed_logins > 40:
                    credential_stuffing += 1

                distinct_endpoints = len(set(req.path for req in s.requests))
                if distinct_endpoints > 100:
                    endpoint_enumeration += 1

            pages_per_session = total_pages / total_sessions
            requests_per_session = total_requests / total_sessions
        else:
            avg_duration = 0.0
            longest_duration = 0.0
            bounce_rate = 0.0
            pages_per_session = 0.0
            requests_per_session = 0.0

        # Save sessions list to context parser_metadata to share with JourneyAnalyzer
        context.parser_metadata["reconstructed_sessions"] = sessions

        return SessionMetrics(
            average_session_duration_seconds=round(avg_duration, 2),
            bounce_rate=round(bounce_rate, 2),
            pages_per_session=round(pages_per_session, 2),
            requests_per_session=round(requests_per_session, 2),
            active_sessions_count=total_sessions,
            longest_session_duration_seconds=round(longest_duration, 2),
            sessions=sessions,
            possible_bot_count=possible_bot,
            credential_stuffing_count=credential_stuffing,
            endpoint_enumeration_count=endpoint_enumeration
        )
