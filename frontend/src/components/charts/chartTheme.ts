export const LEVEL_COLORS: Record<string, string> = {
  INFO: "#22c55e",
  DEBUG: "#3b82f6",
  WARN: "#f59e0b",
  WARNING: "#f59e0b",
  ERROR: "#ef4444",
  CRITICAL: "#a855f7",
  SUCCESS: "#10b981",
  unknown: "#9ca3af"
};

export const STATUS_COLORS: Record<string, string> = {
  "2": "#22c55e", // 2xx (Success) - Green
  "3": "#3b82f6", // 3xx (Redirection) - Blue
  "4": "#f59e0b", // 4xx (Client Error) - Yellow/Orange
  "5": "#ef4444"  // 5xx (Server Error) - Red
};

export const fallbackStatusColor = "#9ca3af";
