import os
import json
import logging
import httpx
from fastapi import APIRouter, Request
from api.dependencies.rate_limiter import limiter
from api.schemas.ai import AIExplainRequest, AIExplainResponse

logger = logging.getLogger("unilog-api")
router = APIRouter(tags=["AI"])

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def generate_fallback_mock(req: AIExplainRequest) -> dict:
    """Generate high-fidelity local deterministic mock analysis if Gemini API key is missing."""
    metrics = req.metrics

    has_errors = metrics.get("error_metrics", {}).get("error_rate", 0.0) > 0.05
    has_high_latency = metrics.get("traffic_metrics", {}).get("avg_latency_ms", 0.0) > 400.0
    
    # 1. Check for Security Injections
    security_metrics = metrics.get("security_metrics") or metrics.get("security", {})

    injection = security_metrics.get("injection_metrics", {})
    has_sqli = injection.get("sql_injection_count", 0) > 0
    
    # 2. Check for Scanner/Probing
    scanner = security_metrics.get("scanner_metrics", {})
    has_scanner = scanner.get("probe_requests_count", 0) > 0 or scanner.get("scanner_user_agents_count", 0) > 0
    
    # 3. Check for Auth Bruteforce
    auth = security_metrics.get("auth_metrics", {})
    has_auth_fail = auth.get("failed_login_count", 0) > 0

    remediations = []

    
    if has_sqli:
        summary = "CRITICAL: SQL Injection Attempts Detected"
        explanation = (
            "### Security Root-Cause Analysis\n\n"
            "We detected active SQL Injection signatures in incoming request payloads. "
            "An attacker is attempting to exploit potential input sanitization vulnerabilities "
            "to extract database contents or bypass authentication gates."
        )
        remediations.append({
            "title": "Enforce Input Sanitization / WAF Rules",
            "description": "Reject requests containing common SQL injection signatures at the Nginx reverse proxy level.",
            "code": (
                "# Nginx Block SQLi Rule\n"
                "if ($query_string ~* \"union.*select|or.*1=1\") {\n"
                "    return 403;\n"
                "}"
            ),
            "language": "nginx"
        })
    elif has_auth_fail:
        summary = "HIGH: Brute-Force Login Attacks Detected"
        explanation = (
            "### Authentication Security Incident\n\n"
            "Our security analyzer identified clients with elevated failed login attempt ratios. "
            "This behavior is highly indicative of credential stuffing or dictionary attacks targetting login endpoints."
        )
        remediations.append({
            "title": "Enable Fail2Ban / IP Rate Limiting",
            "description": "Limit POST requests to authentication endpoints to prevent brute-force attacks.",
            "code": (
                "# Limit login endpoints to 5 requests per minute\n"
                "limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;\n\n"
                "location /api/v1/auth/login {\n"
                "    limit_req zone=login_limit burst=3 nodelay;\n"
                "    proxy_pass http://backend;\n"
                "}"
            ),
            "language": "nginx"
        })
    elif has_scanner:
        summary = "MEDIUM: Active Vulnerability Scans Identified"
        explanation = (
            "### Network Reconnaissance Probes\n\n"
            "Multiple client IPs are attempting to access sensitive administrative paths "
            "like `.env` or `wp-admin` to discover system vulnerabilities or environment secrets."
        )
        remediations.append({
            "title": "Block Scanner / Prober IPs",
            "description": "Configure block rules for scanner source IPs at your firewall level.",
            "code": (
                "# Block malicious scanner IPs\n"
                "iptables -A INPUT -s 192.168.0.44 -j DROP\n"
                "iptables -A INPUT -s 192.168.0.85 -j DROP"
            ),
            "language": "bash"
        })
    elif has_errors:
        summary = "WARN: High Error Rates on Endpoints"
        explanation = (
            "### System Reliability Degradation\n\n"
            "The system is experiencing an elevated HTTP 5xx error rate. "
            "This suggests an upstream service outage or a database deadlock causing server failures."
        )
        remediations.append({
            "title": "Investigate Database Latency",
            "description": "Verify DB connection pool status and lock contentions.",
            "code": (
                "-- Find long running database queries\n"
                "SELECT pid, now() - pg_stat_activity.query_start AS duration, query\n"
                "FROM pg_stat_activity\n"
                "WHERE state != 'idle' AND now() - pg_stat_activity.query_start > interval '5 seconds'\n"
                "ORDER BY duration DESC;"
            ),
            "language": "sql"
        })
    elif has_high_latency:
        summary = "INFO: Performance Latency Warning"

        explanation = (
            "### API Latency Diagnostics\n\n"
            "Several endpoints are exhibiting response latencies exceeding performance thresholds. "
            "This might be caused by lack of indexing or large synchronous payloads."
        )
        remediations.append({
            "title": "Index Endpoint Query Parameters",
            "description": "Add database indices on columns used to filter or join on the slow endpoints.",
            "code": "CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);",
            "language": "sql"
        })
    else:
        summary = "HEALTHY: No Operational Anomalies Detected"
        explanation = (
            "### System Operational Status\n\n"
            "All metrics are within acceptable parameters. System latencies are minimal, "
            "error rates are below threshold, and no malicious signatures were detected."
        )
        remediations.append({
            "title": "Enable Continuous Monitoring",
            "description": "Ensure log pipelines keep running and active rules stay enabled.",
            "code": "unilog stats realistic_logs.log",
            "language": "bash"
        })

    return {
        "summary": summary,
        "explanation": explanation,
        "remediations": remediations
    }

