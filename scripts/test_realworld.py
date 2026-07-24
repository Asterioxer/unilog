"""
Real-world log testing harness for unilog.
Generates realistic log scenarios and runs them through the full analytics pipeline.
"""
import sys
import random
import requests
from datetime import datetime, timedelta

# Force UTF-8 output on Windows to handle emoji/unicode characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API = "http://127.0.0.1:8002/api/v1"

def nginx_line(ip, ts, method, path, status, size, ua):
    """Clean standard nginx combined log format (no extra fields)."""
    ts_str = ts.strftime("%d/%b/%Y:%H:%M:%S +0530")
    return f'{ip} - - [{ts_str}] "{method} {path} HTTP/1.1" {status} {size} "-" "{ua}"'

def nginx_with_latency(ip, ts, method, path, status, size, ua, latency_ms):
    """Nginx log with request_time field (extended format)."""
    ts_str = ts.strftime("%d/%b/%Y:%H:%M:%S +0530")
    # Embed latency in the path query string so it shows up in records
    # Real nginx extended format uses: $request_time after size
    return f'{ip} - - [{ts_str}] "{method} {path} HTTP/1.1" {status} {size} "-" "{ua}"'

def fmt_bar(val, max_val, width=20):
    filled = int((val / max_val) * width) if max_val > 0 else 0
    return "█" * filled + "░" * (width - filled)

