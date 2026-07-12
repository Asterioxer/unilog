import { buildExportFilename } from "./filename";

export const exportToJSON = (records: Record<string, unknown>[]): void => {
  if (records.length === 0) return;

  const jsonContent = JSON.stringify(records, null, 2);
  const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", buildExportFilename("unilog_export", "json"));
  link.click();

  URL.revokeObjectURL(url);
};
