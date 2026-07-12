import { Download } from "lucide-react";
import { exportToCSV } from "../../utils/export/csv";
import { exportToJSON } from "../../utils/export/json";
import type { ColumnMeta } from "./columns";

interface ExportActionsProps {
  filteredRecords: Record<string, unknown>[];
  columns: ColumnMeta[];
  visibleColumns: Record<string, boolean>;
}

export default function ExportActions({
  filteredRecords,
  columns,
  visibleColumns,
}: ExportActionsProps) {
  const handleCSVExport = () => {
    const visibleKeys = columns
      .filter((col) => visibleColumns[col.id] !== false)
      .map((col) => col.id);
    exportToCSV(filteredRecords, visibleKeys);
  };

  const handleJSONExport = () => {
    exportToJSON(filteredRecords);
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleCSVExport}
        disabled={filteredRecords.length === 0}
        className="px-3.5 py-2 border border-border bg-background hover:bg-muted disabled:opacity-40 disabled:pointer-events-none text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
        title="Export dataset as CSV"
      >
        <Download className="h-4 w-4 text-muted-foreground" />
        <span>CSV</span>
      </button>

      <button
        onClick={handleJSONExport}
        disabled={filteredRecords.length === 0}
        className="px-3.5 py-2 border border-border bg-background hover:bg-muted disabled:opacity-40 disabled:pointer-events-none text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
        title="Export dataset as JSON"
      >
        <Download className="h-4 w-4 text-muted-foreground" />
        <span>JSON</span>
      </button>
    </div>
  );
}
