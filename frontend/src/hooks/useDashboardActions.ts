import { useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useDashboardContext } from "../context/DashboardContext";
import { useUploadMutation } from "./useUploadMutation";
import { useStatsQuery } from "./useStatsQuery";
import { useDetectionQuery } from "./useDetectionQuery";
import { queryKeys } from "../services/queryKeys";
import { apiService } from "../services/apiService";
import type { DashboardError } from "../types/dashboard";
import { transformMetricsToStats } from "../utils/metricsTransformer";

export const useDashboardActions = () => {
  const { state, setState } = useDashboardContext();
  const queryClient = useQueryClient();

  const uploadMutation = useUploadMutation();
  const statsMutation = useStatsQuery();
  const detectMutation = useDetectionQuery();

  const abortControllerRef = useRef<AbortController | null>(null);
  const startTimeRef = useRef<number>(0);

  const clearDashboard = () => {
    setState((prev) => ({
      ...prev,
      status: "idle",
      upload: {
        progress: 0,
        activeTaskId: null,
        isUploading: false,
      },
      analysis: {
        stats: null,
        detect: null,
        insights: null,
        session: null,
        journey: null,
        security: null,
        derivedData: {},
        lastUpdated: null,
      },
      metadata: {
        filename: null,
        fileSize: null,
        startedAt: null,
        completedAt: null,
        processingDurationMs: null,
      },
      ui: {
        ...prev.ui,
        logText: "",
        error: null,
      },
    }));
  };

  const handleCancelUpload = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    uploadMutation.reset();
    setState((prev) => ({
      ...prev,
      status: "idle",
      upload: {
        progress: 0,
        activeTaskId: null,
        isUploading: false,
      },
      ui: {
        ...prev.ui,
        error: {
          title: "Cancelled",
          message: "Upload cancelled by user",
          recoverable: true,
        },
      },
    }));
  };

  const handleAnalyze = async (file: File | null) => {
    const startTime = performance.now();
    startTimeRef.current = startTime;
    const startedAt = new Date().toISOString();

    // Optimistic Reset
    setState((prev) => ({
      ...prev,
      status: prev.ui.activeTab === "file" ? "uploading" : "processing",
      upload: {
        progress: 0,
        activeTaskId: null,
        isUploading: prev.ui.activeTab === "file",
      },
      analysis: {
        stats: null,
        detect: null,
        insights: null,
        session: null,
        journey: null,
        security: null,
        derivedData: {},
        lastUpdated: null,
      },
      metadata: {
        filename: prev.ui.activeTab === "file" ? (file?.name || null) : "Pasted Dump",
        fileSize: prev.ui.activeTab === "file" ? (file?.size || null) : new Blob([prev.ui.logText]).size,
        startedAt,
        completedAt: null,
        processingDurationMs: null,
      },
      ui: {
        ...prev.ui,
        error: null,
      },
    }));

    if (state.ui.activeTab === "paste") {
      if (!state.ui.logText.trim()) {
        setState((prev) => ({
          ...prev,
          status: "error",
          ui: {
            ...prev.ui,
            error: {
              title: "Validation Error",
              message: "Please paste some log text to analyze",
              recoverable: true,
            },
          },
        }));
        return;
      }

      try {
        const statsPromise = statsMutation.mutateAsync({
          logText: state.ui.logText,
          format: state.ui.selectedFormat,
        });
        const detectPromise = detectMutation.mutateAsync({
          logText: state.ui.logText,
        });
        const parsePromise = apiService.parseLog(
          state.ui.logText,
          state.ui.selectedFormat === "auto" ? undefined : state.ui.selectedFormat
        );

        const [stats, detect, parseRes] = await Promise.all([statsPromise, detectPromise, parsePromise]);
        queryClient.setQueryData(queryKeys.records, parseRes.records);

        const statsResponse = transformMetricsToStats(stats.metrics, stats.format || detect.format || "unknown");

        setState((prev) => ({
          ...prev,
          status: "ready",
          analysis: {
            ...prev.analysis,
            stats: statsResponse,
            detect,
            insights: stats.insights || [],
            session: stats.session || null,
            journey: stats.journey || null,
            security: stats.security || null,
            rawMetrics: stats.metrics || null,
            lastUpdated: new Date().toISOString(),
          },
          metadata: {
            ...prev.metadata,
            completedAt: new Date().toISOString(),
            processingDurationMs: performance.now() - startTime,
          },
        }));
      } catch (err: unknown) {
        const apiError = err as { message?: string };
        setState((prev) => ({
          ...prev,
          status: "error",
          ui: {
            ...prev.ui,
            error: {
              title: "Analysis Failed",
              message: apiError.message || "Failed to process log text analytics",
              recoverable: true,
            },
          },
        }));
      }
    } else {
      if (!file) {
        setState((prev) => ({
          ...prev,
          status: "error",
          ui: {
            ...prev.ui,
            error: {
              title: "Validation Error",
              message: "Please select or drop a log file first",
              recoverable: true,
            },
          },
        }));
        return;
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      uploadMutation.mutate(
        {
          file,
          format: state.ui.selectedFormat,
          signal: controller.signal,
          onProgress: (percent) => {
            setState((prev) => ({
              ...prev,
              upload: {
                ...prev.upload,
                progress: percent,
              },
            }));
          },
        },
        {
          onSuccess: (data) => {
            setState((prev) => ({
              ...prev,
              upload: {
                ...prev.upload,
                isUploading: false,
              },
            }));

            if (data.task_id) {
              setState((prev) => ({
                ...prev,
                status: "polling",
                upload: {
                  ...prev.upload,
                  activeTaskId: data.task_id,
                },
              }));

              // Concurrently run format detection on the first 20KB of the file
              const reader = new FileReader();
              reader.onload = async (e) => {
                const text = e.target?.result as string;
                try {
                  const detect = await detectMutation.mutateAsync({ logText: text });
                  setState((prev) => ({
                    ...prev,
                    analysis: {
                      ...prev.analysis,
                      detect,
                      lastUpdated: new Date().toISOString(),
                    },
                  }));
                } catch (err) {
                  console.error("Format detection failed on background header", err);
                }
              };
              reader.readAsText(file.slice(0, 20 * 1024));
            } else if (data.status === "completed" && data.records) {
              // Small file completed synchronously
              const reader = new FileReader();
              reader.onload = async (e) => {
                const text = e.target?.result as string;
                try {
                  const [stats, detect] = await Promise.all([
                    statsMutation.mutateAsync({ logText: text, format: data.format }),
                    detectMutation.mutateAsync({ logText: text }),
                  ]);
                  queryClient.setQueryData(queryKeys.records, data.records);

                  const statsResponse = transformMetricsToStats(stats.metrics, stats.format || data.format || detect.format || "unknown");

                  setState((prev) => ({
                    ...prev,
                    status: "ready",
                    analysis: {
                      ...prev.analysis,
                      stats: statsResponse,
                      detect,
                      insights: stats.insights || [],
                      session: stats.session || null,
                      journey: stats.journey || null,
                      security: stats.security || null,
                      rawMetrics: stats.metrics || null,
                      lastUpdated: new Date().toISOString(),
                    },
                    metadata: {
                      ...prev.metadata,
                      completedAt: new Date().toISOString(),
                      processingDurationMs: performance.now() - startTimeRef.current,
                    },
                  }));
                } catch (err: unknown) {
                  const apiError = err as { message?: string };
                  setState((prev) => ({
                    ...prev,
                    status: "error",
                    ui: {
                      ...prev.ui,
                      error: {
                        title: "Processing Error",
                        message: apiError.message || "Failed to generate analytics for uploaded file",
                        recoverable: true,
                      },
                    },
                  }));
                }
              };
              reader.readAsText(file);
            }
          },
          onError: (err: Error) => {
            setState((prev) => ({
              ...prev,
              status: "error",
              upload: {
                ...prev.upload,
                isUploading: false,
              },
              ui: {
                ...prev.ui,
                error: {
                  title: "Upload Failed",
                  message: err.message || "File upload failed",
                  recoverable: true,
                },
              },
            }));
          },
        }
      );
    }
  };

  const setLogText = (logText: string) => {
    setState((prev) => ({
      ...prev,
      ui: { ...prev.ui, logText },
    }));
  };

  const setSelectedFormat = (selectedFormat: string) => {
    setState((prev) => ({
      ...prev,
      ui: { ...prev.ui, selectedFormat },
    }));
  };

  const setActiveTab = (activeTab: "file" | "paste") => {
    setState((prev) => ({
      ...prev,
      ui: { ...prev.ui, activeTab },
    }));
  };

  const setGeneralError = (errorStr: string | null) => {
    const errorObj: DashboardError | null = errorStr
      ? { title: "Error", message: errorStr, recoverable: true }
      : null;
    setState((prev) => ({
      ...prev,
      ui: { ...prev.ui, error: errorObj },
    }));
  };

  return {
    state,
    setState,
    clearDashboard,
    handleCancelUpload,
    handleAnalyze,
    setLogText,
    setSelectedFormat,
    setActiveTab,
    setGeneralError,
    startTimeRef,
  };
};
