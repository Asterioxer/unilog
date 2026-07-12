import { useState } from "react";
import { Copy, Check } from "lucide-react";
import JsonViewer from "./JsonViewer";

interface ExpandedRowProps {
  row: Record<string, unknown>;
  colSpan: number;
}

export default function ExpandedRow({ row, colSpan }: ExpandedRowProps) {
  const [copiedRaw, setCopiedRaw] = useState(false);

  const handleCopyRaw = () => {
    if (row.raw) {
      navigator.clipboard.writeText(String(row.raw));
      setCopiedRaw(true);
      setTimeout(() => setCopiedRaw(false), 2000);
    }
  };

  return (
    <tr className="bg-muted/10">
      <td colSpan={colSpan} className="px-6 py-4 border-t border-b border-border/50">
        <div className="flex flex-col gap-5 max-w-4xl">
          {!!row.raw && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider">
                  Raw Log Record
                </span>
                <button
                  onClick={handleCopyRaw}
                  className="p-1 hover:bg-muted rounded-md text-slate-400 hover:text-slate-200 transition-all inline-flex items-center gap-1 text-[10px]"
                  title="Copy Raw Log"
                >
                  {copiedRaw ? (
                    <Check className="h-3 w-3 text-emerald-400" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                  <span>{copiedRaw ? "Copied!" : "Copy Raw"}</span>
                </button>
              </div>
              <div className="bg-background border border-border/40 p-3 rounded-lg overflow-x-auto select-all font-mono text-xs text-muted-foreground leading-relaxed">
                {String(row.raw)}
              </div>
            </div>
          )}

          <div>
            <JsonViewer data={row} />
          </div>
        </div>
      </td>
    </tr>
  );
}
