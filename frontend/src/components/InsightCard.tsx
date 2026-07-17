import React, { useState } from "react";
import { 
  ShieldAlert, Zap, AlertTriangle, TrendingUp, ChevronDown, ChevronUp, Copy, Check 
} from "lucide-react";
import type { InsightResponse } from "../types/api";

interface InsightCardProps {
  insight: InsightResponse;
}

const severityColors: Record<string, { border: string; bg: string; text: string; badgeBg: string }> = {
  critical: {
    border: "border-l-4 border-l-red-600 border-red-100",
    bg: "bg-red-50/30",
    text: "text-red-950",
    badgeBg: "bg-red-100 text-red-800"
  },
  high: {
    border: "border-l-4 border-l-orange-500 border-orange-100",
    bg: "bg-orange-50/20",
    text: "text-orange-950",
    badgeBg: "bg-orange-100 text-orange-800"
  },
  medium: {
    border: "border-l-4 border-l-amber-500 border-amber-100",
    bg: "bg-amber-50/20",
    text: "text-amber-950",
    badgeBg: "bg-amber-100 text-amber-800"
  },
  low: {
    border: "border-l-4 border-l-blue-500 border-blue-100",
    bg: "bg-blue-50/10",
    text: "text-blue-950",
    badgeBg: "bg-blue-100 text-blue-800"
  }
};

const categoryIcons: Record<string, React.ReactNode> = {
  security: <ShieldAlert className="h-5 w-5 text-red-600" />,
  performance: <Zap className="h-5 w-5 text-amber-500" />,
  reliability: <AlertTriangle className="h-5 w-5 text-orange-500" />,
  traffic: <TrendingUp className="h-5 w-5 text-blue-500" />
};

export default function InsightCard({ insight }: InsightCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const colors = severityColors[insight.severity.toLowerCase()] || severityColors.low;
  const icon = categoryIcons[insight.category.toLowerCase()] || <AlertTriangle className="h-5 w-5 text-gray-500" />;
  
  // Format the camelCase or snake_case ID to a clean Title
  const formatTitle = (id: string) => {
    return id
      .replace(/[._-]/g, " ")
      .replace(/([A-Z])/g, " $1")
      .trim()
      .replace(/\s+/g, " ")
      .split(" ")
      .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(" ");
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(insight.recommendation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div 
      className={`border rounded-xl shadow-xs transition-all duration-200 ${colors.border} ${colors.bg} hover:shadow-md`}
    >
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="p-2 bg-background rounded-lg border border-border shrink-0 mt-0.5 shadow-xs">
              {icon}
            </div>
            <div className="space-y-1.5 flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className={`text-base font-bold tracking-tight ${colors.text} truncate`}>
                  {formatTitle(insight.id)}
                </h3>
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${colors.badgeBg}`}>
                  {insight.severity}
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-800">
                  {insight.category}
                </span>
                <span className="text-[10px] font-medium text-muted-foreground ml-auto">
                  Confidence: {(insight.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-sm leading-relaxed text-slate-600 block">
                {insight.description}
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1.5 hover:bg-muted rounded-lg text-muted-foreground transition-colors self-start shrink-0"
            aria-label={isOpen ? "Collapse recommendation" : "Expand recommendation"}
          >
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>

        {isOpen && (
          <div className="mt-4 pt-4 border-t border-border/50 animate-fade-in space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Recommended Remediation Plan
              </h4>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground font-medium px-2 py-1 rounded-md hover:bg-muted transition-colors border border-border/30 bg-background/50"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>Copy Plan</span>
                  </>
                )}
              </button>
            </div>
            <div className="p-3.5 bg-background rounded-lg border border-border/60 text-sm leading-relaxed text-slate-600 font-medium whitespace-pre-line">
              {insight.recommendation}
            </div>
            {insight.evidence && Object.keys(insight.evidence).length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  Trigger Evidence
                </span>
                <div className="text-xs font-mono bg-muted p-3 rounded-lg border border-border overflow-x-auto text-slate-700 max-h-40">
                  {JSON.stringify(insight.evidence, null, 2)}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
