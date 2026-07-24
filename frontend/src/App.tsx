import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "./components/ThemeProvider";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import LogsTable from "./pages/LogsTable";
import CustomRulesPage from "./pages/CustomRulesPage";
import ApiReferencePage from "./pages/ApiReferencePage";
import SettingsPage from "./pages/SettingsPage";
import HelpCenterPage from "./pages/HelpCenterPage";
import DashboardLayout from "./layouts/DashboardLayout";
import { ErrorBoundary } from "./components/ErrorBoundary";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider defaultTheme="system" storageKey="unilog-ui-theme">
          <BrowserRouter>
            <Routes>
              {/* Landing Experience Page */}
              <Route path="/" element={<Landing />} />

              {/* Dashboard Shell Routes */}
              <Route
                path="/dashboard/*"
                element={
                  <DashboardLayout>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      {/* Log Explorer Table subroute */}
                      <Route path="/logs" element={<LogsTable />} />
                      {/* Dedicated sidebar sub-routes */}
                      <Route path="/rules" element={<CustomRulesPage />} />
                      <Route path="/docs" element={<ApiReferencePage />} />
                      <Route path="/settings" element={<SettingsPage />} />
                      <Route path="/help" element={<HelpCenterPage />} />
                    </Routes>
                  </DashboardLayout>
                }
              />
            </Routes>
          </BrowserRouter>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

