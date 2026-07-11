import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { BrowserRouter } from "react-router-dom";
import Landing from "../pages/Landing";
import Dashboard from "../pages/Dashboard";

describe("Landing and Dashboard placeholder render checks", () => {
  it("renders Landing component text", () => {
    render(
      <BrowserRouter>
        <Landing />
      </BrowserRouter>
    );
    expect(screen.getByText(/Universal Log Analytics/i)).toBeInTheDocument();
    expect(screen.getByText(/Platform Features/i)).toBeInTheDocument();
  });

  it("renders Dashboard component text", () => {
    render(<Dashboard />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText(/Real-time log analytics/i)).toBeInTheDocument();
  });
});
