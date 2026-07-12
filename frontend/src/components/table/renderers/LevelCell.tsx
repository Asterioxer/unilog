import { highlightMatch } from "../../../utils/highlight";

interface LevelCellProps {
  value: unknown;
  query: string;
}

export default function LevelCell({ value, query }: LevelCellProps) {
  const strVal = value !== undefined && value !== null ? String(value).toUpperCase() : "";
  if (!strVal) return <span>-</span>;

  let color = "text-muted-foreground bg-muted/30 border-border";
  if (
    strVal.includes("ERR") ||
    strVal.includes("FAIL") ||
    strVal.includes("CRIT") ||
    strVal.includes("FATAL")
  ) {
    color = "text-rose-600 bg-rose-500/10 border-rose-500/20 dark:text-rose-400";
  } else if (strVal.includes("WARN")) {
    color = "text-amber-600 bg-amber-500/10 border-amber-500/20 dark:text-amber-400";
  } else if (strVal.includes("INFO") || strVal.includes("SUCCESS")) {
    color = "text-emerald-600 bg-emerald-500/10 border-emerald-500/20 dark:text-emerald-400";
  } else if (strVal.includes("DEBUG") || strVal.includes("TRACE")) {
    color = "text-blue-600 bg-blue-500/10 border-blue-500/20 dark:text-blue-400";
  }

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-bold tracking-wide border ${color}`}
    >
      {highlightMatch(strVal, query)}
    </span>
  );
}
