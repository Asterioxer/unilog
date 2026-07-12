import { highlightMatch } from "../../../utils/highlight";

interface StatusCellProps {
  value: unknown;
  query: string;
}

export default function StatusCell({ value, query }: StatusCellProps) {
  const strVal = value !== undefined && value !== null ? String(value) : "";
  if (!strVal) return <span>-</span>;

  const firstDigit = strVal.charAt(0);
  let badgeColor = "bg-muted text-muted-foreground border-border";

  if (firstDigit === "2") {
    badgeColor = "bg-emerald-500/10 text-emerald-600 border-emerald-500/20 dark:text-emerald-400";
  } else if (firstDigit === "3") {
    badgeColor = "bg-blue-500/10 text-blue-600 border-blue-500/20 dark:text-blue-400";
  } else if (firstDigit === "4") {
    badgeColor = "bg-amber-500/10 text-amber-600 border-amber-500/20 dark:text-amber-400";
  } else if (firstDigit === "5") {
    badgeColor = "bg-rose-500/10 text-rose-600 border-rose-500/20 dark:text-rose-400";
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold font-mono border ${badgeColor}`}
    >
      {highlightMatch(strVal, query)}
    </span>
  );
}
