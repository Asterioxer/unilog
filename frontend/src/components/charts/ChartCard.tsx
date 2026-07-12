import React from "react";
import EmptyState from "../EmptyState";
import { FileWarning } from "lucide-react";

interface ChartCardProps {
  title: string;
  description?: string;
  loading: boolean;
  empty: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export default function ChartCard({
  title,
  description,
  loading,
  empty,
  emptyTitle = "No data available",
  emptyDescription = "No data mapping available for this log payload.",
  children,
  actions,
  className = "",
}: ChartCardProps) {
  return (
    <div
      className={`border border-border bg-card rounded-xl p-6 shadow-xs flex flex-col justify-between animate-fade-in ${className}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-base font-bold tracking-tight text-foreground">{title}</h3>
          {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>

      <div className="h-64 flex items-center justify-center w-full">
        {loading ? (
          <div className="w-full h-full flex flex-col gap-4 animate-pulse justify-center">
            <div className="h-6 bg-muted rounded-md w-1/3" />
            <div className="h-32 bg-muted rounded-md w-full" />
            <div className="h-4 bg-muted rounded-md w-1/2" />
          </div>
        ) : empty ? (
          <EmptyState
            icon={<FileWarning className="h-6 w-6 text-muted-foreground" />}
            title={emptyTitle}
            description={emptyDescription}
            className="border-none bg-transparent min-h-0 py-0 w-full"
          />
        ) : (
          <div className="w-full h-full">{children}</div>
        )}
      </div>
    </div>
  );
}
