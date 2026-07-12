import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { 
  FileWarning, CheckCircle2, BarChart2, Clock, Database, AlertCircle, ChevronDown 
} from "lucide-react";
import { apiService } from "../services/apiService";
import { queryKeys } from "../services/queryKeys";
import { useTaskPoller } from "../hooks/useTaskPoller";
import { DashboardProvider, useDashboardContext } from "../context/DashboardContext";
import { useDashboardActions } from "../hooks/useDashboardActions";
import { selectLogLevelDistribution } from "../transformers/logLevel";
import { selectTopIps } from "../transformers/topIps";
import { selectTopEndpoints } from "../transformers/endpoints";
import UploadPanel from "../components/UploadPanel";
import SummaryCard from "../components/SummaryCard";
import EmptyState from "../components/EmptyState";
import MetricBadge from "../components/MetricBadge";
import AnimatedCounter from "../components/AnimatedCounter";
import MetadataPanel from "../components/MetadataPanel";
import type { FormatDetail } from "../types/api";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  PieChart,
  Pie
} from "recharts";

const LOG_LEVEL_COLORS: Record<string, string> = {
  INFO: "#22c55e",
  DEBUG: "#3b82f6",
  WARN: "#f59e0b",
  WARNING: "#f59e0b",
  ERROR: "#ef4444",
  CRITICAL: "#a855f7",
  SUCCESS: "#10b981",
  unknown: "#9ca3af"
};

