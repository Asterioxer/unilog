import { useState } from "react";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";

type DashboardLayoutProps = {
  children: React.ReactNode;
};

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <Header onMobileMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)} />

      <div className="flex flex-1 relative">
        {/* Desktop Sidebar (hidden on mobile, shown on lg) */}
        <Sidebar className="hidden lg:flex" />

        {/* Mobile Drawer Backdrop */}
        {isMobileMenuOpen && (
          <div 
            className="fixed inset-0 bg-background/80 backdrop-blur-xs z-40 lg:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}

        {/* Mobile Sidebar (shown off-canvas) */}
        <Sidebar 
          className={`fixed top-[65px] left-0 h-[calc(100vh-65px)] z-50 transition-transform duration-300 lg:hidden ${
            isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        />

        {/* Main Content Area */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
