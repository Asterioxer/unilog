import type { StatsResponse } from "../types/api";

interface TrafficMetrics {
  total_requests?: number;
  volume_bytes?: number;
}

interface ErrorMetrics {
  total_errors?: number;
  error_ratio?: number;
  errors_by_level?: Record<string, number>;
}

interface StatusMetrics {
  status_codes?: Record<string, number>;
  status_categories?: Record<string, number>;
  http_5xx_rate?: number | null;
}

interface EndpointMetrics {
  top_endpoints?: { endpoint?: string; path?: string; count: number; percentage?: number }[];
}

interface DistributionMetrics {
  top_ips?: { ip: string; requests: number }[];
}

interface BandwidthMetrics {
  total_bytes_sent?: number;
}

interface MetricsBundle {
  traffic?: TrafficMetrics | null;
  error?: ErrorMetrics | null;
  status?: StatusMetrics | null;
  endpoint?: EndpointMetrics | null;
  distribution?: DistributionMetrics | null;
  bandwidth?: BandwidthMetrics | null;
}

export function transformMetricsToStats(metrics: MetricsBundle, format: string): StatsResponse {
  const traffic = metrics.traffic || {};
  const error = metrics.error || {};
  const status = metrics.status || {};
  const endpoint = metrics.endpoint || {};
  const distribution = metrics.distribution || {};
  const bandwidth = metrics.bandwidth || {};

  const totalLines = traffic.total_requests || 0;
  
  const topIps = (distribution.top_ips || []).map((ipInfo) => ({
    ip: ipInfo.ip,
    count: ipInfo.requests,
    percentage: totalLines > 0 ? (ipInfo.requests / totalLines) * 100 : 0
  }));

  const topEndpoints = (endpoint.top_endpoints || []).map((ep) => ({
    endpoint: ep.endpoint || ep.path || "unknown",
    count: ep.count,
    percentage: ep.percentage !== undefined ? ep.percentage : (totalLines > 0 ? (ep.count / totalLines) * 100 : 0)
  }));

  return {
    format,
    total_lines: totalLines,
    error_rate: (error.error_ratio || 0) * 100,
    http_5xx_rate: status.http_5xx_rate !== undefined && status.http_5xx_rate !== null ? status.http_5xx_rate * 100 : null,
    time_range: null,
    top_ips: topIps,
    log_levels: error.errors_by_level || {},
    top_endpoints: topEndpoints,
    bytes_transferred: bandwidth.total_bytes_sent || traffic.volume_bytes || 0,
    status_codes: status.status_codes || {}
  };
}
