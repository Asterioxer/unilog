import { useState, useRef, useEffect } from "react";
import { SlidersHorizontal, CheckSquare, Square } from "lucide-react";
import type { ColumnMeta } from "./columns";

interface ColumnToggleProps {
  columns: ColumnMeta[];
  visibleColumns: Record<string, boolean>;
  onToggleColumn: (colId: string) => void;
}

export default function ColumnToggle({
  columns,
  visibleColumns,
  onToggleColumn,
}: ColumnToggleProps) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="px-3.5 py-2 border border-border bg-background hover:bg-muted text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
        title="Toggle Column Visibility"
      >
        <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
        <span>Columns</span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 border border-border bg-card rounded-xl shadow-lg z-50 p-2 text-sm flex flex-col gap-1">
          <span className="font-semibold text-[10px] text-muted-foreground uppercase px-2.5 py-1.5 tracking-wider border-b border-border/60 mb-1">
            Toggle Columns
          </span>
          <div className="max-h-[240px] overflow-y-auto pr-1">
            {columns.map((col) => {
              const isVisible = visibleColumns[col.id] !== false;
              return (
                <button
                  key={col.id}
                  onClick={() => onToggleColumn(col.id)}
                  className="flex items-center gap-2.5 w-full text-left px-2 py-1.5 rounded-lg hover:bg-muted transition-colors font-medium text-foreground/80 hover:text-foreground"
                >
                  {isVisible ? (
                    <CheckSquare className="h-4 w-4 text-primary" />
                  ) : (
                    <Square className="h-4 w-4 text-muted-foreground" />
                  )}
                  <span className="capitalize">{col.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