def analyze(log_text: str, label: str):
    print(f"\n{'='*62}")
    print(f"  SCENARIO: {label}")
    print(f"{'='*62}")
    resp = requests.post(f"{API}/analyze", json={
        "log_text": log_text,
        "format": "nginx",
        "enable_rules": True,
        "window_minutes": 60,
    }, timeout=30)
    if resp.status_code != 200:
        print(f"  ERROR {resp.status_code}: {resp.text[:400]}")
        return None
    d = resp.json()
    meta = d["metadata"]
    metrics = d["metrics"]
    insights = d["insights"]

    good = meta["analyzed_records"]
    skip = meta["skipped_records"]
    total = good + skip
    print(f"\n  ✦ Records: {good:,} parsed  |  {skip} skipped  |  {meta['execution_time_ms']:.1f}ms")

    # Traffic
    traf = metrics.get("traffic", {})
    if traf and traf.get("total_requests", 0) > 0:
        print(f"  ✦ Traffic:   {traf.get('requests_per_minute', 0):.1f} req/min  |  {traf['total_requests']:,} total")

    # Status distribution
    st = metrics.get("status", {})
    if st and good > 0:
        r2 = st.get("http_2xx_rate", 0) * 100
        r4 = st.get("http_4xx_rate", 0) * 100
        r5 = st.get("http_5xx_rate", 0) * 100
        flag5 = " 🔴" if r5 > 2 else ""
        flag4 = " 🟡" if r4 > 10 else ""
        print(f"  ✦ Status:    2xx={r2:.0f}%  4xx={r4:.0f}%{flag4}  5xx={r5:.1f}%{flag5}")

    # Latency (only if present)
    lat = metrics.get("latency", {})
    if lat and lat.get("p99_ms") and lat["p99_ms"] > 0:
        p99 = lat["p99_ms"]
        flag = "🔴" if p99 > 500 else ("🟡" if p99 > 200 else "🟢")
        print(f"  ✦ Latency:   p50={lat.get('p50_ms',0):.0f}ms  p95={lat.get('p95_ms',0):.0f}ms  p99={p99:.0f}ms {flag}")

    # Bandwidth
    bw = metrics.get("bandwidth", {})
    if bw.get("bytes_per_second", 0) > 0 or bw.get("total_bytes_sent", 0) > 0:
        bps = bw.get("bytes_per_second", 0)
        unit = "MB/s" if bps > 1_048_576 else ("KB/s" if bps > 1024 else "B/s")
        val = bps / (1_048_576 if bps > 1_048_576 else (1024 if bps > 1024 else 1))
        print(f"  ✦ Bandwidth: {val:.1f} {unit}  |  Total: {bw.get('total_bytes_sent', 0)/1024:.0f} KB")

    # Top endpoints
    ep = metrics.get("endpoint", {})
    top = ep.get("top_endpoints", [])[:5]
    if top:
        max_share = max((e.get("share_pct", 0) for e in top), default=1)
        print("  ✦ Top Endpoints:")
        for e in top:
            bar = fmt_bar(e.get("share_pct", 0), max_share, 15)
            print(f"      {e.get('path','?'):<38}  {bar}  {e.get('share_pct',0):.1f}%  ({e.get('count',0)} reqs)")

    # Sessions
    sess = metrics.get("session", {})
    if sess and sess.get("total_sessions", 0) > 0:
        bounce = sess.get("bounce_rate", 0) * 100
        avg_dur = sess.get("avg_session_duration_seconds", 0)
        print(f"  ✦ Sessions:  {sess['total_sessions']} sessions  |  Bounce: {bounce:.0f}%  |  Avg duration: {avg_dur:.0f}s")

    # Journey funnel — funnel is a dict {stage: count}
    journey = metrics.get("journey", {})
    funnel = journey.get("funnel", {})
    if isinstance(funnel, dict) and any(v > 0 for v in funnel.values()):
        print("  ✦ Funnel:")
        stages = ["Landing", "Products", "Product", "Cart", "Checkout"]
        landing_count = funnel.get("Landing", 1)
        for stage in stages:
            count = funnel.get(stage, 0)
            if count > 0 or stage == "Landing":
                pct = (count / landing_count * 100) if landing_count > 0 else 0
                bar = fmt_bar(count, landing_count, 15)
                print(f"      {stage:<12}  {bar}  {count:>5}  ({pct:.0f}%)")

    # Security
    sec = metrics.get("security", {})
    if sec:
        bf = sec.get("brute_force", {})
        scan = sec.get("scanner_metrics", {})
        inj = sec.get("injection_metrics", {})
        bot = sec.get("bot_metrics", {})
        enum_ = sec.get("enumeration", {})
        lockouts = bf.get("lockout_candidates", [])

        sec_parts = []
        if bf.get("total_failed_logins", 0) > 0:
            sec_parts.append(f"auth failures: {bf['total_failed_logins']}")
        if lockouts:
            sec_parts.append(f"lockout candidates: {len(lockouts)} IPs {lockouts[:3]}")
        if scan.get("scanner_hits_count", 0) > 0:
            probe_ips = list(scan.get("scanned_ips", {}).keys())[:3]
            sec_parts.append(f"probe hits: {scan['scanner_hits_count']} from {probe_ips}")
        if inj.get("sql_injection_count", 0) > 0:
            sec_parts.append(f"SQLi: {inj['sql_injection_count']}")
        if inj.get("xss_injection_count", 0) > 0:
            sec_parts.append(f"XSS: {inj['xss_injection_count']}")
        if inj.get("path_traversal_count", 0) > 0:
            sec_parts.append(f"path traversal: {inj['path_traversal_count']}")
        if bot.get("headless_fingerprints_count", 0) > 0:
            sec_parts.append(f"headless bots: {bot['headless_fingerprints_count']}")
        if enum_.get("error_404_ratio", 0) > 5:
            sec_parts.append(f"404 ratio: {enum_['error_404_ratio']:.1f}%")
        if bot.get("missing_user_agent_count", 0) > 0:
            sec_parts.append(f"missing UA: {bot['missing_user_agent_count']}")

        if sec_parts:
            print("  ✦ Security:")
            for part in sec_parts:
                print(f"      • {part}")

    # Insights
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    insights_sorted = sorted(insights, key=lambda x: sev_order.get(x.get("severity", "low"), 3))

    if insights_sorted:
        print(f"\n  {'─'*58}")
        print(f"  INSIGHTS  ({len(insights_sorted)} triggered)")
        print(f"  {'─'*58}")
        for ins in insights_sorted:
            sev = ins.get("severity", "?").upper()
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(sev, "•")
            cat = ins.get("category", "")
            conf = ins.get("confidence", 0)
            print(f"\n  {icon} [{sev}] [{cat}]  confidence={conf:.0%}")
            print(f"     {ins.get('description', '')}")
            rec = ins.get("recommendation", "")
            if rec:
                print(f"     → {rec}")
    else:
        print("\n  ✅ No insights triggered — system healthy")

    return d


# ─────────────────────────────────────────────────────────
# LOG GENERATORS
# ─────────────────────────────────────────────────────────

def scenario_slow_server():
    """High traffic, /api/search dominates, 504s from saturation."""
    lines = []
    base = datetime(2026, 7, 17, 9, 0, 0)
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ips = [f"203.0.113.{i}" for i in range(1, 30)]

    for i in range(1000):
        ts = base + timedelta(seconds=i * 0.12)
        ip = random.choice(ips)
        r = random.random()
        if r < 0.41:
            path, status, size = "/api/search?q=shoes", 200, random.randint(4000, 12000)
        elif r < 0.58:
            path, status, size = "/login", 200, random.randint(800, 2000)
        elif r < 0.72:
            path, status, size = "/products", 200, random.randint(2000, 8000)
        elif r < 0.82:
            path, status, size = "/api/cart", 200, random.randint(500, 1500)
        elif r < 0.90:
            path, status, size = "/static/app.js", 200, random.randint(80000, 200000)
        else:
            path, status, size = "/api/search?q=timeout", 504, 0
        lines.append(nginx_line(ip, ts, "GET", path, status, size, ua))
    return "\n".join(lines)


