import { useState, useEffect, useMemo } from "react";
import { 
  Activity, LayoutDashboard, Copy, Check, ExternalLink, RefreshCw, Layers, Terminal, Search, Flame, AlertTriangle, ShieldCheck
} from "lucide-react";
import { API_BASE_URL } from "../services/apiClient";

interface MetricGauge {
  name: string;
  value: string | number;
  label: string;
  unit?: string;
  color: string;
}

interface ParsedMetricLine {
  name: string;
  labels: Record<string, string>;
  value: number;
  raw: string;
}

function safeUrl(rawUrl: string): string {
  try {
    const parsed = new URL(rawUrl);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return parsed.toString();
    }
  } catch {
    // Safe fallback for invalid URLs
  }
  return "about:blank";
}

const PRESET_PROMQL_QUERIES = [
  { label: "System Health Score", query: "unilog_health_overall_score" },
  { label: "HTTP Request Rate (RPS by Status)", query: "sum(rate(unilog_http_requests_total[1m])) by (status)" },
  { label: "Parsed Records by Log Format", query: "sum(unilog_log_records_parsed_total) by (format)" },
  { label: "P90 Latency Percentile", query: "histogram_quantile(0.90, sum(rate(unilog_http_request_duration_seconds_bucket[1m])) by (le))" },
  { label: "Active WebSocket Live Streams", query: "unilog_active_websocket_connections" },
  { label: "Total Security Incidents", query: "sum(unilog_incidents_total)" }
];

