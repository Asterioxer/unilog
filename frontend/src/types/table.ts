import type { TableFilters } from "./filters";

export interface SortState {
  key: string;
  direction: "asc" | "desc" | null;
}

export interface TablePreferences {
  visibleColumns: Record<string, boolean>;
  pageSize: number;
  sortState: SortState;
  filters: TableFilters;
}

export interface TableRowModel {
  id: string;
  record: Record<string, unknown>;
  expanded: boolean;
}
