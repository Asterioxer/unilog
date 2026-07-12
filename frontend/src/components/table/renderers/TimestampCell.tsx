import { highlightMatch } from "../../../utils/highlight";

interface TimestampCellProps {
  value: unknown;
  query: string;
}

export default function TimestampCell({ value, query }: TimestampCellProps) {
  const strVal = value !== undefined && value !== null ? String(value) : "-";
  return (
    <span className="font-mono text-xs text-muted-foreground">
      {highlightMatch(strVal, query)}
    </span>
  );
}
