import { Sun, Moon, Menu } from "lucide-react";
import { useTheme } from "../hooks/useTheme";
import { useLocation, Link } from "react-router-dom";

type HeaderProps = {
  onMobileMenuToggle: () => void;
};

export default function Header({ onMobileMenuToggle }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const location = useLocation();

  // Generate simple breadcrumbs from path
  const pathParts = location.pathname.split("/").filter(Boolean);
  const breadcrumbs = pathParts.map((part, index) => {
    const url = "/" + pathParts.slice(0, index + 1).join("/");
    const label = part.charAt(0).toUpperCase() + part.slice(1);
    return { label, url };
  });

  return (
    <header className="h-[65px] border-b border-border bg-card/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-4">
        {/* Mobile Menu trigger */}
        <button
          onClick={onMobileMenuToggle}
          className="lg:hidden p-2 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground"
          aria-label="Toggle Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Brand / Logo */}
        <Link to="/" className="text-xl font-bold tracking-tight text-primary flex items-center gap-2">
          unilog
        </Link>

        {/* Divider */}
        <span className="hidden sm:inline text-muted-foreground/30">|</span>

        {/* Breadcrumbs */}
        <nav className="hidden sm:flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
          <Link to="/" className="hover:text-foreground transition-colors">
            Home
          </Link>
          {breadcrumbs.map((crumb, idx) => (
            <div key={idx} className="flex items-center gap-1.5">
              <span>/</span>
              <Link
                to={crumb.url}
                className={idx === breadcrumbs.length - 1 ? "text-foreground font-semibold" : "hover:text-foreground transition-colors"}
              >
                {crumb.label}
              </Link>
            </div>
          ))}
        </nav>
      </div>

      {/* Utilities */}
      <div className="flex items-center gap-3">
        {/* Theme switcher */}
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="p-2 hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Toggle Theme"
        >
          {theme === "dark" ? <Sun className="h-5 w-5 text-amber-500" /> : <Moon className="h-5 w-5 text-indigo-500" />}
        </button>

        {/* User avatar indicator */}
        <div className="h-8 w-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm border border-primary/30">
          U
        </div>
      </div>
    </header>
  );
}
