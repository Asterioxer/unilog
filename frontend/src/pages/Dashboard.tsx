import { useState, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { 
  FileWarning, CheckCircle2, BarChart2, AlertCircle, ChevronDown, Database, Clock 
} from "lucide-react";
import { apiService } from "../services/apiService";
import { queryKeys } from "../services/queryKeys";
import { useTaskPoller } from "../hooks/useTaskPoller";
import { DashboardProvider, useDashboardContext } from "../context/DashboardContext";
import { useDashboardActions } from "../hooks/useDashboardActions";
import { selectLogLevelDistribution } from "../transformers/logLevel";
import { selectTopIps } from "../transformers/topIps";
import { selectTopEndpoints } from "../transformers/endpoints";
import { selectStatusCodeDistribution } from "../transformers/statusCodes";
import { buildTimelineSeries } from "../transformers/timeline";
import UploadPanel from "../components/UploadPanel";
import SummaryCard from "../components/SummaryCard";
import MetricBadge from "../components/MetricBadge";
import AnimatedCounter from "../components/AnimatedCounter";
import MetadataPanel from "../components/MetadataPanel";

import ChartCard from "../components/charts/ChartCard";
import LogLevelChart from "../components/charts/LogLevelChart";
import StatusCodeChart from "../components/charts/StatusCodeChart";
import TopIPsChart from "../components/charts/TopIPsChart";
import TopEndpointsChart from "../components/charts/TopEndpointsChart";
import TimelineChart from "../components/charts/TimelineChart";

import type { FormatDetail, SessionMetrics, JourneyMetrics, SecurityMetrics } from "../types/api";
import { transformMetricsToStats } from "../utils/metricsTransformer";
import InsightCardsList from "../components/InsightCardsList";
import SessionObserver from "../components/SessionObserver";
import SecurityObserver from "../components/SecurityObserver";
import AIAssistant from "../components/AIAssistant";
import LiveMonitor from "../components/LiveMonitor";

function DashboardContent() {
  const [file, setFile] = useState<File | null>(null);
  const [activeResultTab, setActiveResultTab] = useState<"overview" | "sessions" | "security" | "ai">("overview");
  
  const { state, setState } = useDashboardContext();
  const queryClient = useQueryClient();
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

  const { data: records } = useQuery<Record<string, unknown>[] | null>({
    queryKey: queryKeys.records,
    queryFn: () => null,
    staleTime: Infinity,
    gcTime: Infinity,
    initialData: null,
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
        queryClient.setQueryData(queryKeys.records, records);

        setState((prev) => {
          let statsResponse;
          if (taskRes.result?.metrics) {
            statsResponse = transformMetricsToStats(taskRes.result.metrics, taskRes.result.format || prev.analysis.stats?.format || prev.ui.selectedFormat);
          } else {
            const levels: Record<string, number> = {};
            const ips: Record<string, number> = {};
            const endpoints: Record<string, number> = {};
            const statusCodes: Record<string, number> = {};
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

              const status = String(r["status_code"] || r["status"] || "");
              if (status) {
                statusCodes[status] = (statusCodes[status] || 0) + 1;
              }

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

            statsResponse = {
              format: taskRes.result?.format || prev.analysis.stats?.format || prev.ui.selectedFormat,
              total_lines: taskRes.result?.total || 0,
              error_rate: (errors / total) * 100,
              http_5xx_rate: 0.0,
              time_range: null,
              top_ips: topIps,
              log_levels: levels,
              top_endpoints: topEndpoints,
              bytes_transferred: bytes,
              status_codes: statusCodes
            };
          }

          return {
            ...prev,
            status: "ready",
            analysis: {
              ...prev.analysis,
              stats: statsResponse,
              insights: taskRes.result?.insights || [],
              session: (taskRes.result?.metrics?.session as SessionMetrics) || null,
              journey: (taskRes.result?.metrics?.journey as JourneyMetrics) || null,
              security: (taskRes.result?.metrics?.security as SecurityMetrics) || null,
              rawMetrics: taskRes.result?.metrics || null,
              lastUpdated: new Date().toISOString()
            },
            metadata: {
              ...prev.metadata,
              completedAt: new Date().toISOString(),
              processingDurationMs: performance.now() - startTimeRef.current
            }
          };
        });
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

  const chartStatusCodes = useMemo(
    () => selectStatusCodeDistribution(state.analysis.stats),
    [state.analysis.stats]
  );

  const chartTimeline = useMemo(
    () => buildTimelineSeries(records, "hour"),
    [records]
  );

  const handleClear = () => {
    setFile(null);
    clearDashboard();
    queryClient.setQueryData(queryKeys.records, null);
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

      {/* Main Tab Switcher */}
      <div className="flex border-b border-border mb-2 max-w-sm">
        <button
          onClick={() => setActiveTab("file")}
          className={`pb-2.5 text-sm font-semibold border-b-2 px-4 transition-colors ${
            state.ui.activeTab === "file" 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          File Uploader
        </button>
        <button
          onClick={() => setActiveTab("paste")}
          className={`pb-2.5 text-sm font-semibold border-b-2 px-4 transition-colors ${
            state.ui.activeTab === "paste" 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Raw Text Dump
        </button>
        <button
          onClick={() => setActiveTab("live")}
          className={`pb-2.5 text-sm font-semibold border-b-2 px-4 transition-colors ${
            state.ui.activeTab === "live" 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Live Monitor
        </button>
      </div>

      {state.ui.activeTab === "live" ? (
        <LiveMonitor />
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col justify-between">
          <div className="space-y-6">
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
          {/* Rule Engine Insights */}
          <InsightCardsList insights={state.analysis.insights} />

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
              {/* Tab Switcher for Analytics Results */}
              <div className="flex border-b border-border mb-6">
                <button
                  onClick={() => setActiveResultTab("overview")}
                  className={`pb-3 text-sm font-semibold border-b-2 px-4 transition-colors ${
                    activeResultTab === "overview" 
                      ? "border-primary text-primary" 
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Metrics Overview
                </button>
                <button
                  onClick={() => setActiveResultTab("sessions")}
                  className={`pb-3 text-sm font-semibold border-b-2 px-4 transition-colors ${
                    activeResultTab === "sessions" 
                      ? "border-primary text-primary" 
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Session Observability & Journeys
                </button>
                <button
                  onClick={() => setActiveResultTab("security")}
                  className={`pb-3 text-sm font-semibold border-b-2 px-4 transition-colors ${
                    activeResultTab === "security" 
                      ? "border-primary text-primary" 
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Security Intelligence
                </button>
                <button
                  onClick={() => setActiveResultTab("ai")}
                  className={`pb-3 text-sm font-semibold border-b-2 px-4 transition-colors ${
                    activeResultTab === "ai" 
                      ? "border-primary text-primary" 
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  AI SRE Assistant
                </button>
              </div>

              {activeResultTab === "overview" ? (
                <>
                  {/* Detail Visualizations Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Log Level Distribution */}
                    <ChartCard
                      title="Log Level Distribution"
                      description="Severities breakdown"
                      loading={isProcessing}
                      empty={chartLogLevels.length === 0}
                      emptyTitle="No Levels Detected"
                      emptyDescription={`This log format (${state.analysis.stats?.format}) does not map severity indicators.`}
                    >
                      <LogLevelChart data={chartLogLevels} />
                    </ChartCard>

                    {/* HTTP Status Codes */}
                    <ChartCard
                      title="HTTP Status Codes"
                      description="Response status frequencies"
                      loading={isProcessing}
                      empty={chartStatusCodes.length === 0}
                      emptyTitle="No Status Codes"
                      emptyDescription={`This log format (${state.analysis.stats?.format}) does not capture HTTP response statuses.`}
                    >
                      <StatusCodeChart data={chartStatusCodes} />
                    </ChartCard>
                  </div>

                  {/* Requests Over Time */}
                  <ChartCard
                    title="Requests Over Time"
                    description="Timeline rate metrics"
                    loading={isProcessing}
                    empty={chartTimeline.length === 0}
                    emptyTitle="No Timeline Available"
                    emptyDescription={`No timestamp data available to construct timeline.`}
                  >
                    <TimelineChart data={chartTimeline} />
                  </ChartCard>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Top IP Addresses */}
                    <ChartCard
                      title="Top Client IPs"
                      description="Active request sources"
                      loading={isProcessing}
                      empty={chartTopIps.length === 0}
                      emptyTitle="No Client IP Data"
                      emptyDescription={`This log format (${state.analysis.stats?.format}) does not contain remote host IP addresses.`}
                    >
                      <TopIPsChart data={chartTopIps} />
                    </ChartCard>

                    {/* Top Requested Paths */}
                    <ChartCard
                      title="Top Endpoints & Resources"
                      description="Frequently requested paths"
                      loading={isProcessing}
                      empty={chartTopEndpoints.length === 0}
                      emptyTitle="No Path Data"
                      emptyDescription={`This log format (${state.analysis.stats?.format}) does not record server resource paths.`}
                    >
                      <TopEndpointsChart data={chartTopEndpoints} />
                    </ChartCard>
                  </div>
                </>
              ) : activeResultTab === "sessions" ? (
                <SessionObserver 
                  sessionMetrics={state.analysis.session} 
                  journeyMetrics={state.analysis.journey}
                  isProcessing={isProcessing}
                />
              ) : activeResultTab === "security" ? (
                <SecurityObserver 
                  securityMetrics={state.analysis.security} 
                  isProcessing={isProcessing}
                />
              ) : (
                <AIAssistant
                  metrics={state.analysis.rawMetrics || null}
                  insights={state.analysis.insights || []}
                  isProcessing={isProcessing}
                />
              )}
            </>
          )}
        </div>
      )}
    </>
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
