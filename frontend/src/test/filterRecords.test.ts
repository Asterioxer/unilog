import { describe, it, expect } from "vitest";
import { filterRecords } from "../transformers/filterRecords";
import type { TableFilters } from "../types/filters";

describe("filterRecords pure transformer pipeline", () => {
  const mockRecords = [
    { timestamp: "2026-07-12T10:00:00Z", level: "INFO", status_code: 200, message: "OK request", path: "/index" },
    { timestamp: "2026-07-12T11:00:00Z", level: "ERROR", status_code: 500, message: "Failed database connection", path: "/db" },
    { timestamp: "2026-07-12T12:00:00Z", level: "WARN", status_code: 404, message: "Page not found", path: "/notfound" },
  ];

  const emptyFilters: TableFilters = {
    levels: [],
    statusCodes: [],
    dateRange: null,
    columnFilters: {},
  };

  it("should return all records when filters and search query are empty", () => {
    const result = filterRecords(mockRecords, emptyFilters, "");
    expect(result).toHaveLength(3);
  });

  it("should match global search query case-insensitively", () => {
    const result = filterRecords(mockRecords, emptyFilters, "DATABASE");
    expect(result).toHaveLength(1);
    expect(result[0].level).toBe("ERROR");
  });

  it("should match column-specific filters", () => {
    const filters = {
      ...emptyFilters,
      columnFilters: { path: "/db" },
    };
    const result = filterRecords(mockRecords, filters, "");
    expect(result).toHaveLength(1);
    expect(result[0].level).toBe("ERROR");
  });

  it("should filter by multi-select log severity levels", () => {
    const filters = {
      ...emptyFilters,
      levels: ["WARN", "ERROR"],
    };
    const result = filterRecords(mockRecords, filters, "");
    expect(result).toHaveLength(2);
    expect(result.some((r) => r.level === "INFO")).toBe(false);
  });

  it("should filter by multi-select status code ranges (2xx, 3xx, etc.)", () => {
    const filters = {
      ...emptyFilters,
      statusCodes: ["5xx", "4xx"],
    };
    const result = filterRecords(mockRecords, filters, "");
    expect(result).toHaveLength(2);
    expect(result.some((r) => r.status_code === 200)).toBe(false);
  });

  it("should filter by date ranges", () => {
    const filters = {
      ...emptyFilters,
      dateRange: {
        start: "2026-07-12T10:30:00Z",
        end: "2026-07-12T11:30:00Z",
      },
    };
    const result = filterRecords(mockRecords, filters, "");
    expect(result).toHaveLength(1);
    expect(result[0].level).toBe("ERROR");
  });
});
