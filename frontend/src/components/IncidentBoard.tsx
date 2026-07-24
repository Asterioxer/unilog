import React, { useState } from 'react';
import type { Incident } from '../types/api';


interface IncidentBoardProps {
  incidents: Incident[];
}

export const IncidentBoard: React.FC<IncidentBoardProps> = ({ incidents }) => {
  const [expandedId, setExpandedId] = useState<string | null>(
    incidents.length > 0 ? incidents[0].incident_id : null
  );

  if (!incidents || incidents.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-6 text-center">
        <p className="text-sm text-slate-400">No active incidents detected in current stream window.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
          Correlated Incident Intelligence ({incidents.length})
        </h3>
        <span className="text-xs text-slate-400">SOC Consolidated View</span>
      </div>

      <div className="space-y-3">
        {incidents.map((inc) => {
          const isExpanded = expandedId === inc.incident_id;
          const isCritical = inc.severity === 'CRITICAL';
          const isHigh = inc.severity === 'HIGH';
          const badgeColor = isCritical
            ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
            : isHigh
            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            : 'bg-blue-500/10 text-blue-400 border-blue-500/20';

          return (
            <div
              key={inc.incident_id}
              className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 transition-all shadow-md"
            >
              {/* Incident Header */}
              <div
                className="flex items-center justify-between cursor-pointer select-none"
                onClick={() => setExpandedId(isExpanded ? null : inc.incident_id)}
              >
                <div className="flex items-center space-x-3">
                  <span className={`px-2.5 py-0.5 text-xs font-mono font-bold rounded border ${badgeColor}`}>
                    {inc.severity}
                  </span>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-100">{inc.title}</h4>
                    <span className="text-xs font-mono text-slate-400">{inc.incident_id}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">Confidence</span>
                    <span className="text-sm font-bold font-mono text-emerald-400">
                      {Math.round(inc.confidence * 100)}%
                    </span>
                  </div>
                  <button className="text-slate-400 hover:text-slate-200 text-xs font-mono">
                    {isExpanded ? '▼ Collapse' : '▶ Details'}
                  </button>
                </div>
              </div>

              {/* Expanded Incident Content */}
              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-4">
                  {/* Evidence Rationale */}
                  <div>
                    <h5 className="text-xs font-medium text-slate-300 mb-1.5">Evidence Rationale</h5>
                    <ul className="space-y-1">
                      {inc.confidence_evidence.map((ev, idx) => (
                        <li key={idx} className="text-xs text-slate-300 font-mono flex items-center space-x-2">
                          <span className="text-emerald-400">✓</span>
                          <span>{ev.replace(/^\[\+\]\s*/, '')}</span>
                        </li>
                      ))}

                    </ul>
                  </div>

                  {/* Threat Profile (if available) */}
                  {inc.threat_profile && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-slate-950/60 p-3 rounded-lg border border-slate-800/50 text-xs">
                      <div>
                        <span className="text-slate-400 block mb-1">Suspected Tools</span>
                        <div className="flex flex-wrap gap-1">
                          {inc.threat_profile.suspected_tools.map((t, idx) => (
                            <span key={idx} className="bg-slate-800 text-slate-200 px-2 py-0.5 rounded text-[11px] font-mono">
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="text-slate-400 block mb-1">Observed Capabilities</span>
                        <div className="flex flex-wrap gap-1">
                          {inc.threat_profile.capabilities.map((cap, idx) => (
                            <span key={idx} className="bg-slate-800 text-slate-200 px-2 py-0.5 rounded text-[11px]">
                              {cap}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="text-slate-400 block mb-1">Target Endpoints</span>
                        <div className="flex flex-wrap gap-1">
                          {inc.threat_profile.observed_targets.map((tgt, idx) => (
                            <span key={idx} className="bg-slate-800 text-amber-300 px-2 py-0.5 rounded text-[11px] font-mono">
                              {tgt}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Actionable Remediation Checklist */}
                  {inc.recommendations.length > 0 && (
                    <div>
                      <h5 className="text-xs font-medium text-slate-300 mb-1.5">Actionable Remediation Checklist</h5>
                      <div className="space-y-1">
                        {inc.recommendations.map((rec, idx) => (
                          <div key={idx} className="flex items-start space-x-2 text-xs text-slate-300 bg-slate-950/40 p-2 rounded border border-slate-800/40">
                            <span className="text-amber-400 font-bold">•</span>
                            <span>{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
