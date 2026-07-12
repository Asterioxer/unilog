import { ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react";
import type { ColumnMeta } from "./columns";
import type { SortState } from "../../types/table";

interface HeaderProps {
  columns: ColumnMeta[];
  sortConfig: SortState;
  onSort: (key: string) => void;
}

export default function Header({ columns, sortConfig, onSort }: HeaderProps) {
  return (
    <thead className="sticky top-0 bg-muted/90 backdrop-blur-xs font-semibold text-muted-foreground border-b border-border/80 z-10 shadow-xs">
      <tr>
        <th className="px-4 py-3 text-left w-10"></th>{columns.map((col) => {
          const isSorted = sortConfig.key === col.id;
          const isAsc = sortConfig.direction === "asc";

          return (
            <th
              key={col.id}
              onClick={() => col.sortable && onSort(col.id)}
              className={`px-4 py-3 select-none transition-colors ${
                col.sortable ? "cursor-pointer hover:bg-muted/60" : ""
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className="capitalize">{col.label}</span>
                {col.sortable && (
                  <span className="text-muted-foreground/50">
                    {isSorted ? (
                      isAsc ? (
                        <ArrowUp className="h-3 w-3 text-primary font-bold" />
                      ) : (
                        <ArrowDown className="h-3 w-3 text-primary font-bold" />
                      )
                    ) : (
                      <ArrowUpDown className="h-3 w-3" />
                    )}
                  </span>
                )}
              </div>
            </th>
          );
        })}
        <th className="px-4 py-3 text-right w-16">Actions</th>
      </tr>
    </thead>
  );
}
