import { useRef, useEffect } from "react";
import { ChevronDown, ChevronRight, Copy } from "lucide-react";
import type { ColumnMeta } from "./columns";
import TimestampCell from "./renderers/TimestampCell";
import LevelCell from "./renderers/LevelCell";
import IPCell from "./renderers/IPCell";
import StatusCell from "./renderers/StatusCell";
import RawCell from "./renderers/RawCell";
import { highlightMatch } from "../../utils/highlight";

interface RowProps {
  row: Record<string, unknown>;
  columns: ColumnMeta[];
  expanded: boolean;
  onToggleExpand: () => void;
  query: string;
  onCopyRow: () => void;
  isFocused: boolean;
  onKeyDown: (e: React.KeyboardEvent<HTMLTableRowElement>) => void;
}

export default function Row({
  row,
  columns,
  expanded,
  onToggleExpand,
  query,
  onCopyRow,
  isFocused,
  onKeyDown,
}: RowProps) {
  const rowRef = useRef<HTMLTableRowElement>(null);

  useEffect(() => {
    if (isFocused) {
      rowRef.current?.focus();
    }
  }, [isFocused]);

  const renderCell = (colId: string, value: unknown) => {
    if (colId === "timestamp" || colId === "time" || colId === "datetime") {
      return <TimestampCell value={value} query={query} />;
    }
    if (colId === "level" || colId === "log_level") {
      return <LevelCell value={value} query={query} />;
    }
    if (colId === "source_ip" || colId === "ip" || colId === "client_ip") {
      return <IPCell value={value} query={query} />;
    }
    if (colId === "status_code" || colId === "status") {
      return <StatusCell value={value} query={query} />;
    }
    if (colId === "raw") {
      return <RawCell value={value} query={query} />;
    }

    const strVal = value !== undefined && value !== null ? String(value) : "-";
    return (
      <span className="text-foreground/80 font-mono text-xs">
        {highlightMatch(strVal, query)}
      </span>
    );
  };

  return (
    <tr
      ref={rowRef}
      tabIndex={isFocused ? 0 : -1}
      onKeyDown={onKeyDown}
      className="hover:bg-muted/30 transition-colors group border-b border-border/50 focus:outline-hidden focus:ring-1 focus:ring-primary focus:bg-primary/5"
    >
      <td className="px-4 py-3 text-left w-10">
        <button
          onClick={onToggleExpand}
          tabIndex={-1} // Keep tab-stops clean
          className="p-1 hover:bg-muted rounded-md text-muted-foreground hover:text-foreground transition-colors"
          title={expanded ? "Collapse Row" : "Expand Row"}
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>
      </td>{columns.map((col) => (
        <td key={col.id} className="px-4 py-3 max-w-[240px] truncate">
          {renderCell(col.id, row[col.id])}
        </td>
      ))}
      <td className="px-4 py-3 text-right w-16">
        <button
          onClick={onCopyRow}
          tabIndex={-1} // Keep tab-stops clean
          className="p-1.5 hover:bg-muted rounded-md text-muted-foreground hover:text-foreground transition-colors inline-flex items-center"
          title="Copy Row JSON"
        >
          <Copy className="h-3.5 w-3.5" />
        </button>
      </td>
    </tr>
  );
}
