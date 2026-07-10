import os
import json
import random
from datetime import datetime, timedelta

os.makedirs("tests/sample_logs/realistic", exist_ok=True)

# Generate JSON logs
with open("tests/sample_logs/realistic/json_app.log", "w") as f:
    start_time = datetime(2026, 7, 10, 12, 0, 0)
    levels = ["info", "warning", "error", "debug"]
    messages = [
        "User login successful",
        "API request processed",
        "Connection timeout, retrying",
        "Failed to write to cache",
        "Disk space low",
        "Cache hit ratio: 0.85"
    ]
    for i in range(300):
        t = start_time + timedelta(seconds=i * 5)
        lvl = random.choice(levels)
        msg = random.choice(messages)
        rec = {
            "timestamp": t.isoformat(),
            "level": lvl,
            "message": msg,
            "req_id": f"req-{i}",
            "latency_ms": random.randint(5, 500)
        }
        # Add some dirty records (malformed json)
        if i == 50:
            f.write("invalid json line\n")
        elif i == 150:
            f.write("{'bad_quotes': 1}\n")
        else:
            f.write(json.dumps(rec) + "\n")

# Generate Nginx logs (500 lines)
with open("tests/sample_logs/realistic/nginx_500lines.log", "w") as f:
    start_time = datetime(2026, 7, 10, 12, 0, 0)
    ips = ["127.0.0.1", "192.168.1.1", "10.0.0.5", "2001:db8::1", "8.8.8.8"]
    methods = ["GET", "POST", "PUT", "DELETE", "HEAD"]
    paths = ["/index.html", "/api/v1/users", "/api/v1/login", "/static/css/main.css", "/images/logo.png"]
    statuses = [200, 200, 200, 301, 304, 400, 403, 404, 500, 503]
    referers = ["-", "http://google.com", "http://github.com", "http://localhost:8080/"]
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (Linux; Android 10; SM-A505F)",
        "curl/7.68.0",
        "Go-http-client/1.1"
    ]
    for i in range(500):
        t = start_time + timedelta(seconds=i * 2)
        # Apache/Nginx format: 10/Jul/2026:12:00:00 +0000
        t_str = t.strftime("%d/%b/%Y:%H:%M:%S +0000")
        ip = random.choice(ips)
        method = random.choice(methods)
        path = random.choice(paths)
        status = random.choice(statuses)
        size = random.randint(100, 50000) if status == 200 else 0
        ref = random.choice(referers)
        ua = random.choice(uas)
        line = f'{ip} - - [{t_str}] "{method} {path} HTTP/1.1" {status} {size} "{ref}" "{ua}"\n'
        
        # Add mixed quality lines
        if i == 100:
            f.write("corrupted line that doesn't match nginx regex\n")
        else:
            f.write(line)

# Generate Apache logs (300 lines) - similar to nginx but sometimes without referer/UA (common format) or subtle differences
with open("tests/sample_logs/realistic/apache_300lines.log", "w") as f:
    start_time = datetime(2026, 7, 10, 12, 0, 0)
    for i in range(300):
        t = start_time + timedelta(seconds=i * 3)
        t_str = t.strftime("%d/%b/%Y:%H:%M:%S -0700")
        ip = "192.168.0." + str(random.randint(10, 100))
        method = "GET" if random.random() > 0.2 else "POST"
        path = "/about" if random.random() > 0.5 else "/contact"
        status = 200 if random.random() > 0.1 else 404
        size = random.randint(200, 1500)
        
        # Mix in common vs combined
        if i % 3 == 0:
            # Common format: ip - user [time] "request" status size
            line = f'{ip} - - [{t_str}] "{method} {path} HTTP/1.1" {status} {size}\n'
        else:
            # Combined format
            line = f'{ip} - - [{t_str}] "{method} {path} HTTP/1.1" {status} {size} "http://referrer.org" "Mozilla/5.0"\n'
        
        if i == 50:
            f.write("broken apache log line\n")
        else:
            f.write(line)

# Generate Syslog (1000 lines) - mix of RFC3164 and RFC5424
with open("tests/sample_logs/realistic/syslog_1000lines.log", "w") as f:
    hosts = ["srv-web-01", "srv-db-01", "gw-router", "mail-server"]
    procs = ["sshd", "kernel", "systemd", "cron", "nginx"]
    levels = ["info", "notice", "warning", "err", "crit", "alert"]
    
    start_time = datetime(2026, 7, 10, 12, 0, 0)
    for i in range(1000):
        t = start_time + timedelta(seconds=i)
        pri = random.randint(0, 191)
        host = random.choice(hosts)
        proc = random.choice(procs)
        pid = random.randint(100, 99999)
        lvl = random.choice(levels)
        
        if i % 2 == 0:
            # RFC 3164: Oct 11 22:14:15 host proc[pid]: message
            t_str = t.strftime("%b %d %H:%M:%S")
            # Handle single digit day spacing, e.g. "Jul  9" vs "Jul 10"
            if t.day < 10:
                t_str = t.strftime("%b  %d %H:%M:%S")
            msg = f"Connection accepted from 192.168.1.100 port {random.randint(1024, 65535)}"
            line = f"<{pri}>{t_str} {host} {proc}[{pid}]: {msg}\n"
        else:
            # RFC 5424: 1 2003-10-11T22:14:15.003Z host app pid msgid [sd] message
            t_str = t.isoformat() + "Z"
            msg = f"Database sync finished in {random.randint(10, 500)}ms"
            line = f"<{pri}>1 {t_str} {host} {proc} {pid} MSG{i} [exampleSDID@32473 eventID=\"{i}\"] {msg}\n"
            
        if i == 500:
            f.write("corrupted syslog line\n")
        else:
            f.write(line)

# Generate Django logs (200 lines)
with open("tests/sample_logs/realistic/django.log", "w") as f:
    start_time = datetime(2026, 7, 10, 12, 0, 0)
    for i in range(200):
        t = start_time + timedelta(seconds=i * 10)
        lvl = random.choice(["INFO", "WARNING", "ERROR", "DEBUG"])
        if i % 2 == 0:
            # Django request log format
            line = f"[{t.strftime('%Y-%m-%d %H:%M:%S')}] {lvl} django.request: GET /api/endpoint {random.choice([200, 301, 404, 500])} {random.randint(5, 200)}ms\n"
        else:
            # Bare python logging format
            line = f"{t.strftime('%Y-%m-%d %H:%M:%S')},{random.randint(100, 999)} - app.views - {lvl} - Exception in transaction\n"
        
        if i == 100:
            f.write("django raw syntax error\n")
        else:
            f.write(line)

# Generate Windows events (200 lines)
with open("tests/sample_logs/realistic/windows_event.csv", "w") as f:
    f.write("Level,Date and Time,Source,Event ID,Task Category,Description\n")
    start_time = datetime(2026, 7, 10, 12, 0, 0)
    sources = ["Microsoft-Windows-Security-Auditing", "Service Control Manager", "Disk", "Application Error"]
    categories = ["Logon", "None", "Startup", "Shutdown"]
    for i in range(200):
        t = start_time + timedelta(seconds=i * 15)
        lvl = random.choice(["Information", "Warning", "Error"])
        src = random.choice(sources)
        ev_id = random.randint(1000, 9999)
        cat = random.choice(categories)
        desc = f"Process {random.randint(100, 9999)} started successfully."
        # Add CSV escaping just in case
        f.write(f'"{lvl}","{t.strftime("%Y-%m-%d %H:%M:%S")}","{src}",{ev_id},"{cat}","{desc}"\n')
