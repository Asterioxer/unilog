import { buildExportFilename } from "./filename";

export const exportToCSV = (
  records: Record<string, unknown>[],
  columns: string[]
): void => {
  if (records.length === 0) return;

  const headers = columns.join(",");
  const csvRows = records.map((row) =>
    columns
      .map((colId) => {
        const val = row[colId];
        const strVal = val === undefined || val === null ? "" : String(val);
        return `"${strVal.replace(/"/g, '""')}"`;
      })
      .join(",")
  );

  const csvContent = [headers, ...csvRows].join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", buildExportFilename("unilog_export", "csv"));
  link.click();

  URL.revokeObjectURL(url);
};
