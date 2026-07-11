import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Landing from "../pages/Landing";
import Dashboard from "../pages/Dashboard";

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

  it("toggles dashboard tabs to raw text input area on header tab click", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      </QueryClientProvider>
    );

    const pasteTab = screen.getByText("Raw Text Dump");
    
    await act(async () => {
      pasteTab.click();
    });

    // Check textarea presence
    expect(screen.getByPlaceholderText(/Paste logs here/i)).toBeInTheDocument();
  });
});
