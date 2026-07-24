import { useState } from "react";
import { BookOpen, ExternalLink, Code, Check, Copy } from "lucide-react";


interface EndpointDoc {
  method: "GET" | "POST" | "DELETE" | "WS";
  path: string;
  summary: string;
  description: string;
  curlExample: string;
}

const ENDPOINTS: EndpointDoc[] = [
  {
    method: "POST",
    path: "/api/v1/analyze",
    summary: "Consolidated Analytics Pipeline Execution",
    description: "Accepts raw log text payload or task ID, runs parser detection, metrics compilation, and rule evaluation in a single pass.",
    curlExample: `curl -X POST "http://127.0.0.1:8002/api/v1/analyze" \\
  -H "Content-Type: application/json" \\
  -d '{"log_text": "185.220.101.47 - - [24/Jul/2026:19:00:00 +0000] \\"GET /wp-admin HTTP/1.1\\" 404 150 \\"-\\" \\"Nikto/2.1.6\\""}'`,
  },
  {
    method: "POST",
    path: "/api/v1/parse",
    summary: "Synchronous Log Text Parsing",
    description: "Auto-detects format heuristic score, parses raw log payload, and returns structured records with execution telemetry.",
    curlExample: `curl -X POST "http://127.0.0.1:8002/api/v1/parse" \\
  -H "Content-Type: application/json" \\
  -d '{"log_text": "192.168.1.10 - - [24/Jul/2026:19:00:00 +0000] \\"GET /index.html HTTP/1.1\\" 200 4500", "format": "auto"}'`,
  },
  {
    method: "WS",
    path: "/api/v1/ws/live",
    summary: "Real-Time WebSocket Log Stream",
    description: "Establishes full-duplex WebSocket stream emitting simulated live web traffic records with rate control frames.",
    curlExample: `wscat -c ws://127.0.0.1:8002/api/v1/ws/live`,
  },
  {
    method: "POST",
    path: "/api/v1/ai/explain",
    summary: "AI SRE Root-Cause Diagnostics",
    description: "Generates structured root-cause diagnostic reports, incident summaries, and copyable remediation configs.",
    curlExample: `curl -X POST "http://127.0.0.1:8002/api/v1/ai/explain" \\
  -H "Content-Type: application/json" \\
  -d '{"metrics": {}, "insights": []}'`,
  },
  {
    method: "GET",
    path: "/api/v1/formats",
    summary: "List Supported Log Formats",
    description: "Returns metadata for all registered parser engines including regex patterns, sample lines, and format IDs.",
    curlExample: `curl -X GET "http://127.0.0.1:8002/api/v1/formats"`,
  },
  {
    method: "GET",
    path: "/api/v1/system/info",
    summary: "System Diagnostics & Capability Telemetry",
    description: "Reports unilog engine version, active features, registered parsers, and environment limits.",
    curlExample: `curl -X GET "http://127.0.0.1:8002/api/v1/system/info"`,
  },
];

export default function ApiReferencePage() {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getMethodBadge = (method: string) => {
    switch (method) {
      case "GET":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "POST":
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
      case "DELETE":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      case "WS":
        return "bg-purple-500/10 text-purple-400 border-purple-500/20";
      default:
        return "bg-muted text-muted-foreground border-border";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="p-6 border border-border bg-card rounded-2xl shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-primary" />
              REST API & WebSocket Reference
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Explore platform API endpoints, OpenAPI schemas, and interactive OpenAPI documentation.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="http://127.0.0.1:8002/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground font-semibold text-sm rounded-xl hover:bg-primary/95 transition-all shadow-xs"
            >
              Swagger UI Docs
              <ExternalLink className="h-4 w-4" />
            </a>
            <a
              href="http://127.0.0.1:8002/openapi.json"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 border border-border bg-card hover:bg-muted text-foreground font-medium text-sm rounded-xl transition-all"
            >
              OpenAPI JSON
              <Code className="h-4 w-4" />
            </a>
          </div>
        </div>
      </div>

      {/* Endpoints List */}
      <div className="space-y-4">
        {ENDPOINTS.map((ep, idx) => (
          <div key={idx} className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold border ${getMethodBadge(ep.method)}`}>
                  {ep.method}
                </span>
                <span className="font-mono text-sm font-bold text-foreground">
                  {ep.path}
                </span>
              </div>
              <span className="text-xs text-muted-foreground font-medium">
                {ep.summary}
              </span>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              {ep.description}
            </p>

            {/* Curl Box */}
            <div className="relative bg-zinc-950 p-4 rounded-xl border border-zinc-800 text-xs font-mono text-zinc-300 overflow-x-auto">
              <button
                onClick={() => handleCopy(ep.curlExample, idx)}
                className="absolute right-3 top-3 p-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition-colors"
                title="Copy Curl Command"
              >
                {copiedIndex === idx ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
              <pre className="pr-10 whitespace-pre-wrap">{ep.curlExample}</pre>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
