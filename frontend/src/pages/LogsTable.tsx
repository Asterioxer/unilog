import { useState, useMemo, useRef } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { 
  Search, ArrowUpDown, ChevronLeft, ChevronRight, Copy, Download, SlidersHorizontal, CheckSquare, Square, Trash2, Code, RefreshCw
} from "lucide-react";
import { apiService } from "../services/apiService";
import { useKeyboardShortcut } from "../hooks/useKeyboardShortcut";
import type { FormatDetail } from "../types/api";

type SortConfig = {
  key: string;
  direction: "asc" | "desc" | null;
};

export default function LogsTable() {
  const [logText, setLogText] = useState("");
  const [selectedFormat, setSelectedFormat] = useState("auto");
  const [records, setRecords] = useState<Record<string, unknown>[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: "", direction: null });
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);

  useKeyboardShortcut(
    { key: "k", ctrlKey: true },
    (e) => {
      e.preventDefault();
      searchInputRef.current?.focus();
    }
  );

  // Column visibility states
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>({
    timestamp: true,
    level: true,
    ip: true,
    method: true,
    path: true,
    status_code: true,
    bytes_sent: true,
    message: true,
  });
  const [showColumnDropdown, setShowColumnDropdown] = useState(false);

  // Fetch registered formats
  const { data: formatsData } = useQuery({
    queryKey: ["formats"],
    queryFn: () => apiService.getFormats(),
    initialData: { formats: [] }
  });

  // Log parser mutation
  const parseLogsMutation = useMutation({
    mutationFn: () => apiService.parseLog(logText, selectedFormat === "auto" ? undefined : selectedFormat),
    onSuccess: (data) => {
      setRecords(data.records);
      setCurrentPage(1);
      setToastMessage(`Successfully parsed ${data.total} records`);
      setTimeout(() => setToastMessage(null), 3000);
    },
    onError: (err: unknown) => {
      const apiError = err as { message?: string };
      setToastMessage(`Parsing failed: ${apiError.message || "Unknown error"}`);
      setTimeout(() => setToastMessage(null), 4000);
    }
  });

  const handleParse = () => {
    if (!logText.trim()) return;
    parseLogsMutation.mutate();
  };

  const handleClear = () => {
    setRecords([]);
    setLogText("");
    setSearchQuery("");
  };

  // Dynamically extract all possible keys from records to form columns
  const allKeys = useMemo(() => {
    const keys = new Set<string>();
    records.forEach((r) => {
      Object.keys(r).forEach((k) => keys.add(k));
    });
    return Array.from(keys);
  }, [records]);

  // Filter columns based on visibility preferences
  const activeColumns = useMemo(() => {
    return allKeys.filter((key) => {
      // Check normalized visibility mapping
      if (key.includes("level")) return visibleColumns.level;
      if (key.includes("ip")) return visibleColumns.ip;
      if (key.includes("status")) return visibleColumns.status_code;
      if (key.includes("bytes")) return visibleColumns.bytes_sent;
      if (visibleColumns[key] !== undefined) return visibleColumns[key];
      return true; // Show extra custom fields by default
    });
  }, [allKeys, visibleColumns]);

  // Filter & Search records
  const filteredRecords = useMemo(() => {
    if (!searchQuery) return records;
    const query = searchQuery.toLowerCase();
    return records.filter((r) => {
      return Object.values(r).some((val) => 
        String(val).toLowerCase().includes(query)
      );
    });
  }, [records, searchQuery]);

  // Sort config handler
  const handleSort = (key: string) => {
    let direction: "asc" | "desc" | null = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    } else if (sortConfig.key === key && sortConfig.direction === "desc") {
      direction = null;
    }
    setSortConfig({ key, direction });
  };

  // Sort records
  const sortedRecords = useMemo(() => {
    if (!sortConfig.key || !sortConfig.direction) return filteredRecords;
    const { key, direction } = sortConfig;
    const sorted = [...filteredRecords].sort((a, b) => {
      const valA = a[key];
      const valB = b[key];
      if (valA === undefined) return 1;
      if (valB === undefined) return -1;

      // Handle numerical sort
      if (typeof valA === "number" && typeof valB === "number") {
        return direction === "asc" ? valA - valB : valB - valA;
      }
      // String sort
      return direction === "asc"
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
    return sorted;
  }, [filteredRecords, sortConfig]);

  // Pagination calculations
  const totalRows = sortedRecords.length;
  const totalPages = Math.ceil(totalRows / rowsPerPage);
  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * rowsPerPage;
    return sortedRecords.slice(start, start + rowsPerPage);
  }, [sortedRecords, currentPage, rowsPerPage]);

  // Copy row to clipboard helper
  const handleCopyRow = (row: Record<string, unknown>) => {
    navigator.clipboard.writeText(JSON.stringify(row, null, 2));
    setToastMessage("Copied row details as JSON");
    setTimeout(() => setToastMessage(null), 2000);
  };

  // Export actions: CSV
  const handleExportCSV = () => {
    if (records.length === 0) return;
    const headers = allKeys.join(",");
    const csvRows = sortedRecords.map((r) => 
      allKeys.map((key) => {
        const val = r[key];
        const str = val === undefined ? "" : String(val);
        return `"${str.replace(/"/g, '""')}"`;
      }).join(",")
    );
    const csvContent = [headers, ...csvRows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "unilog_export.csv");
    link.click();
  };

  // Export actions: JSON
  const handleExportJSON = () => {
    if (records.length === 0) return;
    const jsonContent = JSON.stringify(sortedRecords, null, 2);
    const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "unilog_export.json");
    link.click();
  };

  const toggleColumnVisibility = (col: string) => {
    setVisibleColumns((prev) => ({
      ...prev,
      [col]: !prev[col]
    }));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Advanced Log Explorer</h1>
        <p className="text-muted-foreground">
          Perform strict column filtering, search queries, pagination, and data export on log entries.
        </p>
      </div>

      {/* Toast Alert popup */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 bg-primary text-primary-foreground px-4 py-3 rounded-lg shadow-lg z-50 text-sm flex items-center gap-2 animate-bounce">
          <Code className="h-4 w-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Input Parser Dump Section */}
      <div className="border border-border bg-card rounded-xl p-5 shadow-xs space-y-4">
        <textarea
          value={logText}
          onChange={(e) => setLogText(e.target.value)}
          placeholder="Paste log stream entries to explorer database table..."
          rows={3}
          className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:outline-hidden focus:ring-1 focus:ring-primary"
        />
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value)}
              className="rounded-lg border border-border bg-background px-3 py-2 text-sm focus:ring-1 focus:ring-primary"
            >
              <option value="auto">Auto-Detect</option>
              {formatsData.formats.map((f: FormatDetail) => (
                <option key={f.name} value={f.name}>
                  {f.description}
                </option>
              ))}
            </select>
            <button
              onClick={handleParse}
              disabled={parseLogsMutation.isPending || !logText.trim()}
              className="px-5 py-2 bg-primary text-primary-foreground rounded-lg font-semibold text-sm hover:bg-primary/95 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {parseLogsMutation.isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : null}
              Load Logs
            </button>
          </div>
          {records.length > 0 && (
            <button
              onClick={handleClear}
              className="px-4 py-2 border border-destructive/20 text-destructive bg-destructive/5 hover:bg-destructive/10 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Clear Dataset
            </button>
          )}
        </div>
      </div>

      {records.length > 0 ? (
        <div className="border border-border bg-card rounded-xl shadow-xs overflow-hidden flex flex-col">
          {/* Table Toolbar */}
          <div className="p-4 border-b border-border flex flex-wrap items-center justify-between gap-4 bg-muted/30">
            {/* Search */}
            <div className="relative min-w-[280px]">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search matching entries..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="pl-9 pr-4 py-2 w-full rounded-lg border border-border bg-background text-sm focus:ring-1 focus:ring-primary"
              />
            </div>

            {/* Actions & Exporters */}
            <div className="flex items-center gap-3 relative">
              {/* Column selector dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowColumnDropdown(!showColumnDropdown)}
                  className="px-3.5 py-2 border border-border bg-background rounded-lg text-sm font-medium hover:bg-muted transition-colors flex items-center gap-2"
                >
                  <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
                  Columns
                </button>
                {showColumnDropdown && (
                  <div className="absolute right-0 mt-2 w-56 border border-border bg-card rounded-xl shadow-lg z-50 p-2 text-sm flex flex-col gap-1.5">
                    <span className="font-semibold text-xs text-muted-foreground uppercase px-2 py-1 tracking-wider">
                      Toggle Columns
                    </span>
                    {Object.keys(visibleColumns).map((col) => (
                      <button
                        key={col}
                        onClick={() => toggleColumnVisibility(col)}
                        className="flex items-center gap-2.5 w-full text-left px-2 py-1.5 rounded-lg hover:bg-muted transition-colors"
                      >
                        {visibleColumns[col] ? (
                          <CheckSquare className="h-4 w-4 text-primary" />
                        ) : (
                          <Square className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="capitalize">{col.replace("_", " ")}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* CSV Exporter */}
              <button
                onClick={handleExportCSV}
                className="px-3.5 py-2 border border-border bg-background rounded-lg text-sm font-medium hover:bg-muted transition-colors flex items-center gap-2"
              >
                <Download className="h-4 w-4 text-muted-foreground" />
                CSV
              </button>

              {/* JSON Exporter */}
              <button
                onClick={handleExportJSON}
                className="px-3.5 py-2 border border-border bg-background rounded-lg text-sm font-medium hover:bg-muted transition-colors flex items-center gap-2"
              >
                <Download className="h-4 w-4 text-muted-foreground" />
                JSON
              </button>
            </div>
          </div>

          {/* Interactive Data Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead className="border-b border-border bg-muted/20 font-semibold text-muted-foreground">
                <tr>
                  {activeColumns.map((col) => (
                    <th
                      key={col}
                      onClick={() => handleSort(col)}
                      className="px-4 py-3 cursor-pointer select-none hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-1.5">
                        <span className="capitalize">
                          {col.charAt(0).toUpperCase() + col.slice(1).replace("_", " ")}
                        </span>
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                  ))}
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {paginatedRecords.length > 0 ? (
                  paginatedRecords.map((row, idx) => (
                    <tr 
                      key={idx} 
                      className="hover:bg-muted/30 transition-colors group"
                    >
                      {activeColumns.map((col) => (
                        <td key={col} className="px-4 py-3 font-mono text-xs max-w-[240px] truncate">
                          {row[col] !== undefined ? String(row[col]) : "-"}
                        </td>
                      ))}
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleCopyRow(row)}
                          className="p-1.5 hover:bg-muted rounded-md text-muted-foreground hover:text-foreground transition-colors inline-flex items-center"
                          title="Copy Row JSON"
                        >
                          <Copy className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td 
                      colSpan={activeColumns.length + 1} 
                      className="px-6 py-12 text-center text-muted-foreground"
                    >
                      No entries match the active search filter query.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Table Pagination Footer */}
          <div className="p-4 border-t border-border flex flex-wrap items-center justify-between gap-4 bg-muted/10 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <span>Rows per page</span>
              <select
                value={rowsPerPage}
                onChange={(e) => {
                  setRowsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="border border-border rounded-md bg-background px-2 py-1 text-xs focus:ring-1 focus:ring-primary"
              >
                {[10, 25, 50, 100].map((num) => (
                  <option key={num} value={num}>
                    {num}
                  </option>
                ))}
              </select>
              <span>
                Showing {totalRows > 0 ? (currentPage - 1) * rowsPerPage + 1 : 0} to{" "}
                {Math.min(currentPage * rowsPerPage, totalRows)} of {totalRows}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1.5 border border-border bg-background rounded-lg hover:bg-muted transition-colors disabled:opacity-40 disabled:pointer-events-none"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="px-3 py-1 font-semibold text-foreground bg-muted rounded-md text-xs">
                Page {currentPage} of {totalPages || 1}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages || totalPages === 0}
                className="p-1.5 border border-border bg-background rounded-lg hover:bg-muted transition-colors disabled:opacity-40 disabled:pointer-events-none"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="border border-border bg-card rounded-xl p-12 text-center max-w-xl mx-auto shadow-xs flex flex-col items-center gap-4">
          <SlidersHorizontal className="h-12 w-12 text-muted-foreground/30" />
          <h2 className="text-xl font-bold tracking-tight">No Log Records Loaded</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Please paste log text entries inside the parser input box above to load dynamic rows into the data table explorer.
          </p>
        </div>
      )}
    </div>
  );
}
