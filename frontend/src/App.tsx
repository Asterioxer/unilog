import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "./components/ThemeProvider";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import LogsTable from "./pages/LogsTable";
import DashboardLayout from "./layouts/DashboardLayout";

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
                    {/* Placeholder sub-routes for sidebar matches */}
                    <Route path="/rules" element={<Dashboard />} />
                    <Route path="/docs" element={<Dashboard />} />
                    <Route path="/settings" element={<Dashboard />} />
                    <Route path="/help" element={<Dashboard />} />
                  </Routes>
                </DashboardLayout>
              }
            />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
