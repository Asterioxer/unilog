import { useState } from "react";
import { Settings, Save, RefreshCw, Moon, Sun, Monitor, HardDrive, Check } from "lucide-react";
import { useTheme } from "../components/ThemeProvider";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [apiUrl, setApiUrl] = useState("http://127.0.0.1:8002");
  const [maxBuffer, setMaxBuffer] = useState(150);
  const [autoScrollDefault, setAutoScrollDefault] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    localStorage.setItem("unilog_custom_api_url", apiUrl);
    localStorage.setItem("unilog_max_buffer", maxBuffer.toString());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    localStorage.clear();
    setApiUrl("http://127.0.0.1:8002");
    setMaxBuffer(150);
    setAutoScrollDefault(true);
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="p-6 border border-border bg-card rounded-2xl shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Settings className="h-5 w-5 text-primary" />
              Application Preferences & Environment Settings
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Configure backend connection endpoints, theme preferences, live streaming buffers, and client storage.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleSave}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground font-semibold text-sm rounded-xl hover:bg-primary/95 transition-all shadow-xs"
            >
              {saved ? <Check className="h-4 w-4 text-emerald-300" /> : <Save className="h-4 w-4" />}
              {saved ? "Saved Changes!" : "Save Settings"}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Appearance Settings */}
        <div className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
          <h3 className="text-base font-bold text-foreground flex items-center gap-2">
            <Sun className="h-4 w-4 text-primary" />
            Theme & Appearance
          </h3>
          <p className="text-xs text-muted-foreground">
            Select interface theme mode across dark, light, or operating system preferences.
          </p>

          <div className="grid grid-cols-3 gap-3 pt-2">
            {[
              { id: "dark", label: "Dark", icon: <Moon className="h-4 w-4" /> },
              { id: "light", label: "Light", icon: <Sun className="h-4 w-4" /> },
              { id: "system", label: "System", icon: <Monitor className="h-4 w-4" /> },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTheme(t.id as "dark" | "light" | "system")}
                className={`flex flex-col items-center justify-center p-4 border rounded-xl gap-2 transition-all ${
                  theme === t.id
                    ? "border-primary bg-primary/10 text-primary font-bold"
                    : "border-border bg-muted/30 text-muted-foreground hover:bg-muted"
                }`}
              >
                {t.icon}
                <span className="text-xs">{t.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Backend Endpoint Settings */}
        <div className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
          <h3 className="text-base font-bold text-foreground flex items-center gap-2">
            <HardDrive className="h-4 w-4 text-primary" />
            API Host Target
          </h3>
          <p className="text-xs text-muted-foreground">
            Configure the target REST & WebSocket backend service URL.
          </p>

          <div className="space-y-2 pt-2">
            <label className="text-xs font-semibold text-foreground block">
              FastAPI Service Base URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full px-3 py-2 border border-border bg-muted/40 rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
        </div>

        {/* Live Stream Settings */}
        <div className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
          <h3 className="text-base font-bold text-foreground flex items-center gap-2">
            <RefreshCw className="h-4 w-4 text-primary" />
            Live Stream Buffer Limits
          </h3>
          <p className="text-xs text-muted-foreground">
            Control terminal scroll buffer memory size to balance browser rendering performance.
          </p>

          <div className="space-y-4 pt-2">
            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span>Max Terminal Records Buffer:</span>
                <span className="font-mono font-bold text-primary">{maxBuffer} records</span>
              </div>
              <input
                type="range"
                min="50"
                max="500"
                step="25"
                value={maxBuffer}
                onChange={(e) => setMaxBuffer(parseInt(e.target.value))}
                className="w-full accent-primary"
              />
            </div>

            <label className="flex items-center gap-3 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={autoScrollDefault}
                onChange={(e) => setAutoScrollDefault(e.target.checked)}
                className="accent-primary h-4 w-4 rounded-sm"
              />
              <span className="text-xs text-foreground font-medium">Auto-scroll terminal to bottom by default</span>
            </label>
          </div>
        </div>

        {/* Cache & Local Data Reset */}
        <div className="p-6 border border-border bg-card rounded-2xl space-y-4 shadow-xs">
          <h3 className="text-base font-bold text-foreground">
            Clear Client Cache & Reset
          </h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Reset local storage preferences, clear cached log analysis outputs, and restore system defaults.
          </p>

          <div className="pt-2">
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive/15 font-semibold text-xs rounded-xl transition-all"
            >
              Reset All Local Preferences
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
