import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import SecurityObserver from "../components/SecurityObserver";
import type { SecurityMetrics } from "../types/api";

const MOCK_SECURITY_METRICS: SecurityMetrics = {
  brute_force: {
    failed_logins_per_ip: { "192.168.1.5": 42 },
    failure_ratio: 84.0,
    lockout_candidates: ["192.168.1.5"],
    lockout_candidates_count: 1
  },
  enumeration: {
    distinct_endpoints_per_ip: { "192.168.1.5": 105 },
    error_404_ratio: 12.5
  },
  bot_metrics: {
    requests_per_minute: { "192.168.1.5": 250.0 },
    missing_user_agent_count: 0,
    headless_fingerprints_count: 3
  },
  scanner_metrics: {
    scanned_ips: { "192.168.1.5": 5 },
    scanner_hits_count: 5
  },
  injection_metrics: {
    sql_injection_count: 2,
    xss_injection_count: 1,
    path_traversal_count: 0,
    rce_cmd_injection_count: 0
  }
};

describe("SecurityObserver Component", () => {
  it("renders loader while processing security metrics", () => {
    render(<SecurityObserver securityMetrics={null} isProcessing={true} />);
    expect(screen.getByText("Evaluating security intelligence rules...")).toBeInTheDocument();
  });

  it("renders empty state fallback if no security data", () => {
    render(<SecurityObserver securityMetrics={null} />);
    expect(screen.getByText("No Security Data Available")).toBeInTheDocument();
  });

  it("renders threat level banners, KPI counts, and detailed anomalies", () => {
    render(<SecurityObserver securityMetrics={MOCK_SECURITY_METRICS} />);

    // Threat Banner
    expect(screen.getByText("Critical Security Alert")).toBeInTheDocument();

    // KPI Values
    expect(screen.getByText("Injection Hits")).toBeInTheDocument();
    expect(screen.getByText("Scanner Probes")).toBeInTheDocument();
    expect(screen.getByText("Headless Bots")).toBeInTheDocument();

    // Probe IPs
    expect(screen.getAllByText("192.168.1.5")[0]).toBeInTheDocument();
    expect(screen.getByText("5 probe hits")).toBeInTheDocument();

    // Lockout Candidates
    expect(screen.getByText("Threshold Lockout")).toBeInTheDocument();
  });
});
