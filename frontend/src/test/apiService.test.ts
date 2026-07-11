import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiService } from "../services/apiService";
import { apiClient } from "../services/apiClient";

describe("apiService integration wrappers", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("checks liveness check route", async () => {
    const mockRes = { status: "live" };
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({ data: mockRes } as unknown as never);

    const data = await apiService.checkLiveness();
    expect(data).toEqual(mockRes);
    expect(getSpy).toHaveBeenCalledWith("/live");
  });

  it("checks readiness check route", async () => {
    const mockRes = { status: "ready" };
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({ data: mockRes } as unknown as never);

    const data = await apiService.checkReadiness();
    expect(data).toEqual(mockRes);
    expect(getSpy).toHaveBeenCalledWith("/ready");
  });

  it("calls formats log schemas catalog", async () => {
    const mockRes = { formats: [] };
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({ data: mockRes } as unknown as never);

    const data = await apiService.getFormats();
    expect(data).toEqual(mockRes);
    expect(postSpy).toHaveBeenCalledWith("/api/v1/formats");
  });

  it("calls log format heuristic detector", async () => {
    const mockRes = { format: "nginx", confidence: 1.0 };
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({ data: mockRes } as unknown as never);

    const data = await apiService.detectFormat("test log");
    expect(data).toEqual(mockRes);
    expect(postSpy).toHaveBeenCalledWith("/api/v1/detect", { log_text: "test log" });
  });

  it("calls parse log log text parser", async () => {
    const mockRes = { records: [], total: 0 };
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({ data: mockRes } as unknown as never);

    const data = await apiService.parseLog("log lines", "nginx");
    expect(data).toEqual(mockRes);
    expect(postSpy).toHaveBeenCalledWith("/api/v1/parse", { log_text: "log lines", format: "nginx" });
  });

  it("calls generateStats metrics processor", async () => {
    const mockRes = { total_lines: 0 };
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({ data: mockRes } as unknown as never);

    const data = await apiService.generateStats("log lines", "nginx");
    expect(data).toEqual(mockRes);
    expect(postSpy).toHaveBeenCalledWith("/api/v1/stats", { log_text: "log lines", format: "nginx" });
  });

  it("calls uploadFile file upload utility", async () => {
    const mockRes = { status: "completed" };
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({ data: mockRes } as unknown as never);

    const file = new File(["foo"], "access.log", { type: "text/plain" });
    const data = await apiService.uploadFile(file, "nginx");
    expect(data).toEqual(mockRes);
    
    // Assert FormData values
    expect(postSpy).toHaveBeenCalledWith(
      "/api/v1/upload",
      expect.any(FormData),
      expect.any(Object)
    );
  });

  it("calls getTaskStatus polling route", async () => {
    const mockRes = { status: "processing" };
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce({ data: mockRes } as unknown as never);

    const data = await apiService.getTaskStatus("task-123");
    expect(data).toEqual(mockRes);
    expect(getSpy).toHaveBeenCalledWith("/api/v1/tasks/task-123");
  });
});
