import { Link, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, FileText, Code2, BookOpen, Settings, HelpCircle
} from "lucide-react";

type SidebarProps = {
  className?: string;
};

export default function Sidebar({ className = "" }: SidebarProps) {
  const location = useLocation();

  const navItems = [
    { label: "Overview", path: "/dashboard", icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: "Parsed Logs", path: "/dashboard/logs", icon: <FileText className="h-4 w-4" /> },
    { label: "Custom Rules", path: "/dashboard/rules", icon: <Code2 className="h-4 w-4" /> },
    { label: "API Reference", path: "/dashboard/docs", icon: <BookOpen className="h-4 w-4" /> },
  ];

  const bottomItems = [
    { label: "Settings", path: "/dashboard/settings", icon: <Settings className="h-4 w-4" /> },
    { label: "Help Center", path: "/dashboard/help", icon: <HelpCircle className="h-4 w-4" /> },
  ];

  return (
    <aside className={`w-64 border-r border-border bg-card flex flex-col justify-between h-[calc(100vh-65px)] sticky top-[65px] ${className}`}>
      {/* Navigation Links */}
      <div className="px-4 py-6 flex-1 flex flex-col gap-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive 
                  ? "bg-primary/10 text-primary border-l-2 border-primary rounded-l-none" 
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {item.icon}
              {item.label}
            </Link>
          );
        })}
      </div>

      {/* Bottom Config Items */}
      <div className="px-4 py-6 border-t border-border flex flex-col gap-1">
        {bottomItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive 
                  ? "bg-primary/10 text-primary" 
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {item.icon}
              {item.label}
            </Link>
          );
        })}
      </div>
    </aside>
  );
}
