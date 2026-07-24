import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Landing from "../pages/Landing";
import Dashboard from "../pages/Dashboard";
import CustomRulesPage from "../pages/CustomRulesPage";
import ApiReferencePage from "../pages/ApiReferencePage";
import SettingsPage from "../pages/SettingsPage";
import HelpCenterPage from "../pages/HelpCenterPage";

describe("Landing and Dashboard placeholder render checks", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
  });

  it("renders Landing component text", () => {
    render(
      <BrowserRouter>
        <Landing />
      </BrowserRouter>
    );
    expect(screen.getByText(/Universal Log Analytics/i)).toBeInTheDocument();
    expect(screen.getByText(/Platform Features/i)).toBeInTheDocument();
  });

  it("renders Dashboard component inputs, formats dropdown, and trigger buttons", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText("Log Analytics Overview")).toBeInTheDocument();
    expect(screen.getByText("File Uploader")).toBeInTheDocument();
    expect(screen.getByText("Raw Text Dump")).toBeInTheDocument();
    expect(screen.getByText("Run Analytics")).toBeInTheDocument();
  });

  it("renders CustomRulesPage correctly", () => {
    render(<CustomRulesPage />);
    expect(screen.getByText(/Built-in & Custom Analytics Rules/i)).toBeInTheDocument();
    expect(screen.getByText("Sensitive Path Reconnaissance Probe")).toBeInTheDocument();
  });

  it("renders ApiReferencePage correctly", () => {
    render(<ApiReferencePage />);
    expect(screen.getByText(/REST API & WebSocket Reference/i)).toBeInTheDocument();
    expect(screen.getByText("Swagger UI Docs")).toBeInTheDocument();
  });

  it("renders SettingsPage correctly", () => {
    render(<SettingsPage />);
    expect(screen.getByText(/Application Preferences & Environment Settings/i)).toBeInTheDocument();
    expect(screen.getByText("Save Settings")).toBeInTheDocument();
  });

  it("renders HelpCenterPage correctly", () => {
    render(<HelpCenterPage />);
    expect(screen.getByText(/Help Center & Documentation Guide/i)).toBeInTheDocument();
    expect(screen.getByText("Frequently Asked Questions")).toBeInTheDocument();
  });
});