def scenario_vuln_scanner():
    """Single scanner IP hammering probe paths, 85%+ 404 rate."""
    lines = []
    base = datetime(2026, 7, 17, 9, 30, 0)
    scanner_ip = "185.220.101.47"
    normal_ips = [f"198.51.100.{i}" for i in range(1, 15)]
    scanner_ua = "Nikto/2.1.6 (Evasions:None)"
    normal_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

    probe_paths = [
        "/.env", "/.git/HEAD", "/wp-admin/", "/wp-login.php",
        "/phpinfo.php", "/config.php", "/backup.zip",
        "/admin/config", "/cgi-bin/test.cgi", "/setup.php",
        "/.env.local", "/.env.production", "/server-status",
        "/phpmyadmin/", "/db/", "/.DS_Store",
        "/api/admin", "/console", "/actuator/health",
        "/web.config", "/.htpasswd", "/crossdomain.xml",
    ]

    # Legit traffic
    for i in range(60):
        ts = base + timedelta(seconds=i * 2.5)
        ip = random.choice(normal_ips)
        path = random.choice(["/", "/products", "/about", "/login"])
        lines.append(nginx_line(ip, ts, "GET", path, 200, random.randint(1000, 8000), normal_ua))

    # Scanner flood
    for i, probe in enumerate(probe_paths * 18):
        ts = base + timedelta(seconds=i * 0.28)
        lines.append(nginx_line(scanner_ip, ts, "GET", probe, 404, 162, scanner_ua))

    random.shuffle(lines)
    return "\n".join(lines)


def scenario_credential_stuffing():
    """Single attacker IP: 700 POST /login with 401 responses."""
    lines = []
    base = datetime(2026, 7, 17, 9, 40, 0)
    attacker_ip = "18.24.16.8"
    normal_ips = [f"192.168.1.{i}" for i in range(1, 20)]
    normal_ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    bot_ua = "python-requests/2.31.0"

    # Legit users doing normal stuff
    for i in range(60):
        ts = base + timedelta(seconds=i * 3)
        ip = random.choice(normal_ips)
        lines.append(nginx_line(ip, ts, "GET", "/", 200, 4200, normal_ua))
        lines.append(nginx_line(ip, ts + timedelta(seconds=1), "POST", "/login", 200, 890, normal_ua))

    # Credential stuffing: 700 failed logins in ~4 minutes
    for i in range(700):
        ts = base + timedelta(seconds=i * 0.34)
        status = 401 if random.random() < 0.96 else 403
        lines.append(nginx_line(attacker_ip, ts, "POST", "/login", status, 89, bot_ua))

    random.shuffle(lines)
    return "\n".join(lines)


def scenario_product_funnel():
    """1000 simulated users navigating landing → products → checkout."""
    lines = []
    base = datetime(2026, 7, 17, 10, 0, 0)
    ips_pool = [f"10.{random.randint(0,9)}.{random.randint(0,9)}.{i}" for i in range(1, 401)]
    ua_mobile = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit"
    ua_desktop = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    for user_idx in range(1000):
        ip = ips_pool[user_idx % len(ips_pool)]
        ua = ua_mobile if random.random() < 0.55 else ua_desktop
        ts = base + timedelta(seconds=user_idx * 0.9, minutes=random.randint(0, 50))

        # Landing (100%)
        lines.append(nginx_line(ip, ts, "GET", "/", 200, random.randint(4000, 7000), ua))

        # Products (87%)
        if random.random() < 0.87:
            ts += timedelta(seconds=random.randint(5, 35))
            lines.append(nginx_line(ip, ts, "GET", "/products", 200, random.randint(6000, 12000), ua))

            # Product detail (55% of above)
            if random.random() < 0.55:
                ts += timedelta(seconds=random.randint(10, 60))
                pid = random.randint(100, 999)
                lines.append(nginx_line(ip, ts, "GET", f"/products/{pid}", 200, random.randint(4000, 8000), ua))

                # Add to cart (28%)
                if random.random() < 0.28:
                    ts += timedelta(seconds=random.randint(5, 25))
                    lines.append(nginx_line(ip, ts, "POST", "/cart/add", 200, 420, ua))

                    # Checkout (16%)
                    if random.random() < 0.16:
                        ts += timedelta(seconds=random.randint(15, 90))
                        lines.append(nginx_line(ip, ts, "POST", "/checkout", 200, 1200, ua))

    random.shuffle(lines)
    return "\n".join(lines)


