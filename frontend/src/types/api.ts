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
  status_codes?: Record<string, number>;
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
    format: string;
    metrics?: Record<string, unknown>;
    insights?: InsightResponse[];
  } | null;
  error: string | null;
}

export interface InsightResponse {
  id: string;
  category: string;
  severity: string;
  confidence: number;
  description: string;
  recommendation: string;
  evidence: Record<string, unknown>;
}

export interface AnalyzeMetadata {
  analyzed_records: number;
  skipped_records: number;
  missing_latency_fields: number;
  execution_time_ms: number;
  analyzers: { name: string; version: string }[];
}

export interface SessionRequest {
  timestamp: string;
  method: string;
  path: string;
  status_code: number;
  size: number;
  journey_stage: string;
}

export interface Session {
  session_id: string;
  client_ip: string;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  request_count: number;
  requests: SessionRequest[];
  journey: string[];
}

export interface SessionMetrics {
  average_session_duration_seconds: number;
  bounce_rate: number;
  pages_per_session: number;
  requests_per_session: number;
  active_sessions_count: number;
  longest_session_duration_seconds: number;
  sessions: Session[];
  possible_bot_count: number;
  credential_stuffing_count: number;
  endpoint_enumeration_count: number;
}

export interface JourneyMetrics {
  journeys: string[][];
  stage_counts: Record<string, number>;
  funnel: Record<string, number>;
}

export interface BruteForceMetrics {
  failed_logins_per_ip: Record<string, number>;
  failure_ratio: number;
  lockout_candidates: string[];
  lockout_candidates_count: number;
}

export interface EnumerationMetrics {
  distinct_endpoints_per_ip: Record<string, number>;
  error_404_ratio: number;
}

export interface BotMetrics {
  requests_per_minute: Record<string, number>;
  missing_user_agent_count: number;
  headless_fingerprints_count: number;
}

export interface ScannerMetrics {
  scanned_ips: Record<string, number>;
  scanner_hits_count: number;
}

export interface InjectionMetrics {
  sql_injection_count: number;
  xss_injection_count: number;
  path_traversal_count: number;
  rce_cmd_injection_count: number;
}

export interface SecurityMetrics {
  brute_force: BruteForceMetrics;
  enumeration: EnumerationMetrics;
  bot_metrics: BotMetrics;
  scanner_metrics: ScannerMetrics;
  injection_metrics: InjectionMetrics;
}

export interface AnalyzeResponse {
  metrics: Record<string, unknown>;
  insights: InsightResponse[];
  metadata: AnalyzeMetadata;
  ruleset_version: string;
  format?: string;
  session?: SessionMetrics;
  journey?: JourneyMetrics;
  security?: SecurityMetrics;
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

export interface AIRemediationCard {
  title: string;
  description: string;
  code: string;
  language: string;
}

export interface AIExplainResponse {
  summary: string;
  explanation: string;
  remediations: AIRemediationCard[];
}

export interface AIExplainRequest {
  metrics: Record<string, unknown>;
  insights: InsightResponse[];
}
