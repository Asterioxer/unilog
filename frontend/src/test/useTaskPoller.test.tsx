import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useTaskPoller } from "../hooks/useTaskPoller";
import { apiService } from "../services/apiService";

describe("useTaskPoller react query poller hook", () => {
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
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("does not run when taskId is null", () => {
    const { result } = renderHook(() => useTaskPoller(null), { wrapper });
    expect(result.current.isEnabled).toBe(false);
  });

  it("polls and fires onComplete when task completes", async () => {
    const getTaskSpy = vi
      .spyOn(apiService, "getTaskStatus")
      .mockResolvedValueOnce({
        status: "processing",
        filename: "test.log",
        result: null,
        error: null,
      })
      .mockResolvedValueOnce({
        status: "completed",
        filename: "test.log",
        result: { records: [], total: 0, format: "nginx" },
        error: null,
      });

    const onCompleteMock = vi.fn();
    const onFailureMock = vi.fn();

    const { result } = renderHook(
      () => useTaskPoller("task-123", onCompleteMock, onFailureMock),
      { wrapper }
    );

    // Initial status should be loading or processing
    await waitFor(() => {
      expect(result.current.data?.status).toBe("processing");
    });

    // Wait for the next poll to complete
    await waitFor(() => {
      expect(result.current.data?.status).toBe("completed");
    }, { timeout: 3000 });

    expect(onCompleteMock).toHaveBeenCalled();
    expect(onFailureMock).not.toHaveBeenCalled();
    expect(getTaskSpy).toHaveBeenCalledTimes(2);
  });

  it("fires onFailure when task fails", async () => {
    vi.spyOn(apiService, "getTaskStatus").mockResolvedValueOnce({
      status: "failed",
      filename: "test.log",
      result: null,
      error: "Malformed gzip header",
    });

    const onCompleteMock = vi.fn();
    const onFailureMock = vi.fn();

    renderHook(
      () => useTaskPoller("task-fail", onCompleteMock, onFailureMock),
      { wrapper }
    );

    await waitFor(() => {
      expect(onFailureMock).toHaveBeenCalledWith("Malformed gzip header");
    });

    expect(onCompleteMock).not.toHaveBeenCalled();
  });
});
