import { highlightMatch } from "../../../utils/highlight";

interface IPCellProps {
  value: unknown;
  query: string;
}

export default function IPCell({ value, query }: IPCellProps) {
  const strVal = value !== undefined && value !== null ? String(value) : "-";
  return (
    <span className="font-mono text-xs text-foreground/80">
      {highlightMatch(strVal, query)}
    </span>
  );
}
