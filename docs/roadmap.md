# roadmap

This roadmap outlines the milestones for the `unilog` platform ecosystem.

## Milestone A: Core Library Stabilization (Completed)
- Stream-based parser foundation
- Auto-detection algorithm
- Custom parser plugin registry
- 8 built-in parsers

## Milestone B: REST API & Production Hardening (Completed)
- FastAPI async web service
- Background task queues for large files
- Standardized error handlers
- Gzip compression, CORS, security headers, rate limiting (100 req/min/IP)
- Dockerization running as non-root `appuser` with dynamic standard library health checks.

## Milestone C: Documentation Base (Completed)
- Architectural designs
- API references
- Plugin development guides
- Contributing policies

## Milestone D: React Dashboard Integration (Next Milestone)
- Modern React single page application (SPA) powered by Vite
- Drag-and-drop log uploader interfaces
- Live parsing visualizations and JSON tree inspectors
- Interactive charting (aggregates by IP, HTTP status, endpoint path) using Recharts
- Format auto-detection rankings chart
- Custom regex builder interface with live testing feedback

## Milestone E: Operational Intelligence Engine (v0.4 Roadmap)
- **Release 1**: Core analytics architecture (Done)
- **Release 2**: Traffic, error, endpoint metrics (Done)
- **Operational Hardening**: Safe exceptions, CORS, proxy rate limiting (Done)
- **Release 3**: Performance Analytics (Latency, IP/size distribution, Bandwidth, Traffic Burst timeline)
- **Release 4**: Rule Engine (evaluates thresholds, generates alerts)
- **Release 5**: Insight Cards (UI representation of rule alerts)
- **Release 6**: Session Analytics (reconstruction of user journeys)
- **Release 7**: Security Analytics (attack signatures: brute force, SQLi, scans, DDoS)
- **Release 8**: AI Operational Intelligence (explanations & recommendations via LLM)
- **Release 9**: Live Monitoring Mode (`tail -f` realtime observability)
- **Release 10**: Correlation Engine (cross-log correlation & root cause analysis)
