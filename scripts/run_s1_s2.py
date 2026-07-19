import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import scripts.test_realworld as h
h.analyze(h.scenario_slow_server(), "1 -- Slow Production Server")
h.analyze(h.scenario_vuln_scanner(), "2 -- Vulnerability Scanner")
