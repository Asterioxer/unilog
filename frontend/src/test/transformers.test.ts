import { describe, it, expect } from "vitest";
import { selectLogLevelDistribution } from "../transformers/logLevel";
import { selectTopIps } from "../transformers/topIps";
import { selectTopEndpoints } from "../transformers/endpoints";
import type { StatsResponse } from "../types/api";

const mockStats: StatsResponse = {
  format: "nginx",
  total_lines: 10,
  error_rate: 20.0,
  http_5xx_rate: 0.0,
  time_range: ["2026-07-10 12:00:00", "2026-07-10 12:05:00"],
  top_ips: [
    { ip: "127.0.0.1", count: 8, percentage: 80 },
    { ip: "192.168.1.1", count: 2, percentage: 20 },
  ],
  log_levels: {
    INFO: 6,
    ERROR: 2,
    WARN: 2,
  },
  top_endpoints: [
    { endpoint: "/home", count: 5, percentage: 50 },
    { endpoint: "/login", count: 5, percentage: 50 },
  ],
  bytes_transferred: 1024,
};

describe("Data Transformers / Selectors", () => {
  describe("selectLogLevelDistribution", () => {
    it("should return empty array when stats is null", () => {
      expect(selectLogLevelDistribution(null)).toEqual([]);
    });

    it("should extract log levels mapping to Recharts data array format", () => {
      const res = selectLogLevelDistribution(mockStats);
      expect(res).toEqual([
        { name: "INFO", value: 6 },
        { name: "ERROR", value: 2 },
        { name: "WARN", value: 2 },
      ]);
    });
  });

  describe("selectTopIps", () => {
    it("should return empty array when stats is null", () => {
      expect(selectTopIps(null)).toEqual([]);
    });

    it("should extract client IP request rates directly from top_ips", () => {
      const res = selectTopIps(mockStats);
      expect(res).toEqual(mockStats.top_ips);
    });
  });

  describe("selectTopEndpoints", () => {
    it("should return empty array when stats is null", () => {
      expect(selectTopEndpoints(null)).toEqual([]);
    });

    it("should extract endpoint resource logs from top_endpoints", () => {
      const res = selectTopEndpoints(mockStats);
      expect(res).toEqual(mockStats.top_endpoints);
    });
  });
});
