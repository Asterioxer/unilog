import { useState, useRef, useEffect } from "react";
import { Filter } from "lucide-react";
import type { TableFilters } from "../../types/filters";

interface FiltersPanelProps {
  filters: TableFilters;
  onChangeFilters: (filters: TableFilters) => void;
}

export default function FiltersPanel({
  filters,
  onChangeFilters,
}: FiltersPanelProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLevelToggle = (lvl: string) => {
    const isSelected = filters.levels.includes(lvl);
    const nextLevels = isSelected
      ? filters.levels.filter((l) => l !== lvl)
      : [...filters.levels, lvl];
    onChangeFilters({ ...filters, levels: nextLevels });
  };

  const handleStatusToggle = (sc: string) => {
    const isSelected = filters.statusCodes.includes(sc);
    const nextStatuses = isSelected
      ? filters.statusCodes.filter((s) => s !== sc)
      : [...filters.statusCodes, sc];
    onChangeFilters({ ...filters, statusCodes: nextStatuses });
  };

  const handleDateChange = (field: "start" | "end", val: string) => {
    const nextRange = filters.dateRange
      ? { ...filters.dateRange, [field]: val }
      : { start: "", end: "", [field]: val };

    const hasValue = nextRange.start || nextRange.end;
    onChangeFilters({
      ...filters,
      dateRange: hasValue ? nextRange : null,
    });
  };

  const activeCount =
    filters.levels.length +
    filters.statusCodes.length +
    (filters.dateRange ? 1 : 0);

  return (
    <div className="relative" ref={containerRef}>
      <button
        onClick={() => setOpen(!open)}
        className={`px-3.5 py-2 border text-sm font-medium rounded-lg transition-all flex items-center gap-2 ${
          activeCount > 0
            ? "border-primary/30 bg-primary/5 text-primary hover:bg-primary/10"
            : "border-border bg-background hover:bg-muted"
        }`}
        title="Toggle Filter Parameters Panel"
      >
        <Filter className="h-4 w-4" />
        <span>Filters</span>
        {activeCount > 0 && (
          <span className="h-4.5 min-w-4.5 px-1 rounded-full bg-primary text-primary-foreground text-[10px] font-bold inline-flex items-center justify-center">
            {activeCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute left-0 mt-2 w-80 border border-border bg-card rounded-xl shadow-lg z-50 p-4 space-y-4 text-sm">
          <div className="space-y-1.5">
            <span className="font-semibold text-[10px] text-muted-foreground uppercase tracking-wider block">
              Log Levels
            </span>
            <div className="flex flex-wrap gap-1.5">
              {["INFO", "WARN", "ERROR", "DEBUG"].map((lvl) => {
                const active = filters.levels.includes(lvl);
                return (
                  <button
                    key={lvl}
                    onClick={() => handleLevelToggle(lvl)}
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold border transition-all ${
                      active
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background text-foreground/75 border-border hover:bg-muted"
                    }`}
                  >
                    {lvl}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-1.5">
            <span className="font-semibold text-[10px] text-muted-foreground uppercase tracking-wider block">
              HTTP Status Codes
            </span>
            <div className="flex flex-wrap gap-1.5">
              {["2xx", "3xx", "4xx", "5xx"].map((sc) => {
                const active = filters.statusCodes.includes(sc);
                return (
                  <button
                    key={sc}
                    onClick={() => handleStatusToggle(sc)}
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold border transition-all ${
                      active
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background text-foreground/75 border-border hover:bg-muted"
                    }`}
                  >
                    {sc}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-2 border-t border-border/50 pt-3">
            <span className="font-semibold text-[10px] text-muted-foreground uppercase tracking-wider block">
              Date Range (UTC)
            </span>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground">Start</label>
                <input
                  type="datetime-local"
                  value={filters.dateRange?.start || ""}
                  onChange={(e) => handleDateChange("start", e.target.value)}
                  className="w-full bg-background border border-border rounded-md p-1.5 text-xs text-foreground focus:ring-1 focus:ring-primary focus:outline-hidden"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground">End</label>
                <input
                  type="datetime-local"
                  value={filters.dateRange?.end || ""}
                  onChange={(e) => handleDateChange("end", e.target.value)}
                  className="w-full bg-background border border-border rounded-md p-1.5 text-xs text-foreground focus:ring-1 focus:ring-primary focus:outline-hidden"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
