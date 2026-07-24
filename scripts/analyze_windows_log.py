"""
Analyze a Windows Event Viewer CSV export with unilog.
Usage: uv run python scripts/analyze_windows_log.py <path_to_csv>
"""
import sys
import pathlib

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Config ────────────────────────────────────────────────────────────────────
API = "http://127.0.0.1:8002/api/v1/analyze"
DEFAULT_CSV = pathlib.Path.home() / "Desktop" / "security_200.csv"

csv_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV

if not csv_path.exists():
    print(f"ERROR: File not found: {csv_path}")
    sys.exit(1)

print(f"Reading {csv_path} ({csv_path.stat().st_size:,} bytes)...")
try:
    log_text = csv_path.read_text(encoding="utf-8")
except UnicodeDecodeError:
    log_text = csv_path.read_text(encoding="latin-1")

# ── Send to API ───────────────────────────────────────────────────────────────
payload = {
    "log_text": log_text,
    "format": "windows",
    "enable_rules": True,
    "window_minutes": 60,
}

print(f"Sending to {API} ...")
resp = requests.post(API, json=payload, timeout=60)

if not resp.ok:
    print(f"HTTP {resp.status_code}: {resp.text[:500]}")
    sys.exit(1)

result = resp.json()
meta     = result.get("metadata", {})
insights = result.get("insights", [])
metrics  = result.get("metrics", {})

# ── Print summary ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("  ANALYSIS SUMMARY")
print("=" * 60)
print(f"  Records analyzed   : {meta.get('analyzed_records', '?')}")
print(f"  Skipped records    : {meta.get('skipped_records', '?')}")
print(f"  Execution time     : {meta.get('execution_time_ms', '?')} ms")
print(f"  Insights fired     : {len(insights)}")
print()

# ── Print insights ─────────────────────────────────────────────────────────────
if insights:
    print("=" * 60)
    print("  INSIGHTS")
    print("=" * 60)
    SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    for ins in sorted(insights, key=lambda x: SEV_ORDER.get(x.get("severity","info"), 5)):
        sev = ins.get("severity", "info").upper()
        badge = {"CRITICAL": "[!!!]", "HIGH": "[!! ]", "MEDIUM": "[ ! ]"}.get(sev, "[   ]")
        print(f"\n  {badge} [{sev}] {ins.get('description', '')}")
        print(f"       -> {ins.get('recommendation', '')}")
        ev = ins.get("evidence", {})
        if ev:
            for k, v in list(ev.items())[:3]:
                print(f"          {k}: {v}")
else:
    print("  No insights triggered (normal/quiet log period).")

# ── Print top security metrics ─────────────────────────────────────────────────
sec = metrics.get("security", {})
if sec:
    print()
    print("=" * 60)
    print("  SECURITY METRICS")
    print("=" * 60)
    bf = sec.get("brute_force", {})
    if bf:
        print(f"  Auth failures      : {bf.get('total_failures', 0)}")
        print(f"  Failure rate       : {bf.get('failure_rate', 0):.1%}")
        if bf.get("top_failing_ips"):
            print(f"  Top failing IPs    : {bf['top_failing_ips'][:3]}")
    threats = sec.get("threats", {})
    if threats:
        print()
        print("  Threat detections:")
        for name, val in threats.items():
            if val:
                print(f"    {name}: {val}")

# ── Log level distribution ─────────────────────────────────────────────────────
log_m = metrics.get("log", {})
if log_m and log_m.get("level_distribution"):
    print()
    print("=" * 60)
    print("  EVENT LEVEL DISTRIBUTION")
    print("=" * 60)
    for lvl, count in sorted(log_m["level_distribution"].items(),
                              key=lambda x: -x[1]):
        bar = "#" * min(40, int(count / max(log_m["level_distribution"].values()) * 40))
        print(f"  {lvl:<20} {count:>5}  {bar}")

print()
print("Done.")
