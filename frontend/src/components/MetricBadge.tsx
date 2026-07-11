import type { ReactNode } from "react";

type BadgeVariant = "info" | "success" | "warning" | "error" | "default";

interface MetricBadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  pulse?: boolean;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  info: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  success: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
  error: "bg-destructive/10 text-destructive border-destructive/20",
  default: "bg-muted text-muted-foreground border-border",
};

const pulseStyles: Record<BadgeVariant, string> = {
  info: "bg-blue-500",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  error: "bg-destructive",
  default: "bg-muted-foreground",
};

export default function MetricBadge({
  children,
  variant = "default",
  pulse = false,
  className = "",
}: MetricBadgeProps) {
  return (
    <span 
      data-testid="metric-badge"
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-semibold select-none transition-all ${variantStyles[variant]} ${className}`}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${pulseStyles[variant]}`} />
          <span className={`relative inline-flex rounded-full h-2 w-2 ${pulseStyles[variant]}`} />
        </span>
      )}
      {children}
    </span>
  );
}