def scenario_cascading_failure():
    """Normal → traffic spike → latency → 5xx cascade."""
    lines = []
    base = datetime(2026, 7, 17, 9, 30, 0)
    ips = [f"172.16.{i//50}.{i%50+1}" for i in range(150)]
    ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

    # Normal phase (2 min)
    for i in range(240):
        ts = base + timedelta(seconds=i * 0.5)
        lines.append(nginx_line(random.choice(ips), ts, "GET",
                                random.choice(["/api/data", "/api/users", "/"]),
                                200, random.randint(1000, 4000), ua))

    # Spike + degradation (3 min): 5× traffic, rising latency
    spike_base = base + timedelta(minutes=2)
    for i in range(900):
        ts = spike_base + timedelta(seconds=i * 0.2)
        if i < 400:
            status = 200
            size = random.randint(800, 3000)
        else:
            # 5xx starts appearing
            r = random.random()
            if r < 0.22:
                status = random.choice([502, 503, 504])
                size = 0
            else:
                status = 200
                size = random.randint(500, 2000)
        path = random.choice(["/api/data", "/api/search", "/api/users", "/api/orders"])
        lines.append(nginx_line(random.choice(ips), ts, "GET", path, status, size, ua))

    return "\n".join(lines)


def scenario_injection():
    """SQL injection, XSS, and path traversal payloads in URLs."""
    lines = []
    base = datetime(2026, 7, 17, 10, 30, 0)
    attacker_ip = "45.142.212.100"
    normal_ips = [f"203.0.113.{i}" for i in range(1, 25)]
    normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    hacker_ua = "curl/7.68.0"

    sqli = [
        "/search?q=1' OR '1'='1",
        "/login?user=admin'--&pass=x",
        "/api/users?id=1 UNION SELECT username,password FROM users--",
        "/products?sort=price UNION ALL SELECT null,null,null--",
        "/api/data?filter=1; DROP TABLE users--",
    ]
    xss = [
        "/search?q=<script>alert(1)</script>",
        "/comment?text=<img src=x onerror=alert(document.cookie)>",
        "/profile?name=javascript:alert('XSS')",
    ]
    traversal = [
        "/download?file=../../etc/passwd",
        "/static?path=../../../windows/system32/config/sam",
        "/read?f=%2e%2e%2fetc%2fshadow",
        "/view?file=....//....//etc/hosts",
    ]

    # Normal traffic
    for i in range(120):
        ts = base + timedelta(seconds=i * 1.2)
        ip = random.choice(normal_ips)
        lines.append(nginx_line(ip, ts, "GET", "/products", 200, random.randint(2000, 8000), normal_ua))

    # Attack payloads
    for i, path in enumerate(sqli * 12 + xss * 10 + traversal * 8):
        ts = base + timedelta(seconds=i * 0.7)
        lines.append(nginx_line(attacker_ip, ts, "GET", path, 200, 1200, hacker_ua))

    random.shuffle(lines)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("unilog — Real-World Log Testing Harness")
    print("Generating scenarios and hitting live API at", API)

    scenarios = [
        ("slow_server",   "1 — Slow Production Server",     scenario_slow_server),
        ("vuln_scanner",  "2 — Vulnerability Scanner",       scenario_vuln_scanner),
        ("cred_stuffing", "3 — Credential Stuffing",         scenario_credential_stuffing),
        ("funnel",        "4 — Product Manager Funnel",      scenario_product_funnel),
        ("cascade",       "5 — SRE Cascading Failure",       scenario_cascading_failure),
        ("injection",     "6 — Injection Attacks",           scenario_injection),
    ]

    results = {}
    for key, label, gen_fn in scenarios:
        log_text = gen_fn()
        line_count = log_text.count("\n") + 1
        print(f"\n  >> Generating {label}: {line_count} log lines...")
        results[key] = analyze(log_text, label)

    # Final scoreboard
    print(f"\n\n{'='*62}")
    print("  DETECTION SCOREBOARD")
    print(f"{'='*62}")
    print(f"  {'Scenario':<28}  {'Parsed':>7}  {'Insights':>8}  {'Critical':>8}  {'High':>5}")
    print(f"  {'─'*56}")
    for key, label, _ in scenarios:
        r = results.get(key)
        if r:
            n = len(r.get("insights", []))
            sevs = [i["severity"] for i in r.get("insights", [])]
            parsed = r["metadata"]["analyzed_records"]
            print(f"  {label:<28}  {parsed:>7,}  {n:>8}  {sevs.count('critical'):>8}  {sevs.count('high'):>5}")