function DashboardContent() {
  const [file, setFile] = useState<File | null>(null);
  
  const { state, setState } = useDashboardContext();
  const {
    clearDashboard,
    handleCancelUpload,
    handleAnalyze,
    setLogText,
    setSelectedFormat,
    setActiveTab,
    setGeneralError,
    startTimeRef,
  } = useDashboardActions();

  // Fetch list of registered formats using TanStack Query
  const { data: formatsData } = useQuery({
    queryKey: queryKeys.formats,
    queryFn: () => apiService.getFormats(),
    initialData: { formats: [] }
  });

  // Background task poller hook reacting to state.upload.activeTaskId
  useTaskPoller(
    state.upload.activeTaskId,
    async (taskRes) => {
      setState((prev) => ({
        ...prev,
        upload: {
          ...prev.upload,
          activeTaskId: null
        }
      }));

      if (taskRes.result) {
        const records = taskRes.result.records;
        const levels: Record<string, number> = {};
        const ips: Record<string, number> = {};
        const endpoints: Record<string, number> = {};
        let errors = 0;
        let bytes = 0;

        records.forEach((r) => {
          const lvl = String(r["level"] || r["log_level"] || "unknown").toUpperCase();
          levels[lvl] = (levels[lvl] || 0) + 1;

          if (lvl.includes("ERR") || lvl.includes("FAIL")) {
            errors++;
          }

          const ip = String(r["client_ip"] || r["source_ip"] || r["ip"] || "unknown");
          ips[ip] = (ips[ip] || 0) + 1;

          const path = String(r["request_path"] || r["path"] || r["url"] || "unknown");
          endpoints[path] = (endpoints[path] || 0) + 1;

          if (r["bytes_sent"]) {
            bytes += Number(r["bytes_sent"]);
          }
        });

        const total = records.length || 1;
        const topIps = Object.entries(ips)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([ip, val]) => ({ ip, count: val, percentage: (val / total) * 100 }));

        const topEndpoints = Object.entries(endpoints)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([endpoint, val]) => ({ endpoint, count: val, percentage: (val / total) * 100 }));

        setState((prev) => ({
          ...prev,
          status: "ready",
          analysis: {
            ...prev.analysis,
            stats: {
              format: prev.analysis.stats?.format || prev.ui.selectedFormat,
              total_lines: taskRes.result!.total,
              error_rate: (errors / total) * 100,
              http_5xx_rate: 0.0,
              time_range: null,
              top_ips: topIps,
              log_levels: levels,
              top_endpoints: topEndpoints,
              bytes_transferred: bytes
            },
            lastUpdated: new Date().toISOString()
          },
          metadata: {
            ...prev.metadata,
            completedAt: new Date().toISOString(),
            processingDurationMs: performance.now() - startTimeRef.current
          }
        }));
      }
    },
    (err) => {
      setState((prev) => ({
        ...prev,
        status: "error",
        upload: {
          ...prev.upload,
          activeTaskId: null
        },
        ui: {
          ...prev.ui,
          error: {
            title: "Polling Error",
            message: err,
            recoverable: true
          }
        }
      }));
    }
  );

  const isProcessing =
    state.status === "uploading" ||
    state.status === "processing" ||
    state.status === "polling";

  // Recharts data distributions calculated dynamically using memoized transformers
  const chartLogLevels = useMemo(
    () => selectLogLevelDistribution(state.analysis.stats),
    [state.analysis.stats]
  );
  
  const chartTopIps = useMemo(
    () => selectTopIps(state.analysis.stats),
    [state.analysis.stats]
  );
  
  const chartTopEndpoints = useMemo(
    () => selectTopEndpoints(state.analysis.stats),
    [state.analysis.stats]
  );

  const handleClear = () => {
    setFile(null);
    clearDashboard();
  };

  const handleFileSelect = (f: File) => {
    setFile(f);
    setGeneralError(null);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Log Analytics Overview</h1>
        <p className="text-muted-foreground">
          Upload log logs or paste text dumps to generate visualization metrics.
        </p>
      </div>

      {/* Control Pane & Uploaders */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col justify-between">
          <div className="space-y-6">
            {/* Tabs */}
            <div className="flex border-b border-border">
              <button
                onClick={() => setActiveTab("file")}
                className={`pb-3 text-sm font-semibold border-b-2 px-4 transition-colors ${
                  state.ui.activeTab === "file" 
                    ? "border-primary text-primary" 
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                File Uploader
              </button>
              <button
                onClick={() => setActiveTab("paste")}
                className={`pb-3 text-sm font-semibold border-b-2 px-4 transition-colors ${
                  state.ui.activeTab === "paste" 
                    ? "border-primary text-primary" 
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                Raw Text Dump
              </button>
            </div>

            {/* Tab Contents */}
            {state.ui.activeTab === "file" ? (
              <UploadPanel
                onFileSelect={handleFileSelect}
                selectedFile={file}
                onClear={handleClear}
                isUploading={state.status === "uploading"}
                uploadProgress={state.upload.progress}
                onCancel={handleCancelUpload}
                error={state.ui.error?.message || null}
                setError={setGeneralError}
              />
            ) : (
              <textarea
                value={state.ui.logText}
                onChange={(e) => setLogText(e.target.value)}
                placeholder="Paste logs here (e.g. Nginx, Apache, Syslog, JSON)..."
                rows={6}
                className="w-full rounded-lg border border-border bg-background p-3.5 text-sm focus:outline-hidden focus:ring-2 focus:ring-primary/50"
              />
            )}
          </div>

          {/* Format Select and Action */}
          <div className="flex flex-wrap items-center gap-4 mt-6">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                Log Format
              </label>
              <select
                value={state.ui.selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
                className="w-full rounded-lg border border-border bg-background p-2.5 text-sm focus:outline-hidden focus:ring-1 focus:ring-primary"
              >
                <option value="auto">Auto-Detect Format (Heuristic)</option>
                {formatsData.formats.map((f: FormatDetail) => (
                  <option key={f.name} value={f.name}>
                    {f.description} ({f.name})
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => handleAnalyze(file)}
              disabled={isProcessing}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-semibold text-sm hover:bg-primary/95 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:scale-100 disabled:pointer-events-none self-end h-[42px]"
            >
              {isProcessing ? "Processing log..." : "Run Analytics"}
            </button>
          </div>
        </div>

        {/* Info & Status Panel */}
        <div className="flex flex-col gap-6">
          <div className="border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col gap-4">
            <h2 className="text-lg font-bold tracking-tight text-foreground">Status Monitor</h2>
            
            {/* General Error Banner */}
            {state.ui.error && state.ui.activeTab !== "file" && (
              <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-start gap-2.5 animate-pulse">
                <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                <p>{state.ui.error.message}</p>
              </div>
            )}

            {/* Active task processing state */}
            {isProcessing ? (
              <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 text-primary text-sm flex items-start gap-2.5">
                <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Processing log payload</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {state.upload.activeTaskId ? "Large file background worker task running..." : "Analyzing log streams..."}
                  </p>
                </div>
              </div>
            ) : state.analysis.stats ? (
              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm flex items-start gap-2.5">
                <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Log Analytics Ready</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Detected format matches: <span className="font-semibold uppercase text-emerald-500">{state.analysis.stats.format}</span>
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-muted border border-border text-muted-foreground text-sm flex items-start gap-2.5">
                <FileWarning className="h-5 w-5 shrink-0 mt-0.5" />
                <p>No log records loaded. Use the panels to run computations.</p>
              </div>
            )}

            {/* Collapsible rankings view */}
            {state.analysis.detect && (
              <div className="border-t border-border pt-4 mt-2">
                <details className="group">
                  <summary className="flex items-center justify-between text-xs font-semibold text-muted-foreground uppercase tracking-wider cursor-pointer list-none select-none">
                    <span className="flex items-center gap-1.5">
                      Detection Confidence
                      <MetricBadge variant="success">{(state.analysis.detect.confidence * 100).toFixed(1)}%</MetricBadge>
                    </span>
                    <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
                  </summary>
                  <div className="mt-3 space-y-2 max-h-36 overflow-y-auto">
                    {state.analysis.detect.rankings.map((ranking) => (
                      <div key={ranking.format} className="flex items-center justify-between text-xs p-1.5 rounded-lg hover:bg-muted/50 transition-colors">
                        <span className="font-mono text-foreground font-semibold uppercase">{ranking.format}</span>
                        <span className="font-medium text-muted-foreground">{(ranking.confidence * 100).toFixed(2)}%</span>
                      </div>
                    ))}
                    {state.analysis.detect.reason && (
                      <p className="text-[10px] text-muted-foreground italic leading-relaxed pt-1.5 border-t border-border/40 mt-1">
                        Reason: {state.analysis.detect.reason}
                      </p>
                    )}
                  </div>
                </details>
              </div>
            )}
          </div>

          {/* Metadata Panel */}
          {(state.analysis.stats || isProcessing) && (
            <MetadataPanel
              filename={state.metadata.filename || undefined}
              fileSize={state.metadata.fileSize || undefined}
              processingTimeMs={state.metadata.processingDurationMs || undefined}
              parserName={state.analysis.stats?.format}
              rowsCount={state.analysis.stats?.total_lines}
              taskId={state.upload.activeTaskId}
              taskStatus={state.upload.activeTaskId ? (isProcessing ? "processing" : "completed") : undefined}
            />
          )}

          <div className="p-4 rounded-lg bg-muted/50 border border-border flex flex-col gap-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              File Processing Logic
            </span>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Small payloads (&lt;1MB) are processed synchronously. Larger files are offloaded to background threads.
            </p>
          </div>
        </div>
      </div>

      {/* Analytics Visualizations Panels */}
      {(state.analysis.stats || isProcessing) && (
        <div className="space-y-8 animate-fade-in">
          {/* Card Metrics Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <SummaryCard
              title="Log Format"
              value={state.analysis.stats?.format ? state.analysis.stats.format.toUpperCase() : undefined}
              subtitle={state.analysis.stats ? `Parser: ${state.analysis.stats.format}` : "Detected Format Type"}
              icon={<Database className="h-5 w-5 text-primary" />}
              accentColor="primary"
              badge={
                state.analysis.detect ? (
                  <MetricBadge variant="success">
                    {(state.analysis.detect.confidence * 100).toFixed(0)}%
                  </MetricBadge>
                ) : undefined
              }
              isLoading={isProcessing}
            />
            <SummaryCard
              title="Total Log Lines"
              value={
                state.analysis.stats ? (
                  <AnimatedCounter value={state.analysis.stats.total_lines} />
                ) : undefined
              }
              subtitle="Log Lines Parsed"
              icon={<BarChart2 className="h-5 w-5 text-emerald-500" />}
              accentColor="emerald"
              isLoading={isProcessing}
            />
            <SummaryCard
              title="Error Rate"
              value={
                state.analysis.stats ? (
                  <AnimatedCounter value={state.analysis.stats.error_rate} decimals={2} suffix="%" />
                ) : undefined
              }
              subtitle="Percentage of Error Entries"
              icon={<AlertCircle className="h-5 w-5 text-destructive" />}
              accentColor="destructive"
              badge={
                state.analysis.stats ? (
                  <MetricBadge
                    variant={
                      state.analysis.stats.error_rate > 5
                        ? "error"
                        : state.analysis.stats.error_rate > 0
                        ? "warning"
                        : "success"
                    }
                  >
                    {state.analysis.stats.error_rate > 5
                      ? "High"
                      : state.analysis.stats.error_rate > 0
                      ? "Warn"
                      : "Clear"}
                  </MetricBadge>
                ) : undefined
              }
              isLoading={isProcessing}
            />
            <SummaryCard
              title="Time Range Covered"
              value={state.analysis.stats?.time_range ? state.analysis.stats.time_range.join(" to ") : "N/A"}
              subtitle={
                state.analysis.stats?.time_range 
                  ? "Duration bounds detected" 
                  : "No timestamp range"
              }
              icon={<Clock className="h-5 w-5 text-blue-500" />}
              accentColor="blue"
              isLoading={isProcessing}
            />
          </div>

          {state.analysis.stats && (
            <>
              {/* Detail Recharts Grids */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Log Level Distribution */}
                <div className="border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col justify-between">
                  <h3 className="text-base font-bold tracking-tight mb-4 text-foreground">Log Level Distribution</h3>
                  <div className="h-64 flex items-center justify-center">
                    {chartLogLevels.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={chartLogLevels}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                          >
                            {chartLogLevels.map((entry, idx) => (
                              <Cell 
                                key={`cell-${idx}`} 
                                fill={LOG_LEVEL_COLORS[entry.name] || LOG_LEVEL_COLORS.unknown} 
                              />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <EmptyState
                        icon={<FileWarning className="h-6 w-6 text-muted-foreground" />}
                        title="No Levels Detected"
                        description={`This log format (${state.analysis.stats?.format}) does not map structured logging severity level indicators.`}
                        className="border-none bg-transparent min-h-0 py-0"
                      />
                    )}
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-2 justify-center mt-4">
                    {chartLogLevels.map((entry) => (
                      <div key={entry.name} className="flex items-center gap-1.5 text-xs">
                        <span 
                          className="h-2.5 w-2.5 rounded-xs" 
                          style={{ backgroundColor: LOG_LEVEL_COLORS[entry.name] || LOG_LEVEL_COLORS.unknown }} 
                        />
                        <span className="font-medium">{entry.name}: {entry.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Top IP Addresses */}
                <div className="border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col justify-between lg:col-span-2">
                  <h3 className="text-base font-bold tracking-tight mb-4 text-foreground">Top Client IP Request Rates</h3>
                  <div className="h-64">
                    {chartTopIps.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                           data={chartTopIps}
                           layout="vertical"
                           margin={{ left: 20, right: 20, top: 10, bottom: 10 }}
                         >
                           <XAxis type="number" />
                           <YAxis dataKey="ip" type="category" width={100} />
                           <Tooltip />
                           <Bar dataKey="count" fill="var(--color-primary)" radius={[0, 4, 4, 0]}>
                             {chartTopIps.map((_, index) => (
                               <Cell key={`cell-${index}`} fill="var(--color-primary)" />
                             ))}
                           </Bar>
                         </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <EmptyState
                        icon={<Database className="h-6 w-6 text-muted-foreground" />}
                        title="No Client IP Information"
                        description={`This log format (${state.analysis.stats?.format}) does not contain client or remote host IP address records.`}
                        className="border-none bg-transparent min-h-0 py-6"
                      />
                    )}
                  </div>
                </div>
              </div>

              {/* Top Requested Paths */}
              <div className="grid grid-cols-1 gap-8">
                <div className="border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col">
                  <h3 className="text-base font-bold tracking-tight mb-4 text-foreground">Top Requested Resources & Endpoints</h3>
                  <div className="h-64">
                    {chartTopEndpoints.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={chartTopEndpoints}
                          margin={{ top: 10, bottom: 10 }}
                        >
                          <XAxis dataKey="endpoint" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <EmptyState
                        icon={<Clock className="h-6 w-6 text-muted-foreground" />}
                        title="No Path Information"
                        description={`This log format (${state.analysis.stats?.format}) does not capture requested server resources, paths, or actions.`}
                        className="border-none bg-transparent min-h-0 py-6"
                      />
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  return (
    <DashboardProvider>
      <DashboardContent />
    </DashboardProvider>
  );
}
