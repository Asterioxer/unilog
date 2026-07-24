import { HelpCircle, FileText, Cpu, ExternalLink, ShieldCheck, Zap } from "lucide-react";


export default function HelpCenterPage() {
  const faqs = [
    {
      question: "Which log formats does unilog automatically support?",
      answer: "unilog auto-detects Nginx/Apache Combined & Common Log Format, W3C IIS Logs, Windows Event Log CSV/XML, Syslog RFC5424/RFC3164, JSON Logfmt, and Custom Delimited formats using multi-tier confidence score heuristics."
    },
    {
      question: "How does the Heuristic Auto-Detection scoring engine work?",
      answer: "When a log payload is submitted, unilog runs every registered parser against a 50-line sample. Each parser computes a confidence score (0.0 to 1.0) based on header regex patterns and line structure matches. The candidate with highest score is selected automatically."
    },
    {
      question: "What is the difference between Raw Insights and Correlated Incidents?",
      answer: "Raw Insights represent individual rule alerts (e.g. 404 ratio breach). The Release 10 Incident Correlator groups co-occurring raw alerts within a time window into unified Incident objects (e.g. INC-20260724-001) complete with evidence rationales and threat profiles."
    },
    {
      question: "How do I stream live logs from my production server?",
      answer: "You can open a WebSocket connection to /api/v1/ws/live or configure your log agent (Filebeat, Vector, FluentBit) to forward events directly to unilog REST ingest endpoints."
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="p-6 border border-border bg-card rounded-2xl shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <HelpCircle className="h-5 w-5 text-primary" />
              Help Center & Documentation Guide
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Learn how to utilize unilog parsers, configure custom detection rules, troubleshoot streaming pipelines, and integrate with CI/CD.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/Asterioxer/unilog"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 border border-border bg-card hover:bg-muted text-foreground font-semibold text-sm rounded-xl transition-all shadow-xs"
            >
              <ExternalLink className="h-4 w-4" />
              GitHub Repository
              <ExternalLink className="h-3.5 w-3.5" />

            </a>
          </div>
        </div>
      </div>

      {/* Feature Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 border border-border bg-card rounded-2xl space-y-3 shadow-xs">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary w-fit">
            <FileText className="h-5 w-5" />
          </div>
          <h3 className="text-base font-bold text-foreground">Supported Log Formats</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Full support for Web Servers (Nginx, Apache, IIS), Systems (Syslog, Windows Events), and Cloud Microservices (JSON logfmt).
          </p>
        </div>

        <div className="p-6 border border-border bg-card rounded-2xl space-y-3 shadow-xs">
          <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-500 w-fit">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <h3 className="text-base font-bold text-foreground">Threat Intelligence</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Automatic signature matching for SQL Injections, XSS, Scanner Probes (Nikto), Headless Automation (Playwright), and Brute Force.
          </p>
        </div>

        <div className="p-6 border border-border bg-card rounded-2xl space-y-3 shadow-xs">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-500 w-fit">
            <Zap className="h-5 w-5" />
          </div>
          <h3 className="text-base font-bold text-foreground">AI SRE Assistant</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Generates root-cause analysis reports, incident timelines, and copyable Nginx/SQL/Iptables remediation snippets.
          </p>
        </div>
      </div>

      {/* FAQ Accordion */}
      <div className="p-6 border border-border bg-card rounded-2xl space-y-6 shadow-xs">
        <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
          <Cpu className="h-5 w-5 text-primary" />
          Frequently Asked Questions
        </h3>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div key={index} className="p-4 border border-border/60 bg-muted/20 rounded-xl space-y-2">
              <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
                <span className="text-primary font-mono text-xs">Q{index + 1}.</span>
                {faq.question}
              </h4>
              <p className="text-xs text-muted-foreground leading-relaxed pl-6">
                {faq.answer}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
