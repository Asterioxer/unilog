import { useState } from "react";
import { 
  Clock, Users, ArrowRight, ShieldAlert, BarChart2, Activity,
  ChevronDown, ChevronUp, AlertCircle
} from "lucide-react";
import type { SessionMetrics, JourneyMetrics } from "../types/api";

interface SessionObserverProps {
  sessionMetrics: SessionMetrics | null;
  journeyMetrics: JourneyMetrics | null;
  isProcessing?: boolean;
}

export default function SessionObserver({ 
  sessionMetrics, 
  journeyMetrics,
  isProcessing = false 
}: SessionObserverProps) {
  const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null);

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border border-border bg-card rounded-xl">
        <div className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-muted-foreground">Reconstructing user session graphs...</p>
      </div>
    );
  }

  if (!sessionMetrics || sessionMetrics.active_sessions_count === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-border bg-muted/20 rounded-xl">
        <Users className="h-10 w-10 text-muted-foreground/60 mb-4" />
        <h3 className="text-base font-bold text-foreground">No Sessions Reconstructed</h3>
        <p className="text-sm text-muted-foreground mt-1 max-w-sm">
          Once log entries are processed, client IP behaviors and user journeys will be automatically timeline-mapped here.
        </p>
      </div>
    );
  }

  const {
    average_session_duration_seconds,
    bounce_rate,
    pages_per_session,
    active_sessions_count,
    possible_bot_count,
    credential_stuffing_count,
    endpoint_enumeration_count,
    sessions,
  } = sessionMetrics;

  const funnel = journeyMetrics?.funnel || {
    Landing: 0,
    Products: 0,
    Product: 0,
    Cart: 0,
    Checkout: 0
  };

  const funnelStages = [
    { name: "Landing", label: "Landing Page", count: funnel.Landing },
    { name: "Products", label: "Catalog View", count: funnel.Products },
    { name: "Product", label: "Product Details", count: funnel.Product },
    { name: "Cart", label: "Add to Cart", count: funnel.Cart },
    { name: "Checkout", label: "Purchase Flow", count: funnel.Checkout },
  ];

  const maxFunnelCount = Math.max(...funnelStages.map(s => s.count), 1);

  return (
    <div className="space-y-8">
      {/* Metrics Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="border border-border bg-card p-5 rounded-xl flex items-center gap-4 shadow-xs">
          <div className="p-3 bg-primary/10 text-primary rounded-lg">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Active Sessions</p>
            <p className="text-2xl font-bold text-foreground mt-0.5">{active_sessions_count}</p>
          </div>
        </div>

        <div className="border border-border bg-card p-5 rounded-xl flex items-center gap-4 shadow-xs">
          <div className="p-3 bg-blue-500/10 text-blue-500 rounded-lg">
            <Clock className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Avg Duration</p>
            <p className="text-2xl font-bold text-foreground mt-0.5">
              {average_session_duration_seconds >= 60 
                ? `${(average_session_duration_seconds / 60).toFixed(1)}m` 
                : `${average_session_duration_seconds}s`}
            </p>
          </div>
        </div>

        <div className="border border-border bg-card p-5 rounded-xl flex items-center gap-4 shadow-xs">
          <div className="p-3 bg-emerald-500/10 text-emerald-500 rounded-lg">
            <BarChart2 className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Bounce Rate</p>
            <p className="text-2xl font-bold text-foreground mt-0.5">{bounce_rate.toFixed(1)}%</p>
          </div>
        </div>

        <div className="border border-border bg-card p-5 rounded-xl flex items-center gap-4 shadow-xs">
          <div className="p-3 bg-purple-500/10 text-purple-500 rounded-lg">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Pages / Session</p>
            <p className="text-2xl font-bold text-foreground mt-0.5">{pages_per_session.toFixed(1)}</p>
          </div>
        </div>
      </div>

      {/* Security Threat Alerts Row */}
      {(possible_bot_count > 0 || credential_stuffing_count > 0 || endpoint_enumeration_count > 0) && (
        <div className="border border-destructive/20 bg-destructive/5 text-destructive rounded-xl p-5 flex flex-col gap-3">
          <h3 className="text-sm font-bold flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 animate-pulse" />
            Behavioral Security Anomalies Detected
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-medium">
            {possible_bot_count > 0 && (
              <div className="bg-destructive/10 rounded-lg p-3 border border-destructive/20 flex justify-between items-center">
                <span>Suspected Bot Traffic</span>
                <span className="bg-destructive text-destructive-foreground px-2 py-0.5 rounded-full font-bold">{possible_bot_count} sessions</span>
              </div>
            )}
            {credential_stuffing_count > 0 && (
              <div className="bg-destructive/10 rounded-lg p-3 border border-destructive/20 flex justify-between items-center">
                <span>Suspected Credential Stuffing</span>
                <span className="bg-destructive text-destructive-foreground px-2 py-0.5 rounded-full font-bold">{credential_stuffing_count} sessions</span>
              </div>
            )}
            {endpoint_enumeration_count > 0 && (
              <div className="bg-destructive/10 rounded-lg p-3 border border-destructive/20 flex justify-between items-center">
                <span>Suspected Endpoint Enumeration</span>
                <span className="bg-destructive text-destructive-foreground px-2 py-0.5 rounded-full font-bold">{endpoint_enumeration_count} sessions</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Funnel & User Conversion Stage Layout */}
      <div className="border border-border bg-card rounded-xl p-6 shadow-xs space-y-6">
        <div>
          <h3 className="text-lg font-bold tracking-tight text-foreground">User Journey Funnel Conversion</h3>
          <p className="text-xs text-muted-foreground">Progression pathway conversion rates from landing to purchase flow.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {funnelStages.map((stage) => {
            const pct = ((stage.count / maxFunnelCount) * 100).toFixed(0);
            return (
              <div key={stage.name} className="relative bg-muted/30 border border-border p-4 rounded-xl flex flex-col justify-between h-28 overflow-hidden group hover:border-primary/40 hover:bg-muted/50 transition-all">
                <div className="z-10">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">{stage.label}</span>
                  <div className="text-lg font-bold text-foreground mt-1">{stage.count} sessions</div>
                </div>
                <div className="z-10 text-xs font-semibold text-primary">{pct}% conversion</div>
                {/* Background progress bar block */}
                <div 
                  className="absolute bottom-0 left-0 bg-primary/5 transition-all group-hover:bg-primary/10 w-full"
                  style={{ height: `${pct}%` }}
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* Reconstructed Sessions Timeline Observer list */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold tracking-tight text-foreground">Reconstructed User Sessions</h3>
        <div className="space-y-4">
          {sessions.map((session) => {
            const isExpanded = expandedSessionId === session.session_id;
            const hasBotRisk = session.request_count > 500;
            const hasCS = session.requests.filter(req => 
              req.status_code === 401 || req.status_code === 403
            ).length > 40;
            const hasEnum = new Set(session.requests.map(r => r.path)).size > 100;
            const hasAnomalies = hasBotRisk || hasCS || hasEnum;

            return (
              <div 
                key={session.session_id} 
                className={`border rounded-xl bg-card overflow-hidden transition-all ${
                  isExpanded ? "border-primary/50 shadow-sm" : "border-border hover:border-border-hover"
                }`}
              >
                {/* Header Toggle */}
                <div 
                  className="p-5 flex flex-wrap items-center justify-between gap-4 cursor-pointer select-none"
                  onClick={() => setExpandedSessionId(isExpanded ? null : session.session_id)}
                >
                  <div className="space-y-1.5 min-w-[200px]">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-foreground">
                        {session.client_ip === "-" ? "Anonymous Session" : session.client_ip}
                      </span>
                      {hasAnomalies && (
                        <span className="bg-destructive/10 text-destructive text-[10px] font-bold px-2 py-0.5 rounded-full border border-destructive/20 flex items-center gap-1 shrink-0">
                          <AlertCircle className="h-3 w-3" /> Triggered Alert
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-2">
                      <span>{new Date(session.start_time).toLocaleString()}</span>
                      <span>•</span>
                      <span>{session.request_count} requests</span>
                    </div>
                  </div>

                  {/* Horizontal visual sequence transition journey */}
                  <div className="flex-1 max-w-lg hidden md:flex items-center gap-1 overflow-x-auto whitespace-nowrap py-1 scrollbar-thin">
                    {session.journey.slice(0, 5).map((stage, sIdx) => (
                      <div key={sIdx} className="flex items-center gap-1 text-[10px] font-semibold">
                        <span className={`px-2 py-0.5 rounded-md ${
                          stage === "Checkout" 
                            ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20" 
                            : stage === "Cart"
                            ? "bg-purple-500/10 text-purple-600 border border-purple-500/20"
                            : "bg-muted text-muted-foreground border border-border"
                        }`}>
                          {stage}
                        </span>
                        {sIdx < session.journey.slice(0, 5).length - 1 && (
                          <ArrowRight className="h-3 w-3 text-muted-foreground/60 shrink-0" />
                        )}
                      </div>
                    ))}
                    {session.journey.length > 5 && (
                      <span className="text-[10px] font-semibold text-muted-foreground bg-muted border border-border px-1.5 py-0.5 rounded-md shrink-0">
                        +{session.journey.length - 5} stages
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm font-bold text-foreground">
                        {session.duration_seconds >= 60 
                          ? `${(session.duration_seconds / 60).toFixed(0)}m ${Math.round(session.duration_seconds % 60)}s` 
                          : `${Math.round(session.duration_seconds)}s`}
                      </div>
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Duration</div>
                    </div>
                    {isExpanded ? <ChevronUp className="h-5 w-5 text-muted-foreground" /> : <ChevronDown className="h-5 w-5 text-muted-foreground" />}
                  </div>
                </div>

                {/* Collapsible Session Details */}
                {isExpanded && (
                  <div className="border-t border-border bg-muted/10 p-5 space-y-5 animate-slide-down">
                    {/* Journey Timeline Steps */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Chronological Session Journey</h4>
                      <div className="flex flex-wrap items-center gap-2 p-3 bg-muted/40 rounded-xl border border-border">
                        {session.journey.map((stage, sIdx) => (
                          <div key={sIdx} className="flex items-center gap-2 text-xs font-semibold">
                            <span className={`px-2.5 py-1 rounded-lg ${
                              stage === "Checkout"
                                ? "bg-emerald-500/15 text-emerald-600 border border-emerald-500/30"
                                : stage === "Cart"
                                ? "bg-purple-500/15 text-purple-600 border border-purple-500/30"
                                : "bg-card text-foreground border border-border shadow-xs"
                            }`}>
                              {stage}
                            </span>
                            {sIdx < session.journey.length - 1 && (
                              <ArrowRight className="h-3 w-3 text-muted-foreground/60" />
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Detailed request list within this session */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Session Requests Log ({session.request_count} items)</h4>
                      <div className="border border-border rounded-xl overflow-hidden bg-card max-h-60 overflow-y-auto">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="bg-muted border-b border-border text-muted-foreground uppercase font-semibold text-[10px]">
                              <th className="p-3">Timestamp</th>
                              <th className="p-3">Method</th>
                              <th className="p-3">Stage</th>
                              <th className="p-3">Endpoint Path</th>
                              <th className="p-3">Status</th>
                              <th className="p-3 text-right">Payload Size</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border font-medium">
                            {session.requests.map((req, rIdx) => (
                              <tr key={rIdx} className="hover:bg-muted/30 transition-colors">
                                <td className="p-3 text-muted-foreground">{new Date(req.timestamp).toLocaleTimeString()}</td>
                                <td className="p-3">
                                  <span className={`px-1.5 py-0.5 rounded-sm font-bold text-[9px] uppercase ${
                                    req.method === "POST" ? "bg-blue-500/10 text-blue-600" : "bg-muted text-muted-foreground"
                                  }`}>{req.method}</span>
                                </td>
                                <td className="p-3">
                                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md ${
                                    req.journey_stage === "Checkout" 
                                      ? "bg-emerald-500/10 text-emerald-600" 
                                      : req.journey_stage === "Cart"
                                      ? "bg-purple-500/10 text-purple-600"
                                      : "text-muted-foreground"
                                  }`}>{req.journey_stage}</span>
                                </td>
                                <td className="p-3 font-mono text-[11px] truncate max-w-xs">{req.path}</td>
                                <td className="p-3">
                                  <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-bold ${
                                    req.status_code >= 500
                                      ? "bg-destructive/10 text-destructive"
                                      : req.status_code >= 400
                                      ? "bg-warning/10 text-warning"
                                      : "bg-emerald-500/10 text-emerald-600"
                                  }`}>{req.status_code}</span>
                                </td>
                                <td className="p-3 text-right text-muted-foreground font-mono">
                                  {(req.size / 1024).toFixed(2)} KB
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
