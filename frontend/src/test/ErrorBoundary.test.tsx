import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ErrorBoundary } from "../components/ErrorBoundary";

function ProblemComponent() {
  throw new Error("Triggered runtime crash");
  return <div>Error fallback mock</div>;
}

describe("ErrorBoundary component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders children successfully when no errors are present", () => {
    render(
      <ErrorBoundary>
        <div data-testid="ok-child">Healthy</div>
      </ErrorBoundary>
    );

    expect(screen.getByTestId("ok-child").textContent).toBe("Healthy");
  });

  it("catches rendering errors and displays the fallback banner", () => {
    // Suppress console.error during expected react error boundary triggers
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ProblemComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Triggered runtime crash")).toBeInTheDocument();
    expect(screen.getByText("Reload Application")).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it("reloads the browser page when reload button is clicked", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    
    // Mock window.location.reload
    const reloadMock = vi.fn();
    Object.defineProperty(window, "location", {
      value: { reload: reloadMock },
      writable: true
    });

    render(
      <ErrorBoundary>
        <ProblemComponent />
      </ErrorBoundary>
    );

    const reloadBtn = screen.getByText("Reload Application");
    await act(async () => {
      reloadBtn.click();
    });

    expect(reloadMock).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
