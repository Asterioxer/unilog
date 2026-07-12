import { useState, useMemo, Fragment } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2, Code, RefreshCw } from "lucide-react";
import { apiService } from "../services/apiService";
import { queryKeys } from "../services/queryKeys";
import { useTableState } from "../hooks/useTableState";
import { buildRecordId } from "../utils/recordIdentity";
import {
  Header,
  Row,
  ExpandedRow,
  Pagination,
  TableToolbar,
  buildColumnsMeta,
} from "../components/table";
import type { FormatDetail } from "../types/api";

const EMPTY_RECORDS: Record<string, unknown>[] = [];

export default function LogsTable() {
  const [logText, setLogText] = useState("");
  const [selectedFormat, setSelectedFormat] = useState("auto");
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [focusedRowId, setFocusedRowId] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // 1. Reactive query to read parsed records from central React Query cache
  const { data: recordsData } = useQuery<Record<string, unknown>[] | null>({
    queryKey: queryKeys.records,
    queryFn: () => null,
    staleTime: Infinity,
    gcTime: Infinity,
    initialData: null,
  });

  const records = recordsData || EMPTY_RECORDS;

  // Fetch registered formats
  const { data: formatsData } = useQuery({
    queryKey: queryKeys.formats,
    queryFn: () => apiService.getFormats(),
    initialData: { formats: [] },
  });

  // Log parser mutation syncing raw parsed outputs directly to queryCache
  const parseLogsMutation = useMutation({
    mutationFn: () =>
      apiService.parseLog(
        logText,
        selectedFormat === "auto" ? undefined : selectedFormat
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.records, data.records);
      setToastMessage(`Successfully parsed ${data.total} records`);
      setTimeout(() => setToastMessage(null), 3000);
    },
    onError: (err: unknown) => {
      const apiError = err as { message?: string };
      setToastMessage(`Parsing failed: ${apiError.message || "Unknown error"}`);
      setTimeout(() => setToastMessage(null), 4000);
    },
  });

  const handleParse = () => {
    if (!logText.trim()) return;
    parseLogsMutation.mutate();
  };

  const handleClear = () => {
    queryClient.setQueryData(queryKeys.records, null);
    setLogText("");
  };

  // 2. Build column metadata dynamically using built-in plus dynamic record keys
  const columns = useMemo(() => buildColumnsMeta(records), [records]);

  // 3. Coordinate table visual states (paging, sorting, search, visibility)
  const {
    searchQuery,
    setSearchQuery,
    currentPage,
    setCurrentPage,
    rowsPerPage,
    setRowsPerPage,
    sortConfig,
    handleSort,
    expandedRows,
    toggleRowExpanded,
    filters,
    setFilters,
    resetFilters,
    visibleColumns,
    toggleColumnVisibility,
    totalRows,
    totalPages,
    filteredRecords,
    paginatedRecords,
  } = useTableState(records);

  // Map rows to stable IDs for roving tabIndex key matching
  const paginatedRowIds = useMemo(
    () => paginatedRecords.map((row, idx) => buildRecordId(row, idx)),
    [paginatedRecords]
  );

  // Derive active roving tab index focus ID dynamically
  const activeRowId = useMemo(() => {
    if (paginatedRowIds.length === 0) return null;
    if (focusedRowId && paginatedRowIds.includes(focusedRowId)) {
      return focusedRowId;
    }
    return paginatedRowIds[0];
  }, [paginatedRowIds, focusedRowId]);

  // Rove selection handlers
  const handleRowKeyDown = (
    e: React.KeyboardEvent<HTMLTableRowElement>,
    rowId: string
  ) => {
    const currentIndex = paginatedRowIds.indexOf(rowId);
    if (currentIndex === -1) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        if (currentIndex < paginatedRowIds.length - 1) {
          setFocusedRowId(paginatedRowIds[currentIndex + 1]);
        }
        break;
      case "ArrowUp":
        e.preventDefault();
        if (currentIndex > 0) {
          setFocusedRowId(paginatedRowIds[currentIndex - 1]);
        }
        break;
      case "Home":
        e.preventDefault();
        if (paginatedRowIds.length > 0) {
          setFocusedRowId(paginatedRowIds[0]);
        }
        break;
      case "End":
        e.preventDefault();
        if (paginatedRowIds.length > 0) {
          setFocusedRowId(paginatedRowIds[paginatedRowIds.length - 1]);
        }
        break;
      case "PageDown":
        e.preventDefault();
        setFocusedRowId(
          paginatedRowIds[Math.min(currentIndex + 5, paginatedRowIds.length - 1)]
        );
        break;
      case "PageUp":
        e.preventDefault();
        setFocusedRowId(paginatedRowIds[Math.max(currentIndex - 5, 0)]);
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        toggleRowExpanded(rowId);
        break;
      case "Escape":
        e.preventDefault();
        if (expandedRows[rowId]) {
          toggleRowExpanded(rowId);
        }
        break;
      default:
        break;
    }
  };

  // Only render columns that are configured visible in preference state
  const visibleColumnsMeta = useMemo(
    () => columns.filter((col) => visibleColumns[col.id] !== false),
    [columns, visibleColumns]
  );

  const handleCopyRow = (row: Record<string, unknown>) => {
    navigator.clipboard.writeText(JSON.stringify(row, null, 2));
    setToastMessage("Copied row details as JSON");
    setTimeout(() => setToastMessage(null), 2000);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Advanced Log Explorer</h1>
        <p className="text-muted-foreground text-sm">
          Explore structures, expand row JSON records, and query timelines across active parser streams.
        </p>
      </div>

      {toastMessage && (
        <div className="fixed bottom-4 right-4 bg-primary text-primary-foreground px-4 py-3 rounded-lg shadow-lg z-50 text-sm flex items-center gap-2 animate-bounce">
          <Code className="h-4 w-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Input Parser Area */}
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
              {parseLogsMutation.isPending ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : null}
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
          {/* Table Unified Toolbar */}
          <TableToolbar
            searchQuery={searchQuery}
            onChangeSearch={setSearchQuery}
            filters={filters}
            onChangeFilters={setFilters}
            onResetFilters={resetFilters}
            columns={columns}
            visibleColumns={visibleColumns}
            onToggleColumn={toggleColumnVisibility}
            filteredRecords={filteredRecords}
          />

          {/* Sticky Table Body Viewport */}
          <div className="max-h-[70vh] overflow-auto scrollbar-thin">
            <table className="w-full text-left border-collapse text-sm">
              <Header
                columns={visibleColumnsMeta}
                sortConfig={sortConfig}
                onSort={handleSort}
              />
              <tbody className="divide-y divide-border">
                {paginatedRecords.length > 0 ? (
                  paginatedRecords.map((row, idx) => {
                    const rowId = paginatedRowIds[idx];
                    const isExpanded = !!expandedRows[rowId];
                    const isFocused = activeRowId === rowId;

                    return (
                      <Fragment key={rowId}>
                        <Row
                          row={row}
                          columns={visibleColumnsMeta}
                          expanded={isExpanded}
                          onToggleExpand={() => toggleRowExpanded(rowId)}
                          query={searchQuery}
                          onCopyRow={() => handleCopyRow(row)}
                          isFocused={isFocused}
                          onKeyDown={(e) => handleRowKeyDown(e, rowId)}
                        />
                        {isExpanded && (
                          <ExpandedRow
                            row={row}
                            colSpan={visibleColumnsMeta.length + 2} // columns + expand spacer + actions
                          />
                        )}
                      </Fragment>
                    );
                  })
                ) : (
                  <tr>
                    <td
                      colSpan={visibleColumnsMeta.length + 2}
                      className="px-6 py-12 text-center text-muted-foreground space-y-3"
                    >
                      <p className="text-sm font-medium">
                        No records match the current filters.
                      </p>
                      <button
                        onClick={resetFilters}
                        className="px-3.5 py-1.5 bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 text-xs font-semibold rounded-md transition-colors"
                      >
                        Clear Filters
                      </button>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            rowsPerPage={rowsPerPage}
            totalRows={totalRows}
            setCurrentPage={setCurrentPage}
            setRowsPerPage={setRowsPerPage}
          />
        </div>
      ) : (
        <div className="border border-border bg-card rounded-xl p-12 text-center max-w-xl mx-auto shadow-xs flex flex-col items-center gap-4">
          <Trash2 className="h-12 w-12 text-muted-foreground/30" />
          <h2 className="text-xl font-bold tracking-tight">No Log Records Loaded</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Please paste log text entries inside the parser input box above to load dynamic rows into the data table explorer.
          </p>
        </div>
      )}
    </div>
  );
}
