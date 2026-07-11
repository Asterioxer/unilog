import { render, screen, act, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "../pages/Dashboard";
import { apiService } from "../services/apiService";

const MOCK_DETECT_RESPONSE = {
  format: "nginx",
  confidence: 0.998,
  rankings: [
    { format: "nginx", confidence: 0.998 },
    { format: "apache", confidence: 0.01 },
  ],
  reason: "Pattern match heuristic"
};

const MOCK_STATS_RESPONSE = {
  format: "nginx",
  total_lines: 500,
  error_rate: 2.5,
  http_5xx_rate: null,
  time_range: ["2026-07-11T12:00:00Z", "2026-07-11T13:00:00Z"],
  top_ips: [
    { ip: "192.168.1.100", count: 350, percentage: 70 },
    { ip: "10.0.0.5", count: 150, percentage: 30 }
  ],
  log_levels: { INFO: 480, ERROR: 20 },
  top_endpoints: [
    { endpoint: "/api/v1/user", count: 400, percentage: 80 }
  ],
  bytes_transferred: 512000
};

describe("Dashboard page interactive metrics flows", () => {
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
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );

  it("handles empty validation warnings on analyze runs without inputs", async () => {
    render(<Dashboard />, { wrapper });
    
    const analyzeBtn = screen.getByText("Run Analytics");
    await act(async () => {
      analyzeBtn.click();
    });

    expect(
      screen.getByText("Please select or drop a log file first")
    ).toBeInTheDocument();
  });

  it("submits raw text paste for analysis and renders stats widgets", async () => {
    vi.spyOn(apiService, "generateStats").mockResolvedValueOnce(MOCK_STATS_RESPONSE);
    vi.spyOn(apiService, "detectFormat").mockResolvedValueOnce(MOCK_DETECT_RESPONSE);

    render(<Dashboard />, { wrapper });

    // Switch to paste tab
    const pasteTab = screen.getByText("Raw Text Dump");
    await act(async () => {
      pasteTab.click();
    });

    // Enter raw log text
    const textarea = screen.getByPlaceholderText(/Paste logs here/i) as HTMLTextAreaElement;
    await act(async () => {
      fireEvent.change(textarea, { target: { value: "192.168.1.100 - - ..." } });
    });

    expect(textarea.value).toBe("192.168.1.100 - - ...");

    // Run Analytics trigger
    const analyzeBtn = screen.getByText("Run Analytics");
    await act(async () => {
      analyzeBtn.click();
    });

    // Wait for mock data rendering assertions
    await waitFor(() => {
      expect(screen.getByText("Log Analytics Ready")).toBeInTheDocument();
    });

    // Format name displayed
    expect(screen.getByText("NGINX")).toBeInTheDocument();
    // AnimatedCounter renders values — check the counter testids exist
    const counters = screen.getAllByTestId("animated-counter");
    expect(counters.length).toBeGreaterThanOrEqual(2);
  });

  it("handles synchronous small file upload and displays analytics", async () => {
    const uploadSpy = vi.spyOn(apiService, "uploadFile").mockResolvedValueOnce({
      task_id: null,
      status: "completed",
      filename: "test.log",
      size: 1024,
      format: "nginx",
      records: []
    });

    vi.spyOn(apiService, "generateStats").mockResolvedValueOnce(MOCK_STATS_RESPONSE);
    vi.spyOn(apiService, "detectFormat").mockResolvedValueOnce(MOCK_DETECT_RESPONSE);

    render(<Dashboard />, { wrapper });

    // Find file input and simulate select
    const fileInput = document.querySelector("input[type='file']") as HTMLInputElement;
    const file = new File(["dummy nginx content"], "test.log", { type: "text/plain" });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    expect(screen.getByText("test.log")).toBeInTheDocument();

    const analyzeBtn = screen.getByText("Run Analytics");
    await act(async () => {
      analyzeBtn.click();
    });

    await waitFor(() => {
      expect(screen.getByText("Log Analytics Ready")).toBeInTheDocument();
    });

    expect(uploadSpy).toHaveBeenCalled();
  });

  it("handles asynchronous large file upload, polls status, and aggregates stats locally", async () => {
    const uploadSpy = vi.spyOn(apiService, "uploadFile").mockResolvedValueOnce({
      task_id: "async-task-999",
      status: "processing",
      filename: "large.log",
      size: 5242880,
      format: "auto",
      records: null
    });

    vi.spyOn(apiService, "detectFormat").mockResolvedValueOnce(MOCK_DETECT_RESPONSE);

    vi.spyOn(apiService, "getTaskStatus").mockResolvedValueOnce({
      status: "completed",
      filename: "large.log",
      result: {
        total: 10,
        records: [
          { level: "ERROR", client_ip: "127.0.0.1", path: "/admin", bytes_sent: 500 },
          { level: "INFO", client_ip: "127.0.0.1", path: "/index", bytes_sent: 200 }
        ]
      },
      error: null
    });

    render(<Dashboard />, { wrapper });

    const fileInput = document.querySelector("input[type='file']") as HTMLInputElement;
    const file = new File(["large file content mock"], "large.log", { type: "text/plain" });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    const analyzeBtn = screen.getByText("Run Analytics");
    await act(async () => {
      analyzeBtn.click();
    });

    // Wait for the async processing indicator and task completion callback
    await waitFor(() => {
      expect(screen.getByText("Log Analytics Ready")).toBeInTheDocument();
    }, { timeout: 3000 });

    // Check that animated counters rendered for the stats
    const counters = screen.getAllByTestId("animated-counter");
    expect(counters.length).toBeGreaterThanOrEqual(2);
    
    expect(uploadSpy).toHaveBeenCalled();
  });

  it("handles empty validation warnings on raw text analysis when empty", async () => {
    render(<Dashboard />, { wrapper });

    // Switch to paste tab
    const pasteTab = screen.getByText("Raw Text Dump");
    await act(async () => {
      pasteTab.click();
    });

    const analyzeBtn = screen.getByText("Run Analytics");
    await act(async () => {
      analyzeBtn.click();
    });

    expect(
      screen.getByText("Please paste some log text to analyze")
    ).toBeInTheDocument();
  });

  it("handles change log format select dropdown", async () => {
    vi.spyOn(apiService, "getFormats").mockResolvedValueOnce({
      formats: [
        { 
          name: "nginx", 
          description: "Nginx Access Log",
          priority: 1,
          supported_extensions: [".log"]
        }
      ]
    });

    render(<Dashboard />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Nginx Access Log/i)).toBeInTheDocument();
    });

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    await act(async () => {
      fireEvent.change(select, { target: { value: "nginx" } });
    });

    expect(select.value).toBe("nginx");
  });

  it("handles cancel upload action", async () => {
    vi.spyOn(apiService, "uploadFile").mockImplementation(() => {
      return new Promise(() => {}); // never resolves to simulate pending upload
    });

    render(<Dashboard />, { wrapper });

    const fileInput = document.querySelector("input[type='file']") as HTMLInputElement;
    const file = new File(["dummy"], "unilog.log", { type: "text/plain" });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    const analyzeBtn = screen.getByText("Run Analytics");
    await act(async () => {
      analyzeBtn.click();
    });

    // Cancel upload button should be visible inside UploadPanel
    const cancelBtn = screen.getByText("Cancel Upload");
    await act(async () => {
      cancelBtn.click();
    });

    expect(screen.getByText("Upload cancelled by user")).toBeInTheDocument();
  });
});
