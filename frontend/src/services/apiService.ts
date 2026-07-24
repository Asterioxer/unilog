import { apiClient } from "./apiClient";
import type {
  FormatsResponse,
  DetectResponse,
  ParseResponse,
  StatsResponse,
  UploadResponse,
  TaskResponse,
  AnalyzeResponse,
  AIExplainResponse,
} from "../types/api";

export const apiService = {
  // Liveness check
  async checkLiveness(): Promise<{ status: string }> {
    const { data } = await apiClient.get<{ status: string }>("/live");
    return data;
  },

  // Readiness check
  async checkReadiness(): Promise<{ status: string }> {
    const { data } = await apiClient.get<{ status: string }>("/ready");
    return data;
  },

  // Get registered formats
  async getFormats(): Promise<FormatsResponse> {
    const { data } = await apiClient.post<FormatsResponse>("/api/v1/formats");
    return data;
  },

  // Detect log format
  async detectFormat(logText: string): Promise<DetectResponse> {
    const { data } = await apiClient.post<DetectResponse>("/api/v1/detect", {
      log_text: logText,
    });
    return data;
  },

  // Parse log text
  async parseLog(logText: string, format?: string): Promise<ParseResponse> {
    const { data } = await apiClient.post<ParseResponse>("/api/v1/parse", {
      log_text: logText,
      format,
    });
    return data;
  },

  // Generate log statistics
  async generateStats(logText: string, format?: string): Promise<StatsResponse> {
    const { data } = await apiClient.post<StatsResponse>("/api/v1/stats", {
      log_text: logText,
      format,
    });
    return data;
  },

  // Run full analytics pipeline
  async analyzeLogs(logText: string, format?: string, windowMinutes: number = 5, enableRules: boolean = true): Promise<AnalyzeResponse> {
    const { data } = await apiClient.post<AnalyzeResponse>("/api/v1/analyze", {
      log_text: logText,
      format: format === "auto" ? undefined : format,
      window_minutes: windowMinutes,
      enable_rules: enableRules,
    });
    return data;
  },

  // Upload file (sync or async)
  async uploadFile(
    file: File, 
    format?: string, 
    signal?: AbortSignal,
    onProgress?: (percent: number) => void
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    if (format) {
      formData.append("format", format);
    }
    const { data } = await apiClient.post<UploadResponse>(
      "/api/v1/upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        signal,
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percentCompleted);
          }
        }
      }
    );
    return data;
  },

  // Get background task status
  async getTaskStatus(taskId: string): Promise<TaskResponse> {
    const { data } = await apiClient.get<TaskResponse>(
      `/api/v1/tasks/${taskId}`
    );
    return data;
  },

  // Explain logs using AI
  async explainLogs(metrics: Record<string, unknown>, insights: unknown[]): Promise<AIExplainResponse> {

    const { data } = await apiClient.post<AIExplainResponse>("/api/v1/ai/explain", {
      metrics,
      insights,
    });
    return data;
  },
};
