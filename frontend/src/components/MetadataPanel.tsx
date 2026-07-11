import MetricBadge from "./MetricBadge";

interface MetadataPanelProps {
  filename?: string;
  fileSize?: number;
  processingTimeMs?: number;
  parserName?: string;
  rowsCount?: number;
  taskId?: string | null;
  taskStatus?: "completed" | "processing" | "failed" | null;
  className?: string;
}

export default function MetadataPanel({
  filename,
  fileSize,
  processingTimeMs,
  parserName,
  rowsCount,
  taskId,
  taskStatus,
  className = "",
}: MetadataPanelProps) {
  if (!filename && !parserName && !rowsCount) return null;

  const formatSize = (bytes?: number) => {
    if (bytes === undefined) return "N/A";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDuration = (ms?: number) => {
    if (ms === undefined) return "N/A";
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div 
      data-testid="metadata-panel"
      className={`border border-border bg-card rounded-xl p-5 shadow-xs space-y-4 ${className}`}
    >
      <h3 className="text-sm font-bold tracking-tight border-b border-border pb-2 text-foreground">
        Execution Metadata
      </h3>
      <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs leading-relaxed">
        {filename && (
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground font-medium uppercase tracking-wider text-[10px]">
              Source File
            </span>
            <span className="font-mono text-foreground font-semibold truncate max-w-[140px]" title={filename}>
              {filename}
            </span>
          </div>
        )}
        {fileSize !== undefined && fileSize > 0 && (
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground font-medium uppercase tracking-wider text-[10px]">
              Payload Size
            </span>
            <span className="font-semibold text-foreground">
              {formatSize(fileSize)}
            </span>
          </div>
        )}
        {parserName && (
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground font-medium uppercase tracking-wider text-[10px]">
              Parser Selected
            </span>
            <span className="font-mono text-primary font-bold uppercase">
              {parserName}
            </span>
          </div>
        )}
        {rowsCount !== undefined && (
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground font-medium uppercase tracking-wider text-[10px]">
              Parsed Rows
            </span>
            <span className="font-semibold text-foreground">
              {rowsCount.toLocaleString()}
            </span>
          </div>
        )}
        {processingTimeMs !== undefined && processingTimeMs > 0 && (
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground font-medium uppercase tracking-wider text-[10px]">
              Processing Duration
            </span>
            <span className="font-semibold text-foreground">
              {formatDuration(processingTimeMs)}
            </span>
          </div>
        )}
        {taskId && (
          <div className="col-span-2 flex flex-col gap-0.5 border-t border-border/50 pt-2 mt-1">
            <span className="text-muted-foreground font-medium uppercase tracking-wider text-[10px]">
              Background Worker Task ID
            </span>
            <span className="font-mono text-foreground text-[11px] select-all truncate" title={taskId}>
              {taskId}
            </span>
          </div>
        )}
        {taskStatus && (
          <div className="col-span-2 flex items-center justify-between border-t border-border/50 pt-2 mt-1">
            <span className="text-muted-foreground font-medium uppercase tracking-wider text-[10px]">
              Worker Thread Status
            </span>
            <MetricBadge 
              variant={
                taskStatus === "completed" 
                  ? "success" 
                  : taskStatus === "failed" 
                  ? "error" 
                  : "info"
              }
              pulse={taskStatus === "processing"}
            >
              {taskStatus}
            </MetricBadge>
          </div>
        )}
      </div>
    </div>
  );
}
