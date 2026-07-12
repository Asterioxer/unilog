import { highlightMatch } from "../../../utils/highlight";

interface RawCellProps {
  value: unknown;
  query: string;
}

export default function RawCell({ value, query }: RawCellProps) {
  const strVal = value !== undefined && value !== null ? String(value) : "-";
  return (
    <span
      className="font-mono text-xs text-muted-foreground truncate max-w-[280px] block"
      title={strVal}
    >
      {highlightMatch(strVal, query)}
    </span>
  );
}
