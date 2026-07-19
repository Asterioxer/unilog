import { useState } from "react";
import { Sparkles, Terminal, Copy, Check, AlertCircle, Cpu, ShieldAlert, Zap } from "lucide-react";
import { apiService } from "../services/apiService";
import type { AIExplainResponse, InsightResponse } from "../types/api";

interface AIAssistantProps {
  metrics: Record<string, unknown> | null;
  insights: InsightResponse[];
  isProcessing?: boolean;
}

export default function AIAssistant({
  metrics,
  insights,
  isProcessing = false,
}: AIAssistantProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIExplainResponse | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const handleGenerate = async () => {
    if (!metrics) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.explainLogs(metrics, insights);
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || "Failed to generate AI explanation");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (code: string, cardIndex: number) => {
    navigator.clipboard.writeText(code);
    setCopiedId(cardIndex);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const renderMarkdown = (text: string) => {
    return text.split("\n").map((line, idx) => {
      const trimmed = line.trim();
      if (trimmed.startsWith("### ")) {
        return (
          <h4 key={idx} className="text-md font-bold text-foreground mt-4 mb-2 tracking-tight">
            {trimmed.replace("### ", "")}
          </h4>
        );
      }
      if (trimmed.startsWith("## ")) {
        return (
          <h3 key={idx} className="text-lg font-bold text-foreground mt-5 mb-2 tracking-tight">
            {trimmed.replace("## ", "")}
          </h3>
        );
      }
      if (trimmed.startsWith("# ")) {
        return (
          <h2 key={idx} className="text-xl font-bold text-foreground mt-6 mb-3 tracking-tight">
            {trimmed.replace("# ", "")}
          </h2>
        );
      }
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        return (
          <li key={idx} className="text-sm text-muted-foreground ml-4 list-disc my-1">
            {trimmed.substring(2)}
          </li>
        );
      }
      if (!trimmed) {
        return <div key={idx} className="h-2" />;
      }
      return (
        <p key={idx} className="text-sm text-muted-foreground leading-relaxed my-2">
          {line}
        </p>
      );
    });
  };

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border border-border bg-card rounded-xl">
        <div className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-muted-foreground">Waiting for analysis compilation...</p>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-border bg-muted/20 rounded-xl">
        <Sparkles className="h-10 w-10 text-muted-foreground/60 mb-4" />
        <h3 className="text-base font-bold text-foreground">No Metrics Loaded</h3>
        <p className="text-sm text-muted-foreground mt-1 max-w-sm">
          Parse a log dump or upload files first to enable the AI SRE Assistant diagnostics.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* AI Header Card */}
      <div className="p-6 border border-primary/20 bg-gradient-to-r from-primary/5 via-violet-500/5 to-card rounded-2xl shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-primary/10 text-primary rounded-xl">
              <Cpu className="h-6 w-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                AI SRE Diagnostic Assistant
                <span className="text-xs font-semibold px-2 py-0.5 bg-primary/10 text-primary rounded-full">
                  Gemini Flash
                </span>
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Generates instant root-cause analysis, traffic pattern explanations, and copyable mitigation configurations.
              </p>
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground font-semibold text-sm rounded-xl hover:bg-primary/95 transition-all shadow-md active:scale-98 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="h-4 w-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                Analyzing logs...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generate AI Diagnostics
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 border border-destructive/20 bg-destructive/5 text-destructive rounded-xl">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      {/* Main Results Panel */}
      {result ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Diagnostic Report Panel */}
          <div className="lg:col-span-7 p-6 border border-border bg-card rounded-2xl space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-border">
              <Zap className="h-5 w-5 text-amber-500" />
              <h3 className="text-base font-bold text-foreground">Diagnostic Report</h3>
            </div>
            <div className="p-4 bg-muted/20 border border-border/40 rounded-xl">
              <p className="text-sm font-bold text-foreground">{result.summary}</p>
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground">
              {renderMarkdown(result.explanation)}
            </div>
          </div>

          {/* Actionable Remediations Panel */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center gap-2 px-1">
              <Terminal className="h-5 w-5 text-primary" />
              <h3 className="text-base font-bold text-foreground">Remediation Script Center</h3>
            </div>
            <div className="space-y-4">
              {result.remediations.map((card, index) => (
                <div key={index} className="border border-border bg-card rounded-2xl overflow-hidden shadow-xs">
                  <div className="p-4 border-b border-border bg-muted/10 flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-foreground">{card.title}</h4>
                      <p className="text-xs text-muted-foreground mt-0.5">{card.description}</p>
                    </div>
                    <button
                      onClick={() => handleCopy(card.code, index)}
                      className="p-1.5 border border-border bg-card text-muted-foreground rounded-lg hover:text-foreground hover:bg-muted/30 transition-colors"
                      title="Copy code snippet"
                    >
                      {copiedId === index ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
                    </button>
                  </div>
                  <div className="p-4 bg-zinc-950 font-mono text-xs text-zinc-200 overflow-x-auto leading-relaxed max-h-[220px]">
                    <pre><code>{card.code}</code></pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        !loading && (
          <div className="flex flex-col items-center justify-center p-16 text-center border border-dashed border-border bg-muted/10 rounded-2xl">
            <Sparkles className="h-12 w-12 text-primary/30 mb-4 animate-pulse" />
            <h3 className="text-base font-bold text-foreground">Interactive AI Diagnostic Report</h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-sm">
              Click the generate button above to run deep learning diagnostics on the currently analyzed log records.
            </p>
          </div>
        )
      )}
    </div>
  );
}
