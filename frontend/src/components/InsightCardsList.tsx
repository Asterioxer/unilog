import { Sparkles, Info } from "lucide-react";
import type { InsightResponse } from "../types/api";
import InsightCard from "./InsightCard";

interface InsightCardsListProps {
  insights: InsightResponse[] | null;
}

export default function InsightCardsList({ insights }: InsightCardsListProps) {
  if (insights === null) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-primary" />
        <h2 className="text-xl font-bold tracking-tight text-foreground">
          Operational Intelligence Insights
        </h2>
      </div>

      {insights.length === 0 ? (
        <div className="flex items-center gap-3 p-5 rounded-xl border border-dashed border-border bg-card shadow-xs text-muted-foreground">
          <div className="p-2 rounded-lg bg-muted border border-border shrink-0">
            <Info className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="space-y-0.5">
            <h4 className="text-sm font-semibold text-foreground">
              No operational insights detected.
            </h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              All backend rules parsed clear. Latencies, HTTP statuses, and traffic volumes are within acceptable thresholds.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {insights.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>
      )}
    </div>
  );
}
