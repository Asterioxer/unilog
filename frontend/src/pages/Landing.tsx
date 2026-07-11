import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { 
  ArrowRight, ShieldCheck, Zap, BarChart3, Puzzle, Layers, Cpu, Code
} from "lucide-react";

export default function Landing() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 100 } }
  };

  const formats = [
    { name: "JSON Lines", desc: "Structured log objects per line" },
    { name: "Nginx Access Log", desc: "Combined HTTP access records" },
    { name: "Apache Web Log", desc: "Common/Combined web formats" },
    { name: "Syslog Standard", desc: "RFC3164 service log outputs" },
    { name: "Django logs", desc: "Application execution logs" },
    { name: "Windows Event Logs", desc: "Standard Windows Security XML/Text" },
    { name: "Custom Log Formats", desc: "User-defined regex structures" }
  ];

  const features = [
    {
      icon: <Zap className="h-6 w-6 text-purple-500" />,
      title: "Stream-First Processing",
      description: "Uses generator functions to process logs line-by-line, preventing memory bloating and supporting gigabyte-scale logs."
    },
    {
      icon: <Cpu className="h-6 w-6 text-blue-500" />,
      title: "Intelligent Auto-Detection",
      description: "Dynamically runs samples against registered log syntax heuristics and rates format probability rankings in real time."
    },
    {
      icon: <BarChart3 className="h-6 w-6 text-emerald-500" />,
      title: "Instant Analytics",
      description: "Generates rich response metadata, aggregate counts by HTTP code patterns, bytes transferred, top client IPs, and critical error rates."
    },
    {
      icon: <Puzzle className="h-6 w-6 text-orange-500" />,
      title: "Decoupled Plugin Registry",
      description: "Extend unilog instantly with custom syntax rules using simple Python class decorators (@register_parser)."
    },
    {
      icon: <Layers className="h-6 w-6 text-pink-500" />,
      title: "Background Task Engine",
      description: "Handles heavy files (>1MB) asynchronously with background workers, notifying UI of task completion dynamically."
    },
    {
      icon: <ShieldCheck className="h-6 w-6 text-violet-500" />,
      title: "Enterprise Hardening",
      description: "FastAPI gateway featuring rate limiters (100 req/min), strict schemas, gzip compression, and security headers built-in."
    }
  ];

  return (
    <div className="bg-background text-foreground min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 px-6 sm:py-32 lg:px-8 border-b border-border bg-radial-[at_top_right,_var(--color-primary-foreground)_0%,_transparent_50%]">
        <motion.div 
          className="mx-auto max-w-4xl text-center"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/10 text-xs font-semibold text-primary mb-6">
            <span className="flex h-2 w-2 rounded-full bg-primary animate-pulse" />
            V0.2.0 API Live & Pinned
          </motion.div>
          <motion.h1 
            variants={itemVariants}
            className="text-4xl font-extrabold tracking-tight sm:text-6xl text-balance"
          >
            Universal Log Analytics <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-600">
              Made Simple and Lightweight
            </span>
          </motion.h1>
          <motion.p 
            variants={itemVariants}
            className="mt-6 text-lg leading-8 text-muted-foreground max-w-2xl mx-auto text-pretty"
          >
            Auto-detect log types, run instant metrics calculations, and stream parsed records through a clean REST platform.
          </motion.p>
          <motion.div 
            variants={itemVariants}
            className="mt-10 flex items-center justify-center gap-x-6"
          >
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-xs hover:bg-primary/95 hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              Analyze Logs Now
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="https://github.com/Asterioxer/unilog"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-5 py-3 text-sm font-semibold hover:bg-muted transition-colors"
            >
              <Code className="h-4 w-4" />
              View on GitHub
            </a>
          </motion.div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6 max-w-7xl mx-auto">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Platform Features</h2>
          <p className="mt-4 text-muted-foreground">
            A reliable structure designed for streaming logs efficiently at high speed.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, idx) => (
            <motion.div
              key={idx}
              className="p-6 rounded-xl border border-border bg-card shadow-xs hover:shadow-md hover:border-primary/20 transition-all duration-300 flex flex-col gap-4"
              whileHover={{ y: -4 }}
            >
              <div className="p-3 rounded-lg bg-muted w-fit">
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold tracking-tight">{feature.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Supported Formats */}
      <section className="py-20 px-6 border-t border-border bg-card/50">
        <div className="max-w-7xl mx-auto">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Supported Formats</h2>
            <p className="mt-4 text-muted-foreground">
              Built-in support for standard configurations plus extensible API compatibility.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {formats.map((format, idx) => (
              <div
                key={idx}
                className="p-5 rounded-lg border border-border bg-card flex flex-col gap-2 hover:border-primary/30 transition-colors"
              >
                <span className="font-semibold text-primary text-sm">{format.name}</span>
                <span className="text-xs text-muted-foreground leading-normal">{format.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack Footer */}
      <section className="py-16 px-6 border-t border-border text-center max-w-5xl mx-auto">
        <h3 className="text-sm font-semibold tracking-wider text-muted-foreground uppercase mb-8">
          Powered by modern software standards
        </h3>
        <div className="flex flex-wrap justify-center gap-8 text-muted-foreground font-medium text-sm">
          <span>FastAPI</span>
          <span>React 19</span>
          <span>TypeScript</span>
          <span>TailwindCSS v4</span>
          <span>TanStack Query</span>
          <span>Recharts</span>
        </div>
      </section>
    </div>
  );
}