@router.post(
    "/ai/explain",
    response_model=AIExplainResponse,
    summary="Generate AI Explanation & Remediation",
    description="Analyze metrics and insights, returning an AI-generated explanation and remediation plan using Gemini."
)
@limiter.limit("50/minute")
async def explain_log_analysis(request: Request, req: AIExplainRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("GEMINI_API_KEY not found. Returning local mock engine analysis.")
        return generate_fallback_mock(req)

    # Format the prompt with metrics and insights summaries
    prompt = (
        "Analyze the following system metrics and rule engine insights, "
        "and provide a structured operational report. Respond EXACTLY matching the requested JSON schema.\n\n"
        f"Metrics:\n{json.dumps(req.metrics, indent=2)}\n\n"
        f"Rule Insights:\n{json.dumps([ins.model_dump() for ins in req.insights], indent=2)}"
    )

    schema = {
        "type": "OBJECT",
        "properties": {
            "summary": {
                "type": "STRING",
                "description": "A concise high-level overview of the log status (e.g. 'CRITICAL: SQL Injection Attempts Detected')"
            },
            "explanation": {
                "type": "STRING",
                "description": "Markdown-formatted detailed analysis and root-cause explanation of the events."
            },
            "remediations": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": { "type": "STRING", "description": "Title of the fix" },
                        "description": { "type": "STRING", "description": "What this fix does" },
                        "code": { "type": "STRING", "description": "Code snippet, configuration rule, or shell commands" },
                        "language": { "type": "STRING", "description": "Language of code (nginx, sql, bash, etc)" }
                    },
                    "required": ["title", "description", "code", "language"]
                },
                "description": "Actionable fixes with code/config blocks"
            }
        },
        "required": ["summary", "explanation", "remediations"]
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are unilog's AI SRE Assistant. "
                            "Analyze the system state and respond with JSON matching the schema.\n\n"
                            + prompt
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            if resp.status_code != 200:
                logger.error(f"Gemini API returned error {resp.status_code}: {resp.text}")
                # Fall back to local mock to keep system operational (robust fallback)
                return generate_fallback_mock(req)
                
            result_json = resp.json()
            # Extract generated text
            candidate_text = result_json["candidates"][0]["content"]["parts"][0]["text"]
            parsed_response = json.loads(candidate_text)
            return parsed_response

    except Exception as e:
        logger.error(f"Exception during Gemini API request: {e}", exc_info=True)
        # Fall back to local mock to keep system operational
        return generate_fallback_mock(req)
