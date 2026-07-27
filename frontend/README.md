# unilog Frontend SPA — React + TypeScript + Vite

A modern, high-performance React web application for `unilog` — Universal Log Parser & Analytics Platform.

---

## ⚡ Features & Component Architecture

- **Log Upload & Raw Text Parsing**: Drag-and-drop file uploader and live text dump area (`UploadPanel.tsx`).
- **Summary Metrics**: Animated scorecards for total requests, P99 latency, error rates, and bandwidth (`SummaryCard.tsx`).
- **Data Visualizations**: Recharts-powered graphs for log levels, status codes, latency timelines, top endpoints, and IP distributions (`components/charts/`).
- **Interactive Logs Table**: Filterable, sortable, paginated table with column toggles, keyboard roving focus, and JSON/CSV export (`components/table/`).
- **Session Observer**: Behavioral user session reconstruction, bounce rate calculation, and journey conversion funnels (`SessionObserver.tsx`).
- **Security Intelligence**: Threat profile analysis for brute force, bot probes, directory recon, and vulnerability scanners (`SecurityObserver.tsx`).
- **AI SRE Diagnostic Assistant**: Interactive LLM engine (OpenRouter / Gemini) generating root-cause reports and copyable remediation configs (`AIAssistant.tsx`).
- **Live Monitor**: Real-time full-duplex WebSocket log terminal streaming with speed control (`LiveMonitor.tsx`).
- **API & Observability Reference**: OpenAPI spec browser with dynamic Swagger, ReDoc, OpenAPI JSON, and Prometheus `/metrics` stream links (`ApiReferencePage.tsx`).

---

## 🚀 Development Setup

```bash
# Install dependencies
npm ci

# Start development server (http://localhost:5173)
npm run dev

# Run Vitest unit tests with coverage
npm run test:cov

# Production build
npm run build
```

---

## 🌐 Environment Configuration

The frontend automatically resolves the backend API URL dynamically based on environment or host context:

| Variable | Description | Default |
|:---|:---|:---|
| `VITE_API_BASE_URL` | Primary backend HTTP API URL | Auto-detect (`https://unilog-w9oe.onrender.com` on Vercel / `http://127.0.0.1:8002` on localhost) |
| `VITE_API_URL` | Fallback backend HTTP API URL | Same as `VITE_API_BASE_URL` |

---

## 🗺️ Release Checkpoints

| Release | Subsystem | Status | Features |
|:---|:---|:---|:---|
| **Release 11** | **API Reference & Observability Integration** | `COMPLETED` | Dynamic production URL resolution for Swagger, ReDoc, OpenAPI JSON, and Prometheus `/metrics` endpoints. |
| **Release 12** | **Grafana Telemetry Stream Inspector** | `COMPLETED` | Live `/metrics` stream button and Prometheus telemetry reference documentation. |
| **Release 13** | **Docker Compose Environment & SPA Integration** | `COMPLETED` | 1-Click Docker Compose deployment snippet (`docker compose up -d`), container environment guide, and live observer integration. |

