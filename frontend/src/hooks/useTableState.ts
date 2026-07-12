import { useState, useMemo } from "react";
import type { TableFilters } from "../types/filters";
import type { SortState } from "../types/table";
import { filterRecords } from "../transformers/filterRecords";

const DEFAULT_FILTERS: TableFilters = {
  levels: [],
  statusCodes: [],
  dateRange: null,
  columnFilters: {},
};

export const useTableState = (
  records: Record<string, unknown>[],
  defaultVisibleColumns: Record<string, boolean> = {}
) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [sortConfig, setSortConfig] = useState<SortState>({ key: "", direction: null });
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  const [filters, setFilters] = useState<TableFilters>(DEFAULT_FILTERS);
  const [hiddenColumns, setHiddenColumns] = useState<Record<string, boolean>>({});

  // Derive visible columns dynamically during render
  const visibleColumns = useMemo(() => {
    const visible: Record<string, boolean> = {};
    // Visible by default if not present in defaultVisibleColumns
    Object.entries(defaultVisibleColumns).forEach(([k, v]) => {
      visible[k] = v;
    });

    records.forEach((r) => {
      Object.keys(r).forEach((k) => {
        if (visible[k] === undefined) {
          visible[k] = !hiddenColumns[k];
        } else {
          visible[k] = visible[k] && !hiddenColumns[k];
        }
      });
    });
    return visible;
  }, [records, hiddenColumns, defaultVisibleColumns]);

  const toggleColumnVisibility = (colId: string) => {
    setHiddenColumns((prev) => ({
      ...prev,
      [colId]: !prev[colId],
    }));
  };

  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  };

  const toggleRowExpanded = (id: string) => {
    setExpandedRows((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleSort = (key: string) => {
    let direction: "asc" | "desc" | null = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    } else if (sortConfig.key === key && sortConfig.direction === "desc") {
      direction = null;
    }
    setSortConfig({ key, direction });
  };

  const resetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setSearchQuery("");
    setCurrentPage(1);
  };

  // 1. Pipeline: Filter records using the pure transformer
  const filteredRecords = useMemo(() => {
    return filterRecords(records, filters, searchQuery);
  }, [records, filters, searchQuery]);

  // 2. Pipeline: Sort records
  const sortedRecords = useMemo(() => {
    if (!sortConfig.key || !sortConfig.direction) return filteredRecords;
    const { key, direction } = sortConfig;
    return [...filteredRecords].sort((a, b) => {
      const valA = a[key];
      const valB = b[key];
      if (valA === undefined || valA === null) return 1;
      if (valB === undefined || valB === null) return -1;

      if (typeof valA === "number" && typeof valB === "number") {
        return direction === "asc" ? valA - valB : valB - valA;
      }

      return direction === "asc"
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredRecords, sortConfig]);

  // 3. Pipeline: Paginate records
  const totalRows = sortedRecords.length;
  const totalPages = Math.ceil(totalRows / rowsPerPage);
  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * rowsPerPage;
    return sortedRecords.slice(start, start + rowsPerPage);
  }, [sortedRecords, currentPage, rowsPerPage]);

  return {
    searchQuery,
    setSearchQuery: handleSearchChange,
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
    sortedRecords,
    paginatedRecords,
  };
};
