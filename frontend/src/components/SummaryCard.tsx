import type { ReactNode } from "react";
import Skeleton from "./Skeleton";

type AccentColor = "primary" | "emerald" | "destructive" | "blue" | "violet" | "none";

interface SummaryCardProps {
  title: string;
  value?: string | number | ReactNode;
  subtitle?: string;
  icon?: ReactNode;
  isLoading?: boolean;
  error?: string | null;
  accentColor?: AccentColor;
  badge?: ReactNode;
  ariaLabel?: string;
  className?: string;
}

const accentStyles: Record<AccentColor, string> = {
  primary: "border-l-4 border-l-primary",
  emerald: "border-l-4 border-l-emerald-500",
  destructive: "border-l-4 border-l-destructive",
  blue: "border-l-4 border-l-blue-500",
  violet: "border-l-4 border-l-violet-500",
  none: "",
};

export default function SummaryCard({
  title,
  value,
  subtitle,
  icon,
  isLoading = false,
  error = null,
  accentColor = "none",
  badge,
  ariaLabel,
  className = "",
}: SummaryCardProps) {
  return (
    <div 
      data-testid="summary-card"
      role="region"
      aria-label={ariaLabel || `${title} summary metric`}
      className={`border border-border bg-card text-card-foreground rounded-xl p-5 shadow-xs flex flex-col justify-between min-h-[120px] transition-all hover:shadow-md hover:scale-[1.01] ${accentStyles[accentColor]} ${className}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1 flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block truncate">
              {title}
            </span>
            {badge && !isLoading && !error && (
              <div className="shrink-0">{badge}</div>
            )}
          </div>
          
          {isLoading ? (
            <div className="space-y-2 mt-2">
              <Skeleton className="h-7 w-28" />
              <Skeleton className="h-3 w-20" />
            </div>
          ) : error ? (
            <span className="text-xs text-destructive font-medium block mt-1.5 leading-relaxed">
              {error}
            </span>
          ) : (
            <div className="space-y-1 mt-1">
              <div className="text-2xl font-bold tracking-tight block truncate text-foreground">
                {value !== undefined ? value : "-"}
              </div>
              {subtitle && (
                <span className="text-xs text-muted-foreground block font-medium truncate" title={subtitle}>
                  {subtitle}
                </span>
              )}
            </div>
          )}
        </div>
        {icon && !isLoading && (
          <div className="p-2.5 bg-muted/50 rounded-lg text-muted-foreground shrink-0 self-start">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
