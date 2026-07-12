export interface ColumnMeta {
  id: string;
  label: string;
  sortable: boolean;
  filterable?: boolean;
  searchable?: boolean;
  visibleByDefault?: boolean;
  exportable?: boolean;
}

export const DEFAULT_COLUMNS: ColumnMeta[] = [
  {
    id: "timestamp",
    label: "Timestamp",
    sortable: true,
    filterable: true,
    searchable: true,
    visibleByDefault: true,
    exportable: true,
  },
  {
    id: "level",
    label: "Level",
    sortable: true,
    filterable: true,
    searchable: true,
    visibleByDefault: true,
    exportable: true,
  },
  {
    id: "source_ip",
    label: "Client IP",
    sortable: true,
    filterable: true,
    searchable: true,
    visibleByDefault: true,
    exportable: true,
  },
  {
    id: "method",
    label: "Method",
    sortable: true,
    filterable: true,
    searchable: true,
    visibleByDefault: true,
    exportable: true,
  },
  {
    id: "path",
    label: "Path",
    sortable: true,
    filterable: true,
    searchable: true,
    visibleByDefault: true,
    exportable: true,
  },
  {
    id: "status_code",
    label: "Status",
    sortable: true,
    filterable: true,
    searchable: true,
    visibleByDefault: true,
    exportable: true,
  },
  {
    id: "bytes_sent",
    label: "Bytes",
    sortable: true,
    filterable: false,
    searchable: false,
    visibleByDefault: true,
    exportable: true,
  },
];

export const buildColumnsMeta = (records: Record<string, unknown>[]): ColumnMeta[] => {
  const presentKeys = new Set<string>();
  records.forEach((r) => {
    Object.keys(r).forEach((k) => {
      if (k !== "raw" && k !== "_parse_error" && k !== "original_line") {
        presentKeys.add(k);
      }
    });
  });

  const columns: ColumnMeta[] = [];

  // Add standard default columns in correct layout sequence if matching keys exist
  DEFAULT_COLUMNS.forEach((defCol) => {
    const matchedKey = Array.from(presentKeys).find(
      (k) =>
        k === defCol.id ||
        (defCol.id === "source_ip" && (k === "ip" || k === "client_ip")) ||
        (defCol.id === "level" && k === "log_level")
    );

    if (matchedKey) {
      columns.push({
        id: matchedKey,
        label: defCol.label,
        sortable: defCol.sortable,
        filterable: defCol.filterable,
        searchable: defCol.searchable,
        visibleByDefault: defCol.visibleByDefault,
        exportable: defCol.exportable,
      });
      presentKeys.delete(matchedKey);
    }
  });

  // Append remaining custom fields as dynamically detected columns
  presentKeys.forEach((key) => {
    columns.push({
      id: key,
      label: key.charAt(0).toUpperCase() + key.slice(1).replace("_", " "),
      sortable: true,
      filterable: true,
      searchable: true,
      visibleByDefault: true,
      exportable: true,
    });
  });

  return columns;
};
