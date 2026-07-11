import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div 
      data-testid="empty-state"
      className={`flex flex-col items-center justify-center p-8 text-center bg-muted/20 border border-border rounded-xl min-h-[220px] transition-all hover:bg-muted/30 ${className}`}
    >
      {icon && (
        <div className="p-3 bg-muted rounded-full mb-4 text-muted-foreground">
          {icon}
        </div>
      )}
      <h4 className="text-sm font-semibold tracking-tight mb-1 text-foreground">
        {title}
      </h4>
      <p className="text-xs text-muted-foreground max-w-sm leading-relaxed mb-4">
        {description}
      </p>
      {action && (
        <div className="mt-2">
          {action}
        </div>
      )}
    </div>
  );
}
