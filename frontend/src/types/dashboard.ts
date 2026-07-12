import type { StatsResponse, DetectResponse } from "./api";

export type DashboardStatus =
  | "idle"
  | "uploading"
  | "processing"
  | "polling"
  | "ready"
  | "error";

export interface DashboardError {
  title: string;
  message: string;
  code?: string;
  recoverable: boolean;
}

export interface DashboardMetadata {
  filename: string | null;
  fileSize: number | null;
  startedAt: string | null;      // ISO Timestamp
  completedAt: string | null;    // ISO Timestamp
  processingDurationMs: number | null;
}

export interface UploadState {
  progress: number;
  activeTaskId: string | null;
  isUploading: boolean;
}

export interface DerivedData {
  logLevelDistribution?: { name: string; value: number }[];
  topEndpoints?: { endpoint: string; count: number; percentage: number }[];
  topIps?: { ip: string; count: number; percentage: number }[];
}

export interface AnalysisState {
  stats: StatsResponse | null;
  detect: DetectResponse | null;
  derivedData: DerivedData;
  lastUpdated: string | null;    // ISO Timestamp
}

export interface UIState {
  activeTab: "file" | "paste";
  selectedFormat: string;
  logText: string;
  error: DashboardError | null;
}

export interface DashboardState {
  status: DashboardStatus;
  upload: UploadState;
  analysis: AnalysisState;
  metadata: DashboardMetadata;
  ui: UIState;
}
