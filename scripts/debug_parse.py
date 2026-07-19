import unilog
import io

# Test with latency suffix
line1 = '203.0.113.5 - - [17/Jul/2026:09:00:00 +0530] "GET /api/search HTTP/1.1" 200 8234 "-" "Mozilla/5.0" rt=0.742'
recs1 = list(unilog.stream(io.StringIO(line1)))
print("WITH rt=:", recs1)

# Test clean nginx
line2 = '203.0.113.5 - - [17/Jul/2026:09:00:00 +0530] "GET /api/search HTTP/1.1" 200 8234 "-" "Mozilla/5.0"'
recs2 = list(unilog.stream(io.StringIO(line2)))
print("CLEAN:   ", recs2)

# Check what format detect says
det = unilog.detect(io.StringIO(line1))
print("DETECT:  ", det)

# Check journey schema
import requests
resp = requests.post("http://127.0.0.1:8001/api/v1/analyze", json={
    "log_text": line2 + "\n" + line2,
    "format": "nginx",
    "enable_rules": False,
}, timeout=10)
import json
d = resp.json()
print("JOURNEY:", json.dumps(d.get("metrics", {}).get("journey", {}), indent=2))
