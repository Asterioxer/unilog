import { useState } from "react";
import { Code2, ShieldAlert, Zap, Activity, Search, Sliders, Info } from "lucide-react";


interface RuleItem {
  id: string;
  name: string;
  category: "security" | "reliability" | "performance" | "traffic";
  severity: "critical" | "high" | "medium" | "low" | "info";
  description: string;
  threshold: string;
  enabled: boolean;
}

const BUILTIN_RULES: RuleItem[] = [
  {
    id: "sec-scan-04",
    name: "Sensitive Path Reconnaissance Probe",
    category: "security",
    severity: "high",
    description: "Detects unauthorized attempts to probe sensitive administrative paths like /.env, /wp-admin, /config.php, or backup archives.",
    threshold: ">= 2 probe hits within log window",
    enabled: true,
  },
  {
    id: "sec-bot-01",
    name: "Headless Browser Automation Fingerprint",
    category: "security",
    severity: "medium",
    description: "Identifies requests originating from headless automation engines (Playwright, Puppeteer, Selenium, PhantomJS).",
    threshold: "Headless User-Agent pattern match",
    enabled: true,
  },
  {
    id: "sec-enum-03",
    name: "Directory Enumeration & High 404 Ratio",
    category: "security",
    severity: "high",
    description: "Flags clients generating abnormal 404 error ratios exceeding 30% of their total requested URLs.",
    threshold: "404 ratio > 30% & total requests >= 5",
    enabled: true,
  },
  {
    id: "sec-brute-02",
    name: "Authentication Brute-Force Campaign",
    category: "security",
    severity: "critical",
    description: "Detects repeated failed POST requests (401/403) targeting authentication endpoints.",
    threshold: ">= 3 failed login attempts from single IP",
    enabled: true,
  },
  {
    id: "rel-err-01",
    name: "Elevated Server 5xx Failure Rate",
    category: "reliability",
    severity: "critical",
    description: "Monitors application health when HTTP 5xx internal server errors exceed 5% of total traffic.",
    threshold: "5xx error rate > 5.0%",
    enabled: true,
  },
  {
    id: "perf-lat-01",
    name: "High P99 Latency SLA Breach",
    category: "performance",
    severity: "medium",
    description: "Triggers when 99th percentile response latency crosses SLA limits of 500ms.",
    threshold: "P99 latency > 500ms",
    enabled: true,
  },
  {
    id: "traffic-spike-01",
    name: "Abnormal Traffic Burst Anomaly",
    category: "traffic",
    severity: "low",
    description: "Identifies sudden request volume surges exceeding 2.5x the rolling baseline throughput.",
    threshold: "Throughput > 2.5x baseline",
    enabled: true,
  },
];

export default function CustomRulesPage() {
  const [rules, setRules] = useState<RuleItem[]>(BUILTIN_RULES);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  const toggleRule = (id: string) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r))
    );
  };

  const filteredRules = rules.filter((r) => {
    const matchesSearch =
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.id.toLowerCase().includes(search.toLowerCase()) ||
      r.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory =
      selectedCategory === "all" || r.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "critical":
        return "bg-red-500/10 text-red-500 border-red-500/20";
      case "high":
        return "bg-amber-500/10 text-amber-500 border-amber-500/20";
      case "medium":
        return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
      default:
        return "bg-cyan-500/10 text-cyan-500 border-cyan-500/20";
    }
  };

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case "security":
        return <ShieldAlert className="h-4 w-4 text-amber-500" />;
      case "reliability":
        return <Zap className="h-4 w-4 text-red-500" />;
      case "performance":
        return <Activity className="h-4 w-4 text-cyan-500" />;
      default:
        return <Code2 className="h-4 w-4 text-purple-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="p-6 border border-border bg-card rounded-2xl shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Code2 className="h-5 w-5 text-primary" />
              Built-in & Custom Analytics Rules
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Inspect, toggle, and configure deterministic rule triggers across security, performance, reliability, and traffic dimensions.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-3 py-1.5 rounded-xl bg-primary/10 text-primary border border-primary/20 font-semibold">
              {rules.filter((r) => r.enabled).length} / {rules.length} Rules Active
            </span>
          </div>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search rules by ID, name, signature..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-border bg-card rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <Sliders className="h-4 w-4 text-muted-foreground shrink-0" />
          {["all", "security", "reliability", "performance", "traffic"].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all shrink-0 ${
                selectedCategory === cat
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted/50 text-muted-foreground hover:bg-muted"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredRules.map((rule) => (
          <div
            key={rule.id}
            className={`p-5 border rounded-2xl transition-all bg-card ${
              rule.enabled ? "border-border shadow-xs" : "border-border/40 opacity-60"
            }`}
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-muted/60">
                  {getCategoryIcon(rule.category)}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                    {rule.name}
                  </h3>
                  <span className="text-[11px] font-mono text-muted-foreground">
                    {rule.id}
                  </span>
                </div>
              </div>

              <button
                onClick={() => toggleRule(rule.id)}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  rule.enabled ? "bg-primary" : "bg-muted"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    rule.enabled ? "translate-x-4" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed mb-4">
              {rule.description}
            </p>

            <div className="flex items-center justify-between pt-3 border-t border-border/40 text-xs">
              <div className="flex items-center gap-1.5 font-mono text-muted-foreground">
                <Info className="h-3.5 w-3.5" />
                <span>{rule.threshold}</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono uppercase border ${getSeverityBadge(
                  rule.severity
                )}`}
              >
                {rule.severity}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
