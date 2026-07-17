import { Shield, ShieldAlert, ShieldCheck, AlertOctagon, Key, Server, Terminal, Ban } from "lucide-react";
import type { SecurityMetrics } from "../types/api";

interface SecurityObserverProps {
  securityMetrics: SecurityMetrics | null;
  isProcessing?: boolean;
}

export default function SecurityObserver({ 
  securityMetrics, 
  isProcessing = false 
}: SecurityObserverProps) {
  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border border-border bg-card rounded-xl">
        <div className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-muted-foreground">Evaluating security intelligence rules...</p>
      </div>
    );
  }

  if (!securityMetrics) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-border bg-muted/20 rounded-xl">
        <Shield className="h-10 w-10 text-muted-foreground/60 mb-4" />
        <h3 className="text-base font-bold text-foreground">No Security Data Available</h3>
        <p className="text-sm text-muted-foreground mt-1 max-w-sm">
          Run an analytics session with log text or upload files to evaluate security threat signatures.
        </p>
      </div>
    );
  }

  const { brute_force, enumeration, bot_metrics, scanner_metrics, injection_metrics } = securityMetrics;

  const totalInjections = 
    injection_metrics.sql_injection_count +
    injection_metrics.xss_injection_count +
    injection_metrics.path_traversal_count +
    injection_metrics.rce_cmd_injection_count;

  // Determine overall Threat Level
  let threatColor = "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
  let threatIcon = <ShieldCheck className="h-8 w-8 text-emerald-500" />;
  let threatLabel = "Low Risk Profile";
  let threatDesc = "No critical injection patterns or active brute force lockouts identified.";

  if (totalInjections > 0 || brute_force.lockout_candidates_count > 0) {
    threatColor = "text-destructive bg-destructive/10 border-destructive/20";
    threatIcon = <AlertOctagon className="h-8 w-8 text-destructive animate-pulse" />;
    threatLabel = "Critical Security Alert";
    threatDesc = "Active code injection attempts or account brute-force lockouts have been detected.";
  } else if (scanner_metrics.scanner_hits_count > 0 || enumeration.error_404_ratio > 15) {
    threatColor = "text-orange-500 bg-orange-500/10 border-orange-500/20";
    threatIcon = <ShieldAlert className="h-8 w-8 text-orange-500" />;
    threatLabel = "High Scanning Activity";
    threatDesc = "Active vulnerability scanning probes or high 404 error ratios observed.";
  } else if (bot_metrics.headless_fingerprints_count > 0 || brute_force.failure_ratio > 20) {
    threatColor = "text-yellow-600 bg-yellow-600/10 border-yellow-600/20";
    threatIcon = <ShieldAlert className="h-8 w-8 text-yellow-600" />;
    threatLabel = "Suspicious Bot Behavior";
    threatDesc = "Headless browser automated signatures or moderate authentication failures detected.";
  }

  // Scanner Probe paths
  const scannedIpsList = Object.entries(scanner_metrics.scanned_ips)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  // Lockout Candidate list
  const lockoutList = brute_force.lockout_candidates;

  return (
    <div className="space-y-8">
      {/* Dynamic Threat Level Indicator Card */}
      <div className={`border p-6 rounded-xl flex items-start gap-5 shadow-xs transition-all ${threatColor}`}>
        <div className="p-3 bg-background/50 rounded-xl shadow-xs">
          {threatIcon}
        </div>
        <div className="space-y-1">
          <h3 className="text-lg font-extrabold tracking-tight">{threatLabel}</h3>
          <p className="text-sm font-medium opacity-90">{threatDesc}</p>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="border border-border bg-card p-5 rounded-xl flex items-center gap-4 shadow-xs">
          <div className="p-3 bg-red-500/10 text-red-500 rounded-lg">
            <Terminal className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Injection Hits</p>
            <p className="text-2xl font-bold text-foreground mt-0.5">{totalInjections}</p>
          </div>
        </div>

        <div className="border border-border bg-card p-5 rounded-xl flex items-center gap-4 shadow-xs">
          <div className="p-3 bg-orange-500/10 text-orange-500 rounded-lg">
            <Server className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Scanner Probes</p>
            <p className="text-2xl font-bold text-foreground mt-0.5">{scanner_metrics.scanner_hits_count}</p>
          </div>
        </div>

        <div className="border border-border bg-card p-5 rounded-xl flex items-center gap-4 shadow-xs">
          <div className="p-3 bg-yellow-500/10 text-yellow-600 rounded-lg">
            <Key className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Failed Logins</p>
            <p className="text-2xl font-bold text-foreground mt-0.5">{brute_force.failure_ratio.toFixed(1)}%</p>
          </div>
        </div>

        <div className="border border-border bg-card p-5 rounded-xl flex items-center gap-4 shadow-xs">
          <div className="p-3 bg-blue-500/10 text-blue-500 rounded-lg">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Headless Bots</p>
            <p className="text-2xl font-bold text-foreground mt-0.5">{bot_metrics.headless_fingerprints_count}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Code Injection Signatures Breakdown */}
        <div className="border border-border bg-card rounded-xl p-6 shadow-xs space-y-5">
          <div>
            <h3 className="text-base font-bold text-foreground">Code Injection Indicators</h3>
            <p className="text-xs text-muted-foreground">Attempts to inject executable code or escape path constraints.</p>
          </div>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-bold">
                <span>SQL Injection (SQLi)</span>
                <span className="text-red-500">{injection_metrics.sql_injection_count} hits</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-red-500 transition-all duration-500" 
                  style={{ width: `${Math.min((injection_metrics.sql_injection_count / 10) * 100, 100)}%` }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-bold">
                <span>Cross-Site Scripting (XSS)</span>
                <span className="text-red-500">{injection_metrics.xss_injection_count} hits</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-red-500 transition-all duration-500" 
                  style={{ width: `${Math.min((injection_metrics.xss_injection_count / 10) * 100, 100)}%` }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-bold">
                <span>Directory Path Traversal</span>
                <span className="text-orange-500">{injection_metrics.path_traversal_count} hits</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-orange-500 transition-all duration-500" 
                  style={{ width: `${Math.min((injection_metrics.path_traversal_count / 10) * 100, 100)}%` }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-bold">
                <span>Remote Code Execution (RCE)</span>
                <span className="text-red-600">{injection_metrics.rce_cmd_injection_count} hits</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-red-600 transition-all duration-500" 
                  style={{ width: `${Math.min((injection_metrics.rce_cmd_injection_count / 5) * 100, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Vulnerability Scanner Probes */}
        <div className="border border-border bg-card rounded-xl p-6 shadow-xs space-y-4">
          <div>
            <h3 className="text-base font-bold text-foreground">Top Vulnerability Probing IPs</h3>
            <p className="text-xs text-muted-foreground">Remote hosts requesting admin endpoints, env files, or WordPress logins.</p>
          </div>
          {scannedIpsList.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground border border-dashed border-border rounded-xl">
              <ShieldCheck className="h-8 w-8 text-emerald-500/60 mb-2" />
              <span className="text-xs font-semibold">No probe activity detected</span>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {scannedIpsList.map(([ip, count]) => (
                <div key={ip} className="py-3 flex justify-between items-center text-xs font-semibold">
                  <span className="font-mono text-muted-foreground">{ip}</span>
                  <span className="bg-orange-500/10 text-orange-600 border border-orange-500/20 px-2 py-0.5 rounded-full font-bold">
                    {count} probe hits
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Brute Force Candidate Block */}
      <div className="border border-border bg-card rounded-xl p-6 shadow-xs space-y-4">
        <div>
          <h3 className="text-base font-bold text-foreground">Lockout Candidates & Auth Spikes</h3>
          <p className="text-xs text-muted-foreground">IP addresses flagged for abnormally high login failure counts.</p>
        </div>
        {lockoutList.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground border border-dashed border-border rounded-xl">
            <ShieldCheck className="h-8 w-8 text-emerald-500/60 mb-2" />
            <span className="text-xs font-semibold">No login lockout thresholds exceeded</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {lockoutList.map((ip) => (
              <div key={ip} className="bg-destructive/5 border border-destructive/20 p-4 rounded-xl flex items-center gap-3">
                <div className="p-2 bg-destructive/15 text-destructive rounded-lg">
                  <Ban className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-mono text-xs font-bold text-foreground">{ip}</div>
                  <div className="text-[10px] text-destructive font-bold uppercase tracking-wide mt-0.5">Threshold Lockout</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
