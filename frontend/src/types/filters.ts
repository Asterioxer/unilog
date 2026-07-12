export interface DateFilter {
  start: string;
  end: string;
}

export interface TableFilters {
  levels: string[];
  statusCodes: string[];
  dateRange: DateFilter | null;
  columnFilters: Record<string, string>;
}
