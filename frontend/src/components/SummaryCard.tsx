import type { ReactNode } from "react";
import Skeleton from "./Skeleton";

interface SummaryCardProps {
  title: string;
  value?: string | number;
  subtitle?: string;
  icon?: ReactNode;
  isLoading?: boolean;
  error?: string | null;
  className?: string;
}

export default function SummaryCard({
  title,
  value,
  subtitle,
  icon,
  isLoading = false,
  error = null,
  className = "",
}: SummaryCardProps) {
  return (
    <div 
      data-testid="summary-card"
      className={`border border-border bg-card text-card-foreground rounded-xl p-5 shadow-xs flex flex-col justify-between min-h-[120px] transition-all hover:shadow-sm ${className}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1 flex-1">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
            {title}
          </span>
          {isLoading ? (
            <div className="space-y-2 mt-1">
              <Skeleton className="h-6 w-24" />
              <Skeleton className="h-3 w-16" />
            </div>
          ) : error ? (
            <span className="text-xs text-destructive font-medium block mt-1">
              {error}
            </span>
          ) : (
            <div className="space-y-1">
              <span className="text-2xl font-bold tracking-tight block">
                {value !== undefined ? value : "-"}
              </span>
              {subtitle && (
                <span className="text-xs text-muted-foreground block font-medium">
                  {subtitle}
                </span>
              )}
            </div>
          )}
        </div>
        {icon && !isLoading && (
          <div className="p-2.5 bg-muted/50 rounded-lg text-muted-foreground shrink-0">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
