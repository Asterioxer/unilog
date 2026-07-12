import React from "react";
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DashboardProvider } from "../context/DashboardContext";
import { useDashboardActions } from "../hooks/useDashboardActions";
import { apiService } from "../services/apiService";

describe("useDashboardActions Hook", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    vi.restoreAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <DashboardProvider>{children}</DashboardProvider>
    </QueryClientProvider>
  );

  it("should initialize with default states", () => {
    const { result } = renderHook(() => useDashboardActions(), { wrapper });
    expect(result.current.state.status).toBe("idle");
    expect(result.current.state.ui.activeTab).toBe("file");
    expect(result.current.state.ui.selectedFormat).toBe("auto");
    expect(result.current.state.ui.logText).toBe("");
  });

  it("should update tab selection, selected format and log text input", () => {
    const { result } = renderHook(() => useDashboardActions(), { wrapper });

    act(() => {
      result.current.setActiveTab("paste");
    });
    expect(result.current.state.ui.activeTab).toBe("paste");

    act(() => {
      result.current.setSelectedFormat("nginx");
    });
    expect(result.current.state.ui.selectedFormat).toBe("nginx");

    act(() => {
      result.current.setLogText("mock log text entry");
    });
    expect(result.current.state.ui.logText).toBe("mock log text entry");
  });

  it("should perform optimistic reset and run stats & detect mutations in paste mode", async () => {
    const mockStatsResponse = {
      format: "nginx",
      total_lines: 1,
      error_rate: 0,
      http_5xx_rate: 0,
      time_range: null,
      top_ips: [],
      log_levels: {},
      top_endpoints: [],
      bytes_transferred: 0,
    };

    const mockDetectResponse = {
      format: "nginx",
      confidence: 1.0,
      rankings: [{ format: "nginx", confidence: 1.0 }],
      reason: "Matched Nginx format",
    };

    vi.spyOn(apiService, "generateStats").mockResolvedValue(mockStatsResponse);
    vi.spyOn(apiService, "detectFormat").mockResolvedValue(mockDetectResponse);

    const { result } = renderHook(() => useDashboardActions(), { wrapper });

    act(() => {
      result.current.setActiveTab("paste");
      result.current.setLogText("127.0.0.1 - - [10/Jul/2026:20:53:59 +0530] \"GET /api HTTP/1.1\" 200 456");
    });

    let promise: Promise<void>;
    act(() => {
      promise = result.current.handleAnalyze(null);
    });

    // Check optimistic reset state during execution
    expect(result.current.state.status).toBe("processing");
    expect(result.current.state.metadata.filename).toBe("Pasted Dump");

    await act(async () => {
      await promise;
    });

    // Confirm state has updated successfully
    expect(result.current.state.status).toBe("ready");
    expect(result.current.state.analysis.stats).toEqual(mockStatsResponse);
    expect(result.current.state.analysis.detect).toEqual(mockDetectResponse);
  });

  it("should trigger validation warning if paste input is empty", async () => {
    const { result } = renderHook(() => useDashboardActions(), { wrapper });

    act(() => {
      result.current.setActiveTab("paste");
      result.current.setLogText("   ");
    });

    await act(async () => {
      await result.current.handleAnalyze(null);
    });

    expect(result.current.state.status).toBe("error");
    expect(result.current.state.ui.error?.title).toBe("Validation Error");
  });
});