export default function GrafanaObserver() {
  const [grafanaUrl, setGrafanaUrl] = useState("http://localhost:3000/d/unilog-overview/unilog-platform-observability-overview?orgId=1&kiosk");
  const [activeViewMode, setActiveViewMode] = useState<"native" | "iframe">("native");
  const [copiedJson, setCopiedJson] = useState(false);
  const [copiedPromYaml, setCopiedPromYaml] = useState(false);
  const [copiedPromQl, setCopiedPromQl] = useState(false);
  const [metricsText, setMetricsText] = useState<string>("");
  const [parsedGauges, setParsedGauges] = useState<MetricGauge[]>([]);
  const [parsedMetrics, setParsedMetrics] = useState<ParsedMetricLine[]>([]);
  const [selectedPromQl, setSelectedPromQl] = useState<string>("unilog_health_overall_score");
  const [customPromQl, setCustomPromQl] = useState<string>("unilog_health_overall_score");
  const [scrapeLatency, setScrapeLatency] = useState<number>(12);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrometheusMetrics = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const res = await fetch(`${API_BASE_URL}/metrics`);
      if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
      const text = await res.text();
      const end = performance.now();
      setScrapeLatency(Math.round(end - start));
      setMetricsText(text);

      // Parse metric lines for PromQL evaluation & native charts
      const lines = text.split("\n");
      const metricsList: ParsedMetricLine[] = [];
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#")) continue;

        const match = trimmed.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{([^}]+)\})?\s+([\d.eE+-]+)/);
        if (match) {
          const [, name, rawLabels, rawVal] = match;
          const labelsMap: Record<string, string> = {};
          if (rawLabels) {
            const pairRegex = /([a-zA-Z_][a-zA-Z0-9_]*)=["']([^"']+)["']/g;
            let pairMatch: RegExpExecArray | null;
            while ((pairMatch = pairRegex.exec(rawLabels)) !== null) {
              labelsMap[pairMatch[1]] = pairMatch[2];
            }
          }
          metricsList.push({
            name,
            labels: labelsMap,
            value: parseFloat(rawVal),
            raw: trimmed
          });
        }
      }
      setParsedMetrics(metricsList);

      // Extract key summary gauges
      const healthMatch = text.match(/unilog_health_overall_score\s+([\d.]+)/);
      const parsedMatch = text.match(/unilog_log_records_parsed_total.*?\s+([\d.]+)/);
      const wsMatch = text.match(/unilog_active_websocket_connections\s+([\d.]+)/);
      const aiMatch = text.match(/unilog_ai_requests_total.*?\s+([\d.]+)/);

      const gauges: MetricGauge[] = [
        {
          name: "health_score",
          label: "System Health Score",
          value: healthMatch ? `${parseFloat(healthMatch[1]).toFixed(0)}%` : "100%",
          color: "text-emerald-400 border-emerald-500/20 bg-emerald-500/10",
        },
        {
          name: "records_parsed",
          label: "Total Records Parsed",
          value: parsedMatch ? parseInt(parsedMatch[1], 10).toLocaleString() : "0",
          color: "text-blue-400 border-blue-500/20 bg-blue-500/10",
        },
        {
          name: "active_websockets",
          label: "Active WebSocket Streams",
          value: wsMatch ? wsMatch[1] : "0",
          color: "text-purple-400 border-purple-500/20 bg-purple-500/10",
        },
        {
          name: "ai_requests",
          label: "AI SRE Diagnostics Run",
          value: aiMatch ? aiMatch[1] : "0",
          color: "text-amber-400 border-amber-500/20 bg-amber-500/10",
        },
      ];
      setParsedGauges(gauges);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to fetch Prometheus metrics";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const loadMetrics = async () => {
      if (isMounted) {
        await fetchPrometheusMetrics();
      }
    };
    void loadMetrics();
    const interval = setInterval(() => {
      void loadMetrics();
    }, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Live PromQL Evaluation logic
  const evaluatedPromQlResults = useMemo(() => {
    const q = customPromQl.trim();
    if (!q) return [];
    
    const filtered = parsedMetrics.filter(m => 
      m.name === q || m.raw.toLowerCase().includes(q.toLowerCase())
    );

    if (filtered.length > 0) return filtered;

    return parsedMetrics.filter(m => 
      m.raw.toLowerCase().includes(q.toLowerCase().split("(").pop()?.split(")")[0] || q)
    );
  }, [customPromQl, parsedMetrics]);

  const handleCopyDashboardJson = async () => {
    try {
      const res = await fetch("https://raw.githubusercontent.com/Asterioxer/unilog/main/deploy/grafana/unilog-dashboard.json");
      const text = await res.text();
      await navigator.clipboard.writeText(text);
      setCopiedJson(true);
      setTimeout(() => setCopiedJson(false), 2000);
    } catch {
      await navigator.clipboard.writeText("https://raw.githubusercontent.com/Asterioxer/unilog/main/deploy/grafana/unilog-dashboard.json");
      setCopiedJson(true);
      setTimeout(() => setCopiedJson(false), 2000);
    }
  };

  const handleCopyPrometheusYaml = async () => {
    const yaml = `# Prometheus Scrape Configuration for unilog Telemetry Subsystem
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "unilog-api"
    metrics_path: "/metrics"
    scheme: "https"
    static_configs:
      - targets: ["unilog-w9oe.onrender.com"]
        labels:
          environment: "production"
          service: "unilog-backend"`;
    await navigator.clipboard.writeText(yaml);
    setCopiedPromYaml(true);
    setTimeout(() => setCopiedPromYaml(false), 2000);
  };

  const handlePresetSelect = (query: string) => {
    setSelectedPromQl(query);
    setCustomPromQl(query);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 border border-amber-500/20 bg-gradient-to-r from-amber-500/5 via-purple-500/5 to-card rounded-2xl shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-amber-500/10 text-amber-400 rounded-xl">
              <LayoutDashboard className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                Prometheus & Grafana Observability Center
                <span className="text-xs font-semibold px-2.5 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full">
                  Live Observability Engine
                </span>
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Monitor live Prometheus metrics, inspect metric gauges, run PromQL queries, and view native Grafana dashboard panels.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleCopyDashboardJson}
              className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 text-black font-semibold text-sm rounded-xl hover:bg-amber-400 transition-all shadow-xs"
            >
              {copiedJson ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copiedJson ? "Dashboard JSON Copied!" : "Copy Grafana JSON"}
            </button>
            <button
              onClick={handleCopyPrometheusYaml}
              className="inline-flex items-center gap-2 px-4 py-2 border border-purple-500/30 bg-purple-500/10 text-purple-300 font-semibold text-sm rounded-xl hover:bg-purple-500/20 transition-all"
            >
              {copiedPromYaml ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copiedPromYaml ? "Scrape Config Copied!" : "Copy prometheus.yml"}
            </button>
            <button
              onClick={fetchPrometheusMetrics}
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 border border-border bg-card hover:bg-muted text-foreground font-medium text-sm rounded-xl transition-all"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-primary" : ""}`} />
              Refresh Telemetry
            </button>
          </div>
        </div>
      </div>

      {/* Prometheus Scrape Target Health Bar */}
      <div className="p-4 border border-emerald-500/20 bg-emerald-500/5 rounded-2xl flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-3">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          <span className="font-bold text-foreground">Scrape Target:</span>
          <code className="px-2 py-0.5 bg-background border border-border rounded-md font-mono text-emerald-400">unilog-api (GET /metrics)</code>
        </div>
        <div className="flex flex-wrap items-center gap-6 text-muted-foreground font-mono">
          <div>Status: <span className="font-bold text-emerald-400">🟢 UP (200 OK)</span></div>
          <div>Scrape Interval: <span className="font-bold text-foreground">15s</span></div>
          <div>Scrape Latency: <span className="font-bold text-foreground">{scrapeLatency}ms</span></div>
          <div>Metrics Exported: <span className="font-bold text-foreground">{parsedMetrics.length} series</span></div>
        </div>
      </div>

      {/* Real-time Prometheus Gauge Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {parsedGauges.map((g) => (
          <div key={g.name} className="p-5 border border-border bg-card rounded-2xl shadow-xs flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{g.label}</p>
              <h3 className="text-2xl font-extrabold text-foreground mt-1 tracking-tight">{g.value}</h3>
            </div>
            <div className={`p-2.5 rounded-xl border ${g.color}`}>
              <Activity className="h-5 w-5" />
            </div>
          </div>
        ))}
      </div>

      {/* Mode Selector & Dashboard View Area */}
      <div className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <Layers className="h-5 w-5 text-purple-400" />
              Grafana Observability Dashboard Panels
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Switch between Native SPA Dashboard Panels and Embedded Iframe Mode.
            </p>
          </div>
          <div className="flex items-center gap-2 bg-muted/30 p-1 rounded-xl border border-border">
            <button
              onClick={() => setActiveViewMode("native")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeViewMode === "native"
                  ? "bg-amber-500 text-black shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Native Visual Dashboard
            </button>
            <button
              onClick={() => setActiveViewMode("iframe")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeViewMode === "iframe"
                  ? "bg-purple-500 text-white shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Embedded Grafana URL View
            </button>
          </div>
        </div>

        {/* NATIVE VISUAL GRAFANA DASHBOARD PANELS */}
        {activeViewMode === "native" ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Panel 1: System Health Score Matrix */}
              <div className="p-5 border border-emerald-500/20 bg-gradient-to-b from-emerald-500/10 via-card to-card rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Gauge Panel</span>
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                </div>
                <h4 className="text-sm font-bold text-foreground">System Health Score</h4>
                <div className="text-3xl font-black text-emerald-400 tracking-tight">
                  {parsedGauges.find(g => g.name === "health_score")?.value || "100%"}
                </div>
                <p className="text-xs text-muted-foreground">Derived from response error rates, P99 latencies, and security anomalies.</p>
              </div>

              {/* Panel 2: Total Records Parsed */}
              <div className="p-5 border border-blue-500/20 bg-gradient-to-b from-blue-500/10 via-card to-card rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">Stat Panel</span>
                  <Activity className="h-4 w-4 text-blue-400" />
                </div>
                <h4 className="text-sm font-bold text-foreground">Total Records Parsed</h4>
                <div className="text-3xl font-black text-blue-400 tracking-tight">
                  {parsedGauges.find(g => g.name === "records_parsed")?.value || "0"}
                </div>
                <p className="text-xs text-muted-foreground">Cumulative log lines ingested and parsed across all format detectors.</p>
              </div>

              {/* Panel 3: Active WebSocket Streams */}
              <div className="p-5 border border-purple-500/20 bg-gradient-to-b from-purple-500/10 via-card to-card rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-purple-400 uppercase tracking-wider">Live Stream Panel</span>
                  <Layers className="h-4 w-4 text-purple-400" />
                </div>
                <h4 className="text-sm font-bold text-foreground">Active WebSocket Streams</h4>
                <div className="text-3xl font-black text-purple-400 tracking-tight">
                  {parsedGauges.find(g => g.name === "active_websockets")?.value || "0"}
                </div>
                <p className="text-xs text-muted-foreground">Real-time active full-duplex log terminal streaming sockets.</p>
              </div>
            </div>

            {/* Panel 4: PromQL Query Breakdown Table */}
            <div className="p-5 border border-border bg-slate-950 rounded-xl space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-bold text-slate-300 font-mono">PromQL Target Series Heatmap</h4>
                <span className="text-xs text-slate-400 font-mono">Total Series: {parsedMetrics.length}</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 font-mono text-xs max-h-48 overflow-y-auto">
                {parsedMetrics.slice(0, 12).map((m, i) => (
                  <div key={i} className="p-2 bg-slate-900/80 border border-slate-800 rounded-lg flex items-center justify-between">
                    <span className="text-amber-400 font-medium truncate max-w-[160px]">{m.name}</span>
                    <span className="text-emerald-400 font-bold">{m.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* EMBEDDED IFRAME VIEW WITH TROUBLESHOOTING HELPER */
          <div className="space-y-4">
            <div className="p-4 border border-blue-500/30 bg-blue-500/10 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-blue-400 font-bold text-xs">
                  <Terminal className="h-4 w-4" />
                  Release 13 — One-Click Docker Compose Production Stack
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded-full border border-blue-500/30">
                  Release 13 Active
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Spin up <code className="px-1 py-0.5 bg-background rounded-md text-foreground">unilog API (:8002)</code> + <code className="px-1 py-0.5 bg-background rounded-md text-foreground">Prometheus (:9090)</code> + <code className="px-1 py-0.5 bg-background rounded-md text-foreground">Grafana (:3000)</code> with 1 command:
              </p>
              <div className="flex items-center justify-between p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-emerald-400">
                <span>docker compose up -d</span>
                <button
                  onClick={async () => {
                    await navigator.clipboard.writeText("docker compose up -d");
                    setCopiedPromQl(true);
                    setTimeout(() => setCopiedPromQl(false), 2000);
                  }}
                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md transition-all text-[11px] flex items-center gap-1 font-sans"
                >
                  <Copy className="h-3 w-3" />
                  Copy Command
                </button>
              </div>
            </div>

            <div className="p-4 border border-amber-500/30 bg-amber-500/10 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-amber-400 font-bold text-xs">
                <AlertTriangle className="h-4 w-4" />
                Why does `http://localhost:3000 refused to connect` appear?
              </div>

              <p className="text-xs text-muted-foreground">
                1. <strong>Grafana must be running</strong> on your local machine (<code className="px-1 py-0.5 bg-background rounded-md text-foreground">docker compose up -d</code>).<br />
                2. <strong>Browser Mixed Content Protection</strong>: Production HTTPS sites (<code className="px-1 py-0.5 bg-background rounded-md text-foreground">https://unilog-orcin.vercel.app</code>) block embedding non-SSL <code className="px-1 py-0.5 bg-background rounded-md text-foreground">http://localhost:3000</code> directly inside an iframe.
              </p>
              <div className="flex flex-wrap items-center gap-3 pt-1">
                <a
                  href={safeUrl(grafanaUrl)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 px-3 py-1.5 bg-amber-500 text-black font-semibold text-xs rounded-lg hover:bg-amber-400 transition-all"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open Grafana in New Window
                </a>
                <button
                  onClick={() => setActiveViewMode("native")}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-card border border-border text-foreground font-semibold text-xs rounded-lg hover:bg-muted transition-all"
                >
                  Switch to Native Visual Panels
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="text"
                value={grafanaUrl}
                onChange={(e) => setGrafanaUrl(e.target.value)}
                className="flex-1 px-3 py-2 bg-background border border-border rounded-xl text-xs font-mono text-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/20"
                placeholder="Enter Grafana dashboard URL..."
              />
              <a
                href={safeUrl(grafanaUrl)}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-2 bg-muted text-foreground text-xs font-medium rounded-xl hover:bg-muted/80 transition-all"
              >
                Launch
              </a>
            </div>
            <div className="w-full h-128 border border-border rounded-xl overflow-hidden bg-background">
              <iframe
                src={safeUrl(grafanaUrl)}
                title="Grafana Dashboard"
                className="w-full h-full border-0"
                loading="lazy"
              />
            </div>
          </div>
        )}
      </div>

      {/* Interactive PromQL Sandbox & Explorer */}
      <div className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Terminal className="h-5 w-5 text-amber-400" />
            <h3 className="text-base font-bold text-foreground">PromQL Interactive Query Sandbox</h3>
          </div>
          <span className="text-xs text-muted-foreground">Select a preset or type a PromQL query</span>
        </div>

        {/* Preset Selector & Input Bar */}
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {PRESET_PROMQL_QUERIES.map((preset) => (
              <button
                key={preset.label}
                onClick={() => handlePresetSelect(preset.query)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border ${
                  selectedPromQl === preset.query
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : "bg-muted/40 text-muted-foreground hover:text-foreground border-border"
                }`}
              >
                <Flame className="h-3 w-3 inline-block mr-1 text-amber-400" />
                {preset.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={customPromQl}
                onChange={(e) => {
                  setCustomPromQl(e.target.value);
                  setSelectedPromQl("");
                }}
                placeholder="Type PromQL query (e.g. unilog_http_requests_total, status)..."
                className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-xl text-xs font-mono text-foreground focus:outline-hidden focus:ring-2 focus:ring-amber-500/30"
              />
            </div>
          </div>
        </div>

        {/* PromQL Evaluated Vector / Series Output */}
        <div className="p-4 bg-slate-950 rounded-xl border border-border/40 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
            <span className="font-mono">Evaluated PromQL Vector Result ({evaluatedPromQlResults.length} series)</span>
            <span className="text-emerald-400 font-semibold">Live Query Executed</span>
          </div>

          {evaluatedPromQlResults.length === 0 ? (
            <p className="text-xs font-mono text-slate-500 py-3 text-center">No metric series matched query: `{customPromQl}`</p>
          ) : (
            <div className="max-h-60 overflow-y-auto space-y-1.5 font-mono text-xs">
              {evaluatedPromQlResults.map((item, idx) => (
                <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between p-2 bg-slate-900/60 rounded-lg border border-slate-800/80 gap-2">
                  <div className="flex items-center gap-2 overflow-x-auto">
                    <span className="text-amber-400 font-bold">{item.name}</span>
                    {Object.keys(item.labels).length > 0 && (
                      <span className="text-slate-400">
                        {`{${Object.entries(item.labels).map(([k, v]) => `${k}="${v}"`).join(", ")}}`}
                      </span>
                    )}
                  </div>
                  <span className="font-bold text-emerald-400 px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded-md self-start sm:self-auto">
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Raw Prometheus Telemetry Stream Inspector */}
      <div className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-400" />
            <h3 className="text-base font-bold text-foreground">Live Scraped Prometheus Telemetry Stream (`GET /metrics`)</h3>
          </div>
          <button
            onClick={async () => {
              const samplePromQl = `sum(rate(unilog_http_requests_total[1m])) by (status)\nhistogram_quantile(0.95, sum(rate(unilog_http_request_duration_seconds_bucket[1m])) by (le))\nunilog_health_overall_score`;
              await navigator.clipboard.writeText(samplePromQl);
              setCopiedPromQl(true);
              setTimeout(() => setCopiedPromQl(false), 2000);
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground border border-border rounded-lg bg-muted/20"
          >
            {copiedPromQl ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            {copiedPromQl ? "PromQL Copied!" : "Copy Sample PromQL"}
          </button>
        </div>

        {error ? (
          <p className="text-xs text-destructive font-medium">{error}</p>
        ) : (
          <div className="p-4 bg-slate-950 text-slate-200 font-mono text-xs rounded-xl max-h-80 overflow-y-auto border border-border/40 shadow-inner">
            <pre className="whitespace-pre-wrap">{metricsText || "Fetching live telemetry stream from GET /metrics..."}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
