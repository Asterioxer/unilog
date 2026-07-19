# unilog — PowerShell Test Commands
# Run these one at a time in your terminal while the API server is running.
# Server: uv run uvicorn api.app:app --host 127.0.0.1 --port 8002 --reload

# ─────────────────────────────────────────────────────────
# OPTION 1: Check the API is alive
# ─────────────────────────────────────────────────────────

Invoke-RestMethod -Uri "http://127.0.0.1:8002/health" | ConvertTo-Json

# ─────────────────────────────────────────────────────────
# OPTION 2: Parse a single nginx log line
# ─────────────────────────────────────────────────────────

$body = @{
    log_text = '185.220.101.47 - - [19/Jul/2026:09:00:00 +0530] "GET /.env HTTP/1.1" 404 162 "-" "Nikto/2.1.6"'
    format   = "nginx"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8002/api/v1/parse" `
    -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 5

# ─────────────────────────────────────────────────────────
# OPTION 3: Full analyze (scanner attack — copy paste this whole block)
# ─────────────────────────────────────────────────────────

$scannerLog = @"
185.220.101.47 - - [19/Jul/2026:09:00:00 +0530] "GET /.env HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
185.220.101.47 - - [19/Jul/2026:09:00:01 +0530] "GET /.git/HEAD HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
185.220.101.47 - - [19/Jul/2026:09:00:02 +0530] "GET /wp-admin/ HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
185.220.101.47 - - [19/Jul/2026:09:00:03 +0530] "GET /phpinfo.php HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
185.220.101.47 - - [19/Jul/2026:09:00:04 +0530] "GET /backup.zip HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
185.220.101.47 - - [19/Jul/2026:09:00:05 +0530] "GET /config.php HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
185.220.101.47 - - [19/Jul/2026:09:00:06 +0530] "GET /phpmyadmin/ HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
203.0.113.10 - - [19/Jul/2026:09:00:07 +0530] "GET / HTTP/1.1" 200 4200 "-" "Mozilla/5.0"
203.0.113.11 - - [19/Jul/2026:09:00:08 +0530] "GET /products HTTP/1.1" 200 8400 "-" "Mozilla/5.0"
185.220.101.47 - - [19/Jul/2026:09:00:09 +0530] "GET /.env.local HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
185.220.101.47 - - [19/Jul/2026:09:00:10 +0530] "GET /cgi-bin/test.cgi HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
185.220.101.47 - - [19/Jul/2026:09:00:11 +0530] "GET /admin/config HTTP/1.1" 404 162 "-" "Nikto/2.1.6"
"@

$body = @{
    log_text       = $scannerLog
    format         = "nginx"
    enable_rules   = $true
    window_minutes = 60
} | ConvertTo-Json

$result = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8002/api/v1/analyze" `
    -ContentType "application/json" -Body $body

# Print insights
Write-Host "`n=== INSIGHTS ===" -ForegroundColor Cyan
foreach ($ins in $result.insights) {
    $color = switch ($ins.severity) {
        "critical" { "Red" }
        "high"     { "Yellow" }
        "medium"   { "DarkYellow" }
        default    { "White" }
    }
    Write-Host "[$($ins.severity.ToUpper())] $($ins.description)" -ForegroundColor $color
    Write-Host "  -> $($ins.recommendation)" -ForegroundColor Gray
}

# Print security metrics
Write-Host "`n=== SECURITY ===" -ForegroundColor Cyan
$result.metrics.security | ConvertTo-Json -Depth 5

# ─────────────────────────────────────────────────────────
# OPTION 4: Credential stuffing attack simulation
# ─────────────────────────────────────────────────────────

$loginLog = @"
18.24.16.8 - - [19/Jul/2026:09:40:00 +0530] "POST /login HTTP/1.1" 401 89 "-" "python-requests/2.31.0"
18.24.16.8 - - [19/Jul/2026:09:40:01 +0530] "POST /login HTTP/1.1" 401 89 "-" "python-requests/2.31.0"
18.24.16.8 - - [19/Jul/2026:09:40:02 +0530] "POST /login HTTP/1.1" 401 89 "-" "python-requests/2.31.0"
18.24.16.8 - - [19/Jul/2026:09:40:03 +0530] "POST /login HTTP/1.1" 401 89 "-" "python-requests/2.31.0"
18.24.16.8 - - [19/Jul/2026:09:40:04 +0530] "POST /login HTTP/1.1" 401 89 "-" "python-requests/2.31.0"
18.24.16.8 - - [19/Jul/2026:09:40:05 +0530] "POST /login HTTP/1.1" 401 89 "-" "python-requests/2.31.0"
18.24.16.8 - - [19/Jul/2026:09:40:06 +0530] "POST /login HTTP/1.1" 401 89 "-" "python-requests/2.31.0"
18.24.16.8 - - [19/Jul/2026:09:40:07 +0530] "POST /login HTTP/1.1" 403 89 "-" "python-requests/2.31.0"
192.168.1.5 - - [19/Jul/2026:09:40:08 +0530] "GET / HTTP/1.1" 200 4200 "-" "Mozilla/5.0"
192.168.1.5 - - [19/Jul/2026:09:40:09 +0530] "POST /login HTTP/1.1" 200 890 "-" "Mozilla/5.0"
"@

$body = @{
    log_text       = $loginLog
    format         = "nginx"
    enable_rules   = $true
    window_minutes = 60
} | ConvertTo-Json

$result = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8002/api/v1/analyze" `
    -ContentType "application/json" -Body $body

Write-Host "`n=== BRUTE FORCE METRICS ===" -ForegroundColor Cyan
$result.metrics.security.brute_force | ConvertTo-Json

Write-Host "`n=== INSIGHTS ===" -ForegroundColor Cyan
foreach ($ins in $result.insights) {
    $color = if ($ins.severity -eq "critical") { "Red" } else { "Yellow" }
    Write-Host "[$($ins.severity.ToUpper())] $($ins.description)" -ForegroundColor $color
    Write-Host "  -> $($ins.recommendation)" -ForegroundColor Gray
}

# ─────────────────────────────────────────────────────────
# OPTION 5: Run the full Python harness (all 6 scenarios)
# ─────────────────────────────────────────────────────────

# NOTE: The harness talks to port 8001 by default.
# If your server is on 8002, either change the port in the script
# or temporarily update API = "http://127.0.0.1:8002/api/v1" in scripts/test_realworld.py
uv run python scripts/test_realworld.py
