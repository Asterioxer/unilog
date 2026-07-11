export interface FormatDetail {
  name: string;
  description: string;
  priority: number;
  supported_extensions: string[];
}

export interface FormatsResponse {
  formats: FormatDetail[];
}

export interface ParseRequest {
  log_text: string;
  format?: string;
}

export interface ParseResponse {
  records: Record<string, unknown>[];
  total: number;
}

export interface DetectRequest {
  log_text: string;
}

export interface DetectRanking {
  format: string;
  confidence: number;
}

export interface DetectResponse {
  format: string;
  confidence: number;
  rankings: DetectRanking[];
  reason: string;
}

export interface StatsRequest {
  log_text: string;
  format?: string;
}

export interface TopIpInfo {
  ip: string;
  count: number;
  percentage: number;
}

export interface TopEndpointInfo {
  endpoint: string;
  count: number;
  percentage: number;
}

export interface StatsResponse {
  format: string;
  total_lines: number;
  error_rate: number;
  http_5xx_rate: number | null;
  time_range: string[] | null;
  top_ips: TopIpInfo[];
  log_levels: Record<string, number>;
  top_endpoints: TopEndpointInfo[];
  bytes_transferred: number;
}

export interface UploadResponse {
  task_id: string | null;
  status: "completed" | "processing" | "failed";
  filename: string;
  size: number;
  format: string;
  records: Record<string, unknown>[] | null;
}

export interface TaskResponse {
  status: "processing" | "completed" | "failed";
  filename: string;
  result: {
    records: Record<string, unknown>[];
    total: number;
  } | null;
  error: string | null;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ApiErrorResponse {
  success: boolean;
  error: ApiErrorDetail;
}
