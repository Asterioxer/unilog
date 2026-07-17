import type { StatsResponse } from "../types/api";

export function transformMetricsToStats(metrics: any, format: string): StatsResponse {
  const traffic = metrics.traffic || {};
  const error = metrics.error || {};
  const status = metrics.status || {};
  const endpoint = metrics.endpoint || {};
  const distribution = metrics.distribution || {};
  const bandwidth = metrics.bandwidth || {};

  const totalLines = traffic.total_requests || 0;
  
  const topIps = (distribution.top_ips || []).map((ipInfo: any) => ({
    ip: ipInfo.ip,
    count: ipInfo.requests,
    percentage: totalLines > 0 ? (ipInfo.requests / totalLines) * 100 : 0
  }));

  const topEndpoints = (endpoint.top_endpoints || []).map((ep: any) => ({
    endpoint: ep.endpoint || ep.path || "unknown",
    count: ep.count,
    percentage: ep.percentage !== undefined ? ep.percentage : (totalLines > 0 ? (ep.count / totalLines) * 100 : 0)
  }));

  return {
    format,
    total_lines: totalLines,
    error_rate: (error.error_ratio || 0) * 100,
    http_5xx_rate: status.http_5xx_rate !== undefined ? status.http_5xx_rate * 100 : null,
    time_range: null,
    top_ips: topIps,
    log_levels: error.errors_by_level || {},
    top_endpoints: topEndpoints,
    bytes_transferred: bandwidth.total_bytes_sent || traffic.volume_bytes || 0,
    status_codes: status.status_codes || {}
  };
}
