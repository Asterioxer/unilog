import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useTableState } from "../hooks/useTableState";

describe("useTableState custom hook", () => {
  const mockRecords = [
    { level: "INFO", message: "Success login", count: 10, status_code: 200 },
    { level: "ERROR", message: "Timeout failure", count: 2, status_code: 500 },
    { level: "WARN", message: "Disk usage high", count: 5, status_code: 404 },
  ];

  it("should initialize with default states", () => {
    const { result } = renderHook(() => useTableState(mockRecords));

    expect(result.current.searchQuery).toBe("");
    expect(result.current.currentPage).toBe(1);
    expect(result.current.rowsPerPage).toBe(10);
    expect(result.current.sortConfig).toEqual({ key: "", direction: null });
    expect(result.current.expandedRows).toEqual({});
    expect(result.current.filters).toEqual({
      levels: [],
      statusCodes: [],
      dateRange: null,
      columnFilters: {},
    });
    expect(result.current.totalRows).toBe(3);
    expect(result.current.paginatedRecords).toHaveLength(3);
  });

  it("should filter records based on search query case-insensitively", () => {
    const { result } = renderHook(() => useTableState(mockRecords));

    act(() => {
      result.current.setSearchQuery("timeout");
    });

    expect(result.current.searchQuery).toBe("timeout");
    expect(result.current.totalRows).toBe(1);
    expect(result.current.paginatedRecords[0].level).toBe("ERROR");
  });

  it("should filter records by log severity levels and status ranges", () => {
    const { result } = renderHook(() => useTableState(mockRecords));

    act(() => {
      result.current.setFilters({
        levels: ["ERROR", "WARN"],
        statusCodes: ["5xx"],
        dateRange: null,
        columnFilters: {},
      });
    });

    expect(result.current.totalRows).toBe(1);
    expect(result.current.paginatedRecords[0].level).toBe("ERROR");
  });

  it("should reset all filter configurations and page values on resetFilters click", () => {
    const { result } = renderHook(() => useTableState(mockRecords));

    act(() => {
      result.current.setSearchQuery("timeout");
      result.current.setFilters({
        levels: ["ERROR"],
        statusCodes: ["5xx"],
        dateRange: null,
        columnFilters: {},
      });
    });

    expect(result.current.totalRows).toBe(1);

    act(() => {
      result.current.resetFilters();
    });

    expect(result.current.searchQuery).toBe("");
    expect(result.current.filters.levels).toEqual([]);
    expect(result.current.totalRows).toBe(3);
  });

  it("should sort records numerically and alphabetically in both asc and desc direction", () => {
    const { result } = renderHook(() => useTableState(mockRecords));

    act(() => {
      result.current.handleSort("count");
    });
    expect(result.current.sortConfig).toEqual({ key: "count", direction: "asc" });
    expect(result.current.paginatedRecords[0].count).toBe(2);

    act(() => {
      result.current.handleSort("count");
    });
    expect(result.current.sortConfig).toEqual({ key: "count", direction: "desc" });
    expect(result.current.paginatedRecords[0].count).toBe(10);
  });

  it("should handle column visibility changes cleanly", () => {
    const { result } = renderHook(() => useTableState(mockRecords));

    act(() => {
      result.current.toggleColumnVisibility("count");
    });

    expect(result.current.visibleColumns.count).toBe(false);
  });
});
