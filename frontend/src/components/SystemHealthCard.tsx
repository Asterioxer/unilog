import React from 'react';
import type { SystemHealthScore, HealthSubScore } from '../types/api';


interface SystemHealthCardProps {
  health: SystemHealthScore;
}

const renderStatusBadge = (status: string) => {
  const isHealthy = status === 'HEALTHY';
  const isWarn = status === 'WARNING';
  const colorClass = isHealthy
    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    : isWarn
    ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
    : 'bg-rose-500/10 text-rose-400 border-rose-500/20';

  return (
    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${colorClass}`}>
      {status}
    </span>
  );
};

const renderGaugeBar = (label: string, sub: HealthSubScore) => {
  const barColor =
    sub.score >= 85 ? 'bg-emerald-500' : sub.score >= 60 ? 'bg-amber-500' : 'bg-rose-500';

  return (
    <div className="space-y-1.5" key={label}>
      <div className="flex justify-between items-center text-xs">
        <span className="font-medium text-slate-300">{label}</span>
        <span className="font-mono text-slate-400">{sub.score} / 100</span>
      </div>
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${barColor}`}
          style={{ width: `${Math.max(5, sub.score)}%` }}
        />
      </div>
      <p className="text-[11px] text-slate-400 truncate">{sub.summary}</p>
    </div>
  );
};

export const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ health }) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Environment System Health
          </h3>
          <p className="text-xs text-slate-400">Multi-domain operational score matrix</p>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-2xl font-bold font-mono text-slate-100">
            {health.overall_score} <span className="text-xs font-normal text-slate-400">/ 100</span>
          </span>
          {renderStatusBadge(health.status)}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {renderGaugeBar('Security', health.security)}
        {renderGaugeBar('Reliability', health.reliability)}
        {renderGaugeBar('Performance', health.performance)}
        {renderGaugeBar('Traffic', health.traffic)}
      </div>
    </div>
  );
};
