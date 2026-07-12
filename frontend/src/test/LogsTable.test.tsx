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

  it("loads and parses raw logs, checking filter panel, column toggles, and exports", async () => {
    const parseSpy = vi.spyOn(apiService, "parseLog").mockResolvedValueOnce({
      total: 3,
      records: [
        { timestamp: "2026-07-11T12:00:00Z", level: "INFO", message: "User login succeeded", bytes_sent: 50, status_code: 200 },
        { timestamp: "2026-07-11T12:01:00Z", level: "ERROR", message: "Db query timeout", bytes_sent: 20, status_code: 500 },
        { timestamp: "2026-07-11T12:02:00Z", level: "WARN", message: "CPU load above threshold", bytes_sent: 10, status_code: 404 }
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

    // Check filters panel toggle
    const filterBtn = screen.getByTitle("Toggle Filter Parameters Panel");
    await act(async () => {
      filterBtn.click();
    });

    // Toggle ERROR severity level filter
    const errorLevelBtn = screen.getAllByText("ERROR").find((el) => el.tagName === "BUTTON")!;
    await act(async () => {
      errorLevelBtn.click();
    });

    // Verify filter chip is displayed and filtered output is shown
    expect(screen.getByText("Db query timeout")).toBeInTheDocument();
    expect(screen.queryByText("User login succeeded")).toBeNull();

    // Check Column toggle popover
    const columnToggleBtn = screen.getByTitle("Toggle Column Visibility");
    await act(async () => {
      columnToggleBtn.click();
    });
    expect(screen.getByText("Toggle Columns")).toBeInTheDocument();

    // Verify copy row details trigger
    const clipboardSpy = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue();
    const copyBtns = screen.getAllByTitle("Copy Row JSON");
    await act(async () => {
      copyBtns[0].click();
    });
    expect(clipboardSpy).toHaveBeenCalled();

    // Verify exports
    const csvBtn = screen.getByText("CSV");
    const jsonBtn = screen.getByText("JSON");
    const linkMock = {
      setAttribute: vi.fn(),
      click: vi.fn()
    };
    vi.spyOn(document, "createElement").mockReturnValue(linkMock as unknown as never);
    
    await act(async () => {
      csvBtn.click();
      jsonBtn.click();
    });

    expect(linkMock.click).toHaveBeenCalled();
    expect(parseSpy).toHaveBeenCalled();
  });

  it("handles keyboard roving focus and expand/collapse key triggers", async () => {
    vi.spyOn(apiService, "parseLog").mockResolvedValueOnce({
      total: 2,
      records: [
        { timestamp: "2026-07-11T12:00:00Z", level: "INFO", message: "Row 1", raw: "raw row 1" },
        { timestamp: "2026-07-11T12:01:00Z", level: "ERROR", message: "Row 2", raw: "raw row 2" }
      ]
    });

    render(<LogsTable />, { wrapper });

    const textarea = screen.getByPlaceholderText(/Paste log stream entries/i) as HTMLTextAreaElement;
    await act(async () => {
      fireEvent.change(textarea, { target: { value: "INFO Row 1\nERROR Row 2" } });
    });

    const loadBtn = screen.getByText("Load Logs");
    await act(async () => {
      loadBtn.click();
    });

    await waitFor(() => {
      expect(screen.getByText("Row 1")).toBeInTheDocument();
    });

    // Check table rows
    const rows = screen.getAllByRole("row");
    // header row is rows[0], data row 1 is rows[1]
    const row1 = rows[1];
    
    // Focus the first row
    row1.focus();
    expect(document.activeElement).toBe(row1);

    // Simulate Down Arrow key to focus next row
    await act(async () => {
      fireEvent.keyDown(row1, { key: "ArrowDown" });
    });

    const row2 = rows[2];
    expect(document.activeElement).toBe(row2);

    // Press Space to toggle expansion
    await act(async () => {
      fireEvent.keyDown(row2, { key: " " });
    });

    // Check that detail block matches raw output
    expect(screen.getByText("Raw Log Record")).toBeInTheDocument();
    expect(screen.getByText("raw row 2")).toBeInTheDocument();
  });

  it("performs pagination page navigation and rows per page changes", async () => {
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
    act(() => {
      loadBtn.click();
    });

    await waitFor(() => {
      expect(screen.getByText("Message number 0")).toBeInTheDocument();
    });

    expect(screen.getByText("Page 1 of 2")).toBeInTheDocument();

    const nextBtn = screen.getByLabelText("Next Page");
    await act(async () => {
      nextBtn.click();
    });

    expect(screen.getByText("Page 2 of 2")).toBeInTheDocument();
    expect(screen.getByText("Message number 10")).toBeInTheDocument();

    const prevBtn = screen.getByLabelText("Previous Page");
    await act(async () => {
      prevBtn.click();
    });

    expect(screen.getByText("Page 1 of 2")).toBeInTheDocument();
  });
});
