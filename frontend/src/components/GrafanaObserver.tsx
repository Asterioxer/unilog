import { useState, useEffect } from "react";
import { 
  Activity, LayoutDashboard, Copy, Check, ExternalLink, RefreshCw, Layers

} from "lucide-react";
import { API_BASE_URL } from "../services/apiClient";

interface MetricGauge {
  name: string;
  value: string | number;
  label: string;
  unit?: string;
  color: string;
}

export default function GrafanaObserver() {
  const [grafanaUrl, setGrafanaUrl] = useState("http://localhost:3000/d/unilog-overview/unilog-platform-observability-overview?orgId=1&kiosk");
  const [showIframe, setShowIframe] = useState(false);
  const [copiedJson, setCopiedJson] = useState(false);
  const [copiedPromQl, setCopiedPromQl] = useState(false);
  const [metricsText, setMetricsText] = useState<string>("");
  const [parsedGauges, setParsedGauges] = useState<MetricGauge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrometheusMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/metrics`);
      if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
      const text = await res.text();
      setMetricsText(text);

      // Parse key gauge metrics from Prometheus text format
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
    fetchPrometheusMetrics();
    const interval = setInterval(fetchPrometheusMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

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

  const handleCopyPromQl = async () => {
    const samplePromQl = `sum(rate(unilog_http_requests_total[1m])) by (status)\nhistogram_quantile(0.95, sum(rate(unilog_http_request_duration_seconds_bucket[1m])) by (le))\nunilog_health_overall_score`;
    await navigator.clipboard.writeText(samplePromQl);
    setCopiedPromQl(true);
    setTimeout(() => setCopiedPromQl(false), 2000);
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
                Grafana & Prometheus Observability Center
                <span className="text-xs font-semibold px-2.5 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full">
                  Release 12 Active
                </span>
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Monitor real-time Prometheus telemetry, inspect metric gauges, and embed Grafana dashboards inside your SPA.
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

      {/* Embedded Grafana Panel & Controls */}
      <div className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <Layers className="h-5 w-5 text-purple-400" />
              Embedded Grafana Dashboard Viewer
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Enter your local or hosted Grafana URL to view live embedded dashboard panels directly in the app.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowIframe(!showIframe)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500 text-white font-semibold text-sm rounded-xl hover:bg-purple-600 transition-all shadow-xs"
            >
              <LayoutDashboard className="h-4 w-4" />
              {showIframe ? "Hide Embedded Grafana" : "Show Embedded Grafana"}
            </button>
            <a
              href={`${API_BASE_URL}/metrics`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 border border-border hover:bg-muted text-foreground font-medium text-sm rounded-xl transition-all"
            >
              Open /metrics
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>

        {showIframe ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={grafanaUrl}
                onChange={(e) => setGrafanaUrl(e.target.value)}
                className="flex-1 px-3 py-2 bg-background border border-border rounded-xl text-xs font-mono text-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/20"
                placeholder="Enter Grafana dashboard URL..."
              />
              <a
                href={grafanaUrl}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-2 bg-muted text-foreground text-xs font-medium rounded-xl hover:bg-muted/80 transition-all"
              >
                Launch
              </a>
            </div>
            <div className="w-full h-128 border border-border rounded-xl overflow-hidden bg-background">
              <iframe
                src={grafanaUrl}
                title="Grafana Dashboard"
                className="w-full h-full border-0"
                loading="lazy"
              />
            </div>
          </div>
        ) : (
          <div className="p-8 text-center border border-dashed border-border bg-muted/10 rounded-xl space-y-3">
            <LayoutDashboard className="h-10 w-10 text-muted-foreground/60 mx-auto" />
            <h4 className="text-sm font-bold text-foreground">Grafana Embedding Ready</h4>
            <p className="text-xs text-muted-foreground max-w-lg mx-auto">
              Run your Grafana instance locally with <code className="px-1.5 py-0.5 bg-muted rounded-md text-foreground">deploy/grafana/unilog-dashboard.json</code>, then click <strong>Show Embedded Grafana</strong> to render interactive Grafana panels right here inside your React application.
            </p>
          </div>
        )}
      </div>

      {/* Raw Prometheus Telemetry Stream Inspector */}
      <div className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-400" />
            <h3 className="text-base font-bold text-foreground">Live Scraped Prometheus Telemetry Stream (`GET /metrics`)</h3>
          </div>
          <button
            onClick={handleCopyPromQl}
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
