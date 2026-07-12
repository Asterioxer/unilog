import type { TableFilters } from "../types/filters";

export const filterRecords = (
  records: Record<string, unknown>[],
  filters: TableFilters,
  searchQuery: string
): Record<string, unknown>[] => {
  let result = [...records];

  // 1. Global Search Matcher
  if (searchQuery && searchQuery.trim()) {
    const query = searchQuery.toLowerCase().trim();
    result = result.filter((r) =>
      Object.values(r).some((val) =>
        String(val).toLowerCase().includes(query)
      )
    );
  }

  // 2. Column-Specific Filters
  if (filters.columnFilters) {
    Object.entries(filters.columnFilters).forEach(([colId, filterVal]) => {
      if (filterVal && filterVal.trim()) {
        const query = filterVal.toLowerCase().trim();
        result = result.filter((r) => {
          const val = r[colId];
          return val !== undefined && String(val).toLowerCase().includes(query);
        });
      }
    });
  }

  // 3. Log Severity Levels (Multi-select)
  if (filters.levels && filters.levels.length > 0) {
    const activeLevels = filters.levels.map((l) => l.toUpperCase());
    result = result.filter((r) => {
      const rawLevel = r.level || r.log_level;
      if (!rawLevel) return false;
      const levelStr = String(rawLevel).toUpperCase();
      return activeLevels.some(
        (al) => levelStr.includes(al) || al.includes(levelStr)
      );
    });
  }

  // 4. HTTP Status Code Ranges (Multi-select, e.g. "2xx", "3xx", "4xx", "5xx")
  if (filters.statusCodes && filters.statusCodes.length > 0) {
    result = result.filter((r) => {
      const rawStatus = r.status_code || r.status;
      if (!rawStatus) return false;
      const statusStr = String(rawStatus);
      const firstDigit = statusStr.charAt(0);
      return filters.statusCodes.some((sc) => sc.charAt(0) === firstDigit);
    });
  }

  // 5. UTC Date-Time Range Bounds
  if (filters.dateRange) {
    const { start, end } = filters.dateRange;
    const startMs = start ? new Date(start).getTime() : null;
    const endMs = end ? new Date(end).getTime() : null;

    if (startMs !== null || endMs !== null) {
      result = result.filter((r) => {
        const rawTime = r.timestamp || r.time || r.datetime;
        if (!rawTime) return false;
        const timeMs = new Date(String(rawTime)).getTime();
        if (isNaN(timeMs)) return false;

        if (startMs !== null && timeMs < startMs) return false;
        if (endMs !== null && timeMs > endMs) return false;
        return true;
      });
    }
  }

  return result;
};
