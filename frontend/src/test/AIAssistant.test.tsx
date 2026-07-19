import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AIAssistant from "../components/AIAssistant";
import { apiService } from "../services/apiService";

vi.mock("../services/apiService", () => ({
  apiService: {
    explainLogs: vi.fn(),
  },
}));

describe("AIAssistant Component", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders empty state when no metrics are loaded", () => {
    render(<AIAssistant metrics={null} insights={[]} />);
    expect(screen.getByText("No Metrics Loaded")).toBeInTheDocument();
  });

  it("renders default call-to-action when metrics are present but not explained yet", () => {
    render(<AIAssistant metrics={{ some: "metrics" }} insights={[]} />);
    expect(screen.getByText("Interactive AI Diagnostic Report")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Generate AI Diagnostics/ })).toBeInTheDocument();
  });

  it("handles loading and successful generation of AI diagnostics", async () => {
    const mockResponse = {
      summary: "SQL Injection Attempts Blocked",
      explanation: "### Root Cause\nActive SQLi payload scans identified.",
      remediations: [
        {
          title: "Block Malicious IP",
          description: "Drop requests from source IP",
          code: "deny 1.2.3.4;",
          language: "nginx",
        },
      ],
    };

    vi.mocked(apiService.explainLogs).mockResolvedValueOnce(mockResponse);

    render(<AIAssistant metrics={{ traffic: 100 }} insights={[]} />);
    
    const generateBtn = screen.getByRole("button", { name: /Generate AI Diagnostics/ });
    fireEvent.click(generateBtn);

    expect(screen.getByText("Analyzing logs...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("SQL Injection Attempts Blocked")).toBeInTheDocument();
    });

    expect(screen.getByText("Diagnostic Report")).toBeInTheDocument();
    expect(screen.getByText("Root Cause")).toBeInTheDocument();
    expect(screen.getByText("Block Malicious IP")).toBeInTheDocument();
    expect(screen.getByText("deny 1.2.3.4;")).toBeInTheDocument();
  });
});
