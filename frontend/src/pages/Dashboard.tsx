import { useState, useRef } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { 
  FileWarning, CheckCircle2, BarChart2, Clock, Database, AlertCircle 
} from "lucide-react";
import { apiService } from "../services/apiService";
import { useTaskPoller } from "../hooks/useTaskPoller";
import UploadPanel from "../components/UploadPanel";
import SummaryCard from "../components/SummaryCard";
import type { StatsResponse, FormatDetail } from "../types/api";
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
  INFO: "var(--color-primary)",
  WARN: "#eab308",
  ERROR: "#ef4444",
  FATAL: "#7f1d1d",
  DEBUG: "#6b7280",
  unknown: "#a1a1aa"
};

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<string>("auto");
  const [logText, setLogText] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"file" | "paste">("file");
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  
  // Analytics stats hold state
  const [statsData, setStatsData] = useState<StatsResponse | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Fetch list of registered formats
  const { data: formatsData } = useQuery({
    queryKey: ["formats"],
    queryFn: () => apiService.getFormats(),
    initialData: { formats: [] }
  });

  // Parse direct text stats mutation
  const parseTextMutation = useMutation({
    mutationFn: (text: string) => apiService.generateStats(text, selectedFormat === "auto" ? undefined : selectedFormat),
    onSuccess: (data) => {
      setStatsData(data);
      setGeneralError(null);
    },
    onError: (err: unknown) => {
      const apiError = err as { message?: string };
      setGeneralError(apiError.message || "Failed to process log text analytics");
      setStatsData(null);
    }
  });

  // File upload mutation
  const uploadFileMutation = useMutation({
    mutationFn: (payload: { file: File; format?: string }) => {
      const controller = new AbortController();
      abortControllerRef.current = controller;
      setUploadProgress(0);
      return apiService.uploadFile(
        payload.file,
        payload.format === "auto" ? undefined : payload.format,
        controller.signal,
        (percent) => setUploadProgress(percent)
      );
    },
    onSuccess: (data) => {
      if (data.task_id) {
        // Asynchronous processing (large file >1MB)
        setActiveTaskId(data.task_id);
        setGeneralError(null);
      } else if (data.status === "completed" && data.records) {
        // Synchronous processing completed (small file <=1MB)
        const reader = new FileReader();
        reader.onload = async (e) => {
          const text = e.target?.result as string;
          try {
            const stats = await apiService.generateStats(text, data.format);
            setStatsData(stats);
            setGeneralError(null);
          } catch (err: unknown) {
            const apiError = err as { message?: string };
            setGeneralError(apiError.message || "Failed to generate analytics for uploaded file");
          }
        };
        reader.readAsText(file!);
      }
    },
    onError: (err: unknown) => {
      const apiError = err as { message?: string };
      setGeneralError(apiError.message || "File upload failed");
      setStatsData(null);
    }
  });

  const handleCancelUpload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    uploadFileMutation.reset();
    setUploadProgress(0);
    setGeneralError("Upload cancelled by user");
  };

  // Background task poller hook
  useTaskPoller(
    activeTaskId,
    async (taskRes) => {
      setActiveTaskId(null);
      // Once async task completes, the records are computed and total lines are available.
      // We can generate stats for the processed records or request backend to compute stats.
      // Since backend doesn't have an async stats endpoint yet, we fetch task records and compute client-side statistics
      // or map standard fields from the task result records.
      // Let's map records to a simulated StatsResponse to populate the dashboard!
      if (taskRes.result) {
        const records = taskRes.result.records;
        // Compute stats client side from records
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

        setStatsData({
          format: statsData?.format || selectedFormat,
          total_lines: taskRes.result.total,
          error_rate: (errors / total) * 100,
          http_5xx_rate: 0.0,
          time_range: null,
          top_ips: topIps,
          log_levels: levels,
          top_endpoints: topEndpoints,
          bytes_transferred: bytes
        });
      }
    },
    (err) => {
      setActiveTaskId(null);
      setGeneralError(err);
    }
  );

  const handleAnalyze = () => {
    setGeneralError(null);
    if (activeTab === "paste") {
      if (!logText.trim()) {
        setGeneralError("Please paste some log text to analyze");
        return;
      }
      parseTextMutation.mutate(logText);
    } else {
      if (!file) {
        setGeneralError("Please select or drop a log file first");
        return;
      }
      uploadFileMutation.mutate({ file, format: selectedFormat });
    }
  };



  const isProcessing = parseTextMutation.isPending || uploadFileMutation.isPending || !!activeTaskId;

  // Format Recharts distribution parameters
  const chartLogLevels = statsData
    ? Object.entries(statsData.log_levels).map(([name, value]) => ({ name, value }))
    : [];

  const chartTopIps = statsData?.top_ips || [];
  const chartTopEndpoints = statsData?.top_endpoints || [];

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
                  activeTab === "file" 
                    ? "border-primary text-primary" 
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                File Uploader
              </button>
              <button
                onClick={() => setActiveTab("paste")}
                className={`pb-3 text-sm font-semibold border-b-2 px-4 transition-colors ${
                  activeTab === "paste" 
                    ? "border-primary text-primary" 
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                Raw Text Dump
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === "file" ? (
              <UploadPanel
                onFileSelect={(f) => {
                  setFile(f);
                  setGeneralError(null);
                }}
                selectedFile={file}
                onClear={() => {
                  setFile(null);
                  setGeneralError(null);
                }}
                isUploading={uploadFileMutation.isPending}
                uploadProgress={uploadProgress}
                onCancel={handleCancelUpload}
                error={generalError}
                setError={setGeneralError}
              />
            ) : (
              <textarea
                value={logText}
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
                value={selectedFormat}
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
              onClick={handleAnalyze}
              disabled={isProcessing}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-semibold text-sm hover:bg-primary/95 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:scale-100 disabled:pointer-events-none self-end h-[42px]"
            >
              {isProcessing ? "Processing log..." : "Run Analytics"}
            </button>
          </div>
        </div>

        {/* Info & Status Panel */}
        <div className="border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col gap-6 justify-between">
          <div className="space-y-4">
            <h2 className="text-lg font-bold tracking-tight">Status Monitor</h2>
            
            {/* General Error Banner */}
            {generalError && activeTab !== "file" && (
              <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-start gap-2.5 animate-pulse">
                <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                <p>{generalError}</p>
              </div>
            )}

            {/* Active task processing state */}
            {isProcessing ? (
              <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 text-primary text-sm flex items-start gap-2.5">
                <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Processing log payload</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {activeTaskId ? "Large file background worker task running..." : "Analyzing log streams..."}
                  </p>
                </div>
              </div>
            ) : statsData ? (
              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm flex items-start gap-2.5">
                <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Log Analytics Ready</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Detected format matches: <span className="font-semibold uppercase text-emerald-500">{statsData.format}</span>
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-muted border border-border text-muted-foreground text-sm flex items-start gap-2.5">
                <FileWarning className="h-5 w-5 shrink-0 mt-0.5" />
                <p>No log records loaded. Use the panels to run computations.</p>
              </div>
            )}
          </div>

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
      {(statsData || isProcessing) && (
        <div className="space-y-8 animate-fade-in">
          {/* Card Metrics Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <SummaryCard
              title="Log Format"
              value={statsData?.format ? statsData.format.toUpperCase() : undefined}
              subtitle="Detected Format Type"
              icon={<Database className="h-5 w-5 text-primary" />}
              isLoading={isProcessing}
            />
            <SummaryCard
              title="Total Log Lines"
              value={statsData?.total_lines}
              subtitle="Log Lines Parsed"
              icon={<BarChart2 className="h-5 w-5 text-emerald-500" />}
              isLoading={isProcessing}
            />
            <SummaryCard
              title="Error Rate"
              value={statsData ? `${statsData.error_rate.toFixed(2)}%` : undefined}
              subtitle="Percentage of Error Entries"
              icon={<AlertCircle className="h-5 w-5 text-destructive" />}
              isLoading={isProcessing}
            />
            <SummaryCard
              title="Time Range Covered"
              value={statsData?.time_range ? statsData.time_range.join(" to ") : "N/A"}
              subtitle="Detected Timestamp Span"
              icon={<Clock className="h-5 w-5 text-blue-500" />}
              isLoading={isProcessing}
            />
          </div>

          {statsData && (
            <>
              {/* Detail Recharts Grids */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Log Level Distribution */}
                <div className="border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col justify-between">
                  <h3 className="text-base font-bold tracking-tight mb-4">Log Level Distribution</h3>
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
                      <span className="text-sm text-muted-foreground">No level keys mapped</span>
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
                  <h3 className="text-base font-bold tracking-tight mb-4">Top Client IP Request Rates</h3>
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
                      <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                        No client IP values mapped in stats
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Top Requested Paths */}
              <div className="grid grid-cols-1 gap-8">
                <div className="border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col">
                  <h3 className="text-base font-bold tracking-tight mb-4">Top Requested Resources & Endpoints</h3>
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
                      <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                        No path endpoints mapped in stats
                      </div>
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
