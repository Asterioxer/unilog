import { render, screen, act, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LogsTable from "../pages/LogsTable";
import { apiService } from "../services/apiService";

describe("LogsTable page data table flows", () => {
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

  it("renders empty state initially when no logs are loaded", () => {
    render(<LogsTable />, { wrapper });
    expect(screen.getByText("No Log Records Loaded")).toBeInTheDocument();
  });

  it("loads and parses raw logs text, rendering rows, filters, sorting and exports", async () => {
    const parseSpy = vi.spyOn(apiService, "parseLog").mockResolvedValueOnce({
      total: 3,
      records: [
        { timestamp: "2026-07-11T12:00:00Z", level: "INFO", message: "User login succeeded", bytes_sent: 50 },
        { timestamp: "2026-07-11T12:01:00Z", level: "ERROR", message: "Db query timeout", bytes_sent: 20 },
        { timestamp: "2026-07-11T12:02:00Z", level: "WARN", message: "CPU load above threshold", bytes_sent: 10 }
      ]
    });

    render(<LogsTable />, { wrapper });

    const textarea = screen.getByPlaceholderText(/Paste log stream entries/i) as HTMLTextAreaElement;
    await act(async () => {
      fireEvent.change(textarea, { target: { value: "INFO User login...\nERROR Db query..." } });
    });

    const loadBtn = screen.getByText("Load Logs");
    await act(async () => {
      loadBtn.click();
    });

    await waitFor(() => {
      expect(screen.getByText("User login succeeded")).toBeInTheDocument();
    });

    // Check table headers
    expect(screen.getByText("Timestamp")).toBeInTheDocument();
    expect(screen.getByText("Message")).toBeInTheDocument();

    // Check sorting interaction (click level column header to sort desc/asc)
    const levelHeader = screen.getByText("Level");
    await act(async () => {
      levelHeader.click();
    });

    // Verify search filters query
    const searchInput = screen.getByPlaceholderText(/Search matching entries/i);
    await act(async () => {
      fireEvent.change(searchInput, { target: { value: "timeout" } });
    });

    expect(screen.getByText("Db query timeout")).toBeInTheDocument();
    expect(screen.queryByText("User login succeeded")).toBeNull();

    // Reset search
    await act(async () => {
      fireEvent.change(searchInput, { target: { value: "" } });
    });

    // Toggle columns dropdown visibility
    const colBtn = screen.getByText("Columns");
    await act(async () => {
      colBtn.click();
    });

    expect(screen.getByText("Toggle Columns")).toBeInTheDocument();

    // Click Level visibility toggle checkbox
    const levelToggleBtn = screen.getAllByRole("button").find(
      (btn) => btn.textContent?.includes("Level")
    );
    
    await act(async () => {
      levelToggleBtn?.click();
    });

    // Verify copy row details trigger
    // Mock navigator clipboard
    const clipboardSpy = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue();
    
    const copyBtns = screen.getAllByTitle("Copy Row JSON");
    await act(async () => {
      copyBtns[0].click();
    });

    expect(clipboardSpy).toHaveBeenCalled();

    // Verify exports click triggers
    const csvBtn = screen.getByText("CSV");
    const jsonBtn = screen.getByText("JSON");

    // Mock document.createElement to prevent downloads trigger in test environment
    const linkMock = {
      setAttribute: vi.fn(),
      click: vi.fn()
    };
    vi.spyOn(document, "createElement").mockReturnValue(linkMock as unknown as never);
    
    await act(async () => {
      csvBtn.click();
      jsonBtn.click();
    });

    expect(parseSpy).toHaveBeenCalled();
  });

  it("handles clearing the log database", async () => {
    vi.spyOn(apiService, "parseLog").mockResolvedValueOnce({
      total: 1,
      records: [{ level: "INFO", message: "Hello" }]
    });

    render(<LogsTable />, { wrapper });

    const textarea = screen.getByPlaceholderText(/Paste log stream entries/i) as HTMLTextAreaElement;
    await act(async () => {
      fireEvent.change(textarea, { target: { value: "INFO Hello" } });
    });

    const loadBtn = screen.getByText("Load Logs");
    await act(async () => {
      loadBtn.click();
    });

    await waitFor(() => {
      expect(screen.getByText("Hello")).toBeInTheDocument();
    });

    const clearBtn = screen.getByText("Clear Dataset");
    await act(async () => {
      clearBtn.click();
    });

    expect(screen.getByText("No Log Records Loaded")).toBeInTheDocument();
  });

  it("performs pagination page navigation and rows per page changes", async () => {
    // Generate 15 dummy records
    const dummyRecords = Array.from({ length: 15 }, (_, i) => ({
      timestamp: `2026-07-11T12:00:0${i}Z`,
      level: "INFO",
      message: `Message number ${i}`
    }));

    vi.spyOn(apiService, "parseLog").mockResolvedValueOnce({
      total: 15,
      records: dummyRecords
    });

    render(<LogsTable />, { wrapper });

    const textarea = screen.getByPlaceholderText(/Paste log stream entries/i) as HTMLTextAreaElement;
    await act(async () => {
      fireEvent.change(textarea, { target: { value: "INFO Hello" } });
    });

    const loadBtn = screen.getByText("Load Logs");
    await act(async () => {
      loadBtn.click();
    });

    await waitFor(() => {
      expect(screen.getByText("Message number 0")).toBeInTheDocument();
    });

    // Check pagination status: should say Page 1 of 2
    expect(screen.getByText("Page 1 of 2")).toBeInTheDocument();

    // Click next page button
    const nextBtn = document.querySelector(".lucide-chevron-right")?.parentElement as HTMLButtonElement;
    expect(nextBtn).toBeDefined();

    await act(async () => {
      nextBtn.click();
    });

    expect(screen.getByText("Page 2 of 2")).toBeInTheDocument();
    expect(screen.getByText("Message number 10")).toBeInTheDocument();

    // Click previous page button
    const prevBtn = document.querySelector(".lucide-chevron-left")?.parentElement as HTMLButtonElement;
    await act(async () => {
      prevBtn.click();
    });

    expect(screen.getByText("Page 1 of 2")).toBeInTheDocument();

    // Change rows per page selector
    const select = screen.getAllByRole("combobox")[1] as HTMLSelectElement;
    await act(async () => {
      fireEvent.change(select, { target: { value: "25" } });
    });

    expect(screen.getByText("Page 1 of 1")).toBeInTheDocument();
  });
});
