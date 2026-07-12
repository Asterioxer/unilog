import { useState } from "react";
import { Copy, Check } from "lucide-react";

interface JsonViewerProps {
  data: Record<string, unknown>;
}

export default function JsonViewer({ data }: JsonViewerProps) {
  const [copied, setCopied] = useState(false);
  const jsonStr = JSON.stringify(data, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonStr);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group bg-slate-950 text-slate-200 border border-slate-800 rounded-lg overflow-hidden font-mono text-xs shadow-inner">
      <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800">
        <span className="text-[10px] uppercase font-semibold tracking-wider text-slate-500">
          Record Fields JSON
        </span>
        <button
          onClick={handleCopy}
          className="p-1.5 hover:bg-slate-800 rounded-md text-slate-400 hover:text-slate-200 transition-all inline-flex items-center gap-1.5 text-[10px]"
          title="Copy JSON to Clipboard"
        >
          {copied ? (
            <Check className="h-3 w-3 text-emerald-400" />
          ) : (
            <Copy className="h-3 w-3" />
          )}
          <span>{copied ? "Copied!" : "Copy"}</span>
        </button>
      </div>
      <pre className="p-4 overflow-x-auto max-h-[300px] scrollbar-thin">
        <code>{jsonStr}</code>
      </pre>
    </div>
  );
}
