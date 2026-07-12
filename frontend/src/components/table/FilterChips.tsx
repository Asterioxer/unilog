import { X, RotateCcw } from "lucide-react";
import type { TableFilters } from "../../types/filters";

interface FilterChipsProps {
  filters: TableFilters;
  onChangeFilters: (filters: TableFilters) => void;
  onResetAll: () => void;
}

export default function FilterChips({
  filters,
  onChangeFilters,
  onResetAll,
}: FilterChipsProps) {
  const handleRemoveLevel = (lvl: string) => {
    onChangeFilters({
      ...filters,
      levels: filters.levels.filter((l) => l !== lvl),
    });
  };

  const handleRemoveStatus = (sc: string) => {
    onChangeFilters({
      ...filters,
      statusCodes: filters.statusCodes.filter((s) => s !== sc),
    });
  };

  const handleRemoveDateRange = () => {
    onChangeFilters({
      ...filters,
      dateRange: null,
    });
  };

  const hasActiveFilters =
    filters.levels.length > 0 ||
    filters.statusCodes.length > 0 ||
    filters.dateRange !== null;

  if (!hasActiveFilters) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 py-2 px-4 border-t border-border/40 bg-muted/10 text-xs">
      <span className="font-semibold text-muted-foreground uppercase text-[9px] tracking-wider mr-1">
        Active Filters:
      </span>

      {filters.levels.map((lvl) => (
        <span
          key={lvl}
          className="inline-flex items-center gap-1 bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full font-semibold"
        >
          <span>{lvl}</span>
          <button
            onClick={() => handleRemoveLevel(lvl)}
            className="hover:bg-primary/20 rounded-full p-0.5"
            title={`Remove ${lvl} filter`}
          >
            <X className="h-2.5 w-2.5" />
          </button>
        </span>
      ))}

      {filters.statusCodes.map((sc) => (
        <span
          key={sc}
          className="inline-flex items-center gap-1 bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full font-semibold"
        >
          <span>{sc}</span>
          <button
            onClick={() => handleRemoveStatus(sc)}
            className="hover:bg-primary/20 rounded-full p-0.5"
            title={`Remove ${sc} filter`}
          >
            <X className="h-2.5 w-2.5" />
          </button>
        </span>
      ))}

      {filters.dateRange && (
        <span className="inline-flex items-center gap-1 bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full font-semibold">
          <span>
            {filters.dateRange.start
              ? new Date(filters.dateRange.start).toLocaleDateString()
              : ""}{" "}
            -{" "}
            {filters.dateRange.end
              ? new Date(filters.dateRange.end).toLocaleDateString()
              : ""}
          </span>
          <button
            onClick={handleRemoveDateRange}
            className="hover:bg-primary/20 rounded-full p-0.5"
            title="Remove date range filter"
          >
            <X className="h-2.5 w-2.5" />
          </button>
        </span>
      )}

      <button
        onClick={onResetAll}
        className="text-muted-foreground hover:text-foreground hover:bg-muted font-semibold text-[10px] uppercase tracking-wider px-2 py-1 rounded-md transition-colors flex items-center gap-1 ml-auto"
        title="Clear all active filters"
      >
        <RotateCcw className="h-3 w-3" />
        <span>Reset Filters</span>
      </button>
    </div>
  );
}
