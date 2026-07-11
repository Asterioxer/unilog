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

## Milestone E: Advanced Analytics & Orchestration (Future)
- **Dynamic Configuration Endpoint**: Add `GET /api/v1/config` to expose backend upload limits (e.g., maximum file sizes) and supported formats/extensions to the frontend dynamically.
- **Anomaly Detection Module**: Outlier detection using Isolation Forest or DBSCAN on request frequencies and error rates.
- **Alerting Rules Engine**: Configure notification destinations (Webhooks, Slack, Email) when error rates exceed threshold.
- **Database Backend**: Persistent log indices using DuckDB or SQLite for historical search queries.
