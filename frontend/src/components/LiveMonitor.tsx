import { useState, useEffect, useRef } from "react";
import { Play, Pause, Terminal, Trash2, Wifi, WifiOff, Activity, ShieldAlert, Cpu } from "lucide-react";

interface LiveLogRecord {
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR";
  source_ip: string;
  method: string;
  path: string;
  status_code: number;
  size: number;
  user_agent: string;
  raw: string;
}

export default function LiveMonitor() {
  const [status, setStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected");
  const [logs, setLogs] = useState<LiveLogRecord[]>([]);
  const [streaming, setStreaming] = useState(true);
  const [rate, setRate] = useState(0.5);
  const [totalCount, setTotalCount] = useState(0);
  const [errorCount, setErrorCount] = useState(0);

  const socketRef = useRef<WebSocket | null>(null);
  const terminalEndRef = useRef<HTMLDivElement | null>(null);
  const autoScrollRef = useRef(true);

  // Connect to WebSocket
  const connectWebSocket = () => {
    if (socketRef.current) {
      if (
        socketRef.current.readyState === WebSocket.OPEN ||
        socketRef.current.readyState === WebSocket.CONNECTING
      ) {
        return;
      }
      try {
        socketRef.current.close();
      } catch {
        // ignore
      }
      socketRef.current = null;
    }
    
    setStatus("connecting");
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = window.location.hostname || "127.0.0.1";
    const wsUrl = `${wsProto}//${wsHost}:8002/api/v1/ws/live`;

    
    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        ws.send(JSON.stringify({ action: "rate", value: rate }));
      };

      ws.onmessage = (event) => {
        try {
          const record: LiveLogRecord = JSON.parse(event.data);
          setLogs((prev) => {
            const nextLogs = [...prev, record];
            if (nextLogs.length > 150) {
              nextLogs.shift(); // Keep buffer size within 150 records for rendering efficiency
            }
            return nextLogs;
          });
          setTotalCount((c) => c + 1);
          if (record.level === "ERROR" || record.level === "WARN") {
            setErrorCount((c) => c + 1);
          }
        } catch (err) {
          console.error("Failed to parse incoming live WebSocket frame:", err);
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket live stream connection error:", err);
        setStatus("disconnected");
        socketRef.current = null;
      };

      ws.onclose = () => {
        setStatus("disconnected");
        socketRef.current = null;
      };
    } catch (e) {
      console.error("Failed to establish WebSocket:", e);
      setStatus("disconnected");
      socketRef.current = null;
    }
  };

  const disconnectWebSocket = () => {
    if (socketRef.current) {
      try {
        socketRef.current.close();
      } catch {
        // ignore
      }
      socketRef.current = null;
    }
    setStatus("disconnected");
  };


  // Handle Play/Pause
  const toggleStreaming = () => {
    if (!socketRef.current) return;
    const nextStreaming = !streaming;
    setStreaming(nextStreaming);
    socketRef.current.send(
      JSON.stringify({ action: nextStreaming ? "resume" : "pause" })
    );
  };

  // Handle rate change
  const handleRateChange = (newRate: number) => {
    setRate(newRate);
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ action: "rate", value: newRate }));
    }
  };

  // Clear log logs
  const clearTerminal = () => {
    setLogs([]);
    setTotalCount(0);
    setErrorCount(0);
  };

  // Manage connection lifecycle
  useEffect(() => {
    connectWebSocket();
    return () => {
      disconnectWebSocket();
    };
  }, []);

  // Scroll to bottom helper
  useEffect(() => {
    if (autoScrollRef.current && terminalEndRef.current && typeof terminalEndRef.current.scrollIntoView === "function") {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  // Determine Level Colors
  const getLevelBadgeClass = (level: string) => {
    switch (level) {
      case "ERROR":
        return "text-red-500 bg-red-500/10 border-red-500/20";
      case "WARN":
        return "text-amber-500 bg-amber-500/10 border-amber-500/20";
      default:
        return "text-cyan-500 bg-cyan-500/10 border-cyan-500/20";
    }
  };

  const getStatusTextClass = (statusStr: string) => {
    switch (statusStr) {
      case "connected":
        return "text-emerald-500";
      case "connecting":
        return "text-amber-500";
      default:
        return "text-muted-foreground";
    }
  };

  const errorRatePct = totalCount > 0 ? ((errorCount / totalCount) * 100).toFixed(1) : "0.0";

  return (
    <div className="space-y-6">
      {/* Control Panel Header */}
      <div className="p-6 border border-border bg-card rounded-2xl shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl border border-border/40 ${status === "connected" ? "bg-emerald-500/10 text-emerald-500" : "bg-muted text-muted-foreground"}`}>
              <Activity className={`h-6 w-6 ${status === "connected" ? "animate-pulse" : ""}`} />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                Live Log Monitoring Mode
                <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border border-border/40 ${getLevelBadgeClass(status === "connected" ? "INFO" : "ERROR")}`}>
                  {status === "connected" ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                  <span className={getStatusTextClass(status)}>{status.toUpperCase()}</span>
                </span>
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Establish direct WebSocket streaming to capture, trace, and inspect operational log flows in real-time.
              </p>
            </div>
          </div>
          
          <div className="flex flex-wrap items-center gap-3">
            {/* Play/Pause Stream */}
            <button
              onClick={toggleStreaming}
              disabled={status !== "connected"}
              className="inline-flex items-center justify-center h-10 w-10 border border-border bg-card hover:bg-muted/40 rounded-xl transition-all disabled:opacity-40"
              title={streaming ? "Pause Stream" : "Resume Stream"}
            >
              {streaming ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 text-emerald-500" />}
            </button>
            
            {/* Rate controller */}
            <div className="flex items-center gap-2 px-3 h-10 border border-border bg-card rounded-xl">
              <span className="text-xs font-semibold text-muted-foreground">Interval:</span>
              <input
                type="range"
                min="0.1"
                max="2.0"
                step="0.1"
                value={rate}
                onChange={(e) => handleRateChange(parseFloat(e.target.value))}
                className="w-20 accent-primary"
                disabled={status !== "connected"}
              />
              <span className="text-xs font-mono font-semibold w-8 text-right">{rate}s</span>
            </div>

            {/* Clear console */}
            <button
              onClick={clearTerminal}
              className="inline-flex items-center gap-2 px-4 h-10 border border-border bg-card hover:bg-destructive/5 hover:text-destructive hover:border-destructive/20 rounded-xl font-semibold text-sm transition-all"
            >
              <Trash2 className="h-4 w-4" />
              Clear Console
            </button>

            {/* Disconnect / Connect */}
            <button
              onClick={status === "connected" ? disconnectWebSocket : connectWebSocket}
              disabled={status === "connecting"}
              className={`inline-flex items-center gap-2 px-5 h-10 font-semibold text-sm rounded-xl transition-all shadow-xs ${
                status === "connected" 
                  ? "bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive/15" 
                  : "bg-primary text-primary-foreground hover:bg-primary/95"
              }`}
            >
              {status === "connected" ? "Disconnect Stream" : "Connect Stream"}
            </button>
          </div>
        </div>
      </div>

      {/* Real-time metrics grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 border border-border bg-card rounded-2xl flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Stream Count</span>
            <h3 className="text-2xl font-black text-foreground mt-1">{totalCount}</h3>
          </div>
          <Terminal className="h-5 w-5 text-primary" />
        </div>
        <div className="p-5 border border-border bg-card rounded-2xl flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Error Rate</span>
            <h3 className={`text-2xl font-black mt-1 ${Number(errorRatePct) > 5 ? "text-destructive" : "text-foreground"}`}>
              {errorRatePct}%
            </h3>
          </div>
          <ShieldAlert className="h-5 w-5 text-amber-500" />
        </div>
        <div className="p-5 border border-border bg-card rounded-2xl flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Active Rule Evaluator</span>
            <h3 className="text-md font-bold text-emerald-500 mt-2">Active in Background</h3>
          </div>
          <Cpu className="h-5 w-5 text-emerald-500" />
        </div>
      </div>

      {/* Terminal Output */}
      <div className="border border-border bg-zinc-950 rounded-2xl overflow-hidden shadow-md flex flex-col h-[450px]">
        {/* Terminal Header */}
        <div className="px-5 py-3 border-b border-zinc-800 bg-zinc-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <span className="h-3 w-3 rounded-full bg-red-500/60" />
              <span className="h-3 w-3 rounded-full bg-yellow-500/60" />
              <span className="h-3 w-3 rounded-full bg-green-500/60" />
            </div>
            <span className="font-mono text-xs text-zinc-400 font-semibold ml-2">unilog@tail-stream:~</span>
          </div>
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={autoScrollRef.current}
              onChange={(e) => { autoScrollRef.current = e.target.checked; }}
              className="accent-primary h-3.5 w-3.5 rounded-sm"
            />
            <span className="text-xs font-mono text-zinc-400">Auto-Scroll</span>
          </label>
        </div>

        {/* Terminal logs list */}
        <div className="flex-1 p-5 overflow-y-auto font-mono text-xs text-zinc-300 space-y-2.5">
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <div key={index} className="flex items-start gap-3 hover:bg-zinc-900/50 p-1 rounded-sm transition-colors">
                <span className="text-zinc-500 shrink-0">[{log.timestamp.substring(11, 19)}]</span>
                <span className={`px-1.5 py-0.5 rounded-xs text-[10px] font-bold border ${getLevelBadgeClass(log.level)} shrink-0`}>
                  {log.level}
                </span>
                <span className="text-zinc-400 font-semibold shrink-0">{log.source_ip}</span>
                <span className="text-zinc-100 flex-1 break-all">{log.raw}</span>
              </div>
            ))
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-zinc-500 text-center space-y-3">
              <Terminal className="h-10 w-10 opacity-30 animate-pulse" />
              <p>Console idle. Click "Connect Stream" to begin monitoring.</p>
            </div>
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
}
