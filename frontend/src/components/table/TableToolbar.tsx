import SearchBox from "./SearchBox";
import FiltersPanel from "./FiltersPanel";
import ColumnToggle from "./ColumnToggle";
import ExportActions from "./ExportActions";
import FilterChips from "./FilterChips";
import type { ColumnMeta } from "./columns";
import type { TableFilters } from "../../types/filters";

interface TableToolbarProps {
  searchQuery: string;
  onChangeSearch: (val: string) => void;
  filters: TableFilters;
  onChangeFilters: (filters: TableFilters) => void;
  onResetFilters: () => void;
  columns: ColumnMeta[];
  visibleColumns: Record<string, boolean>;
  onToggleColumn: (colId: string) => void;
  filteredRecords: Record<string, unknown>[];
}

export default function TableToolbar({
  searchQuery,
  onChangeSearch,
  filters,
  onChangeFilters,
  onResetFilters,
  columns,
  visibleColumns,
  onToggleColumn,
  filteredRecords,
}: TableToolbarProps) {
  return (
    <div className="flex flex-col border-b border-border bg-muted/20">
      <div className="p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <SearchBox value={searchQuery} onChange={onChangeSearch} />
          <FiltersPanel filters={filters} onChangeFilters={onChangeFilters} />
        </div>
        <div className="flex items-center gap-3">
          <ColumnToggle
            columns={columns}
            visibleColumns={visibleColumns}
            onToggleColumn={onToggleColumn}
          />
          <ExportActions
            filteredRecords={filteredRecords}
            columns={columns}
            visibleColumns={visibleColumns}
          />
        </div>
      </div>
      <FilterChips
        filters={filters}
        onChangeFilters={onChangeFilters}
        onResetAll={onResetFilters}
      />
    </div>
  );
}
