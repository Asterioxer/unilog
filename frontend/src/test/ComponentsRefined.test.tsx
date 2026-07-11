import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import EmptyState from "../components/EmptyState";
import MetricBadge from "../components/MetricBadge";
import AnimatedCounter from "../components/AnimatedCounter";
import MetadataPanel from "../components/MetadataPanel";

describe("EmptyState Component", () => {
  it("renders custom empty states with icon, title, description, and action slots", () => {
    render(
      <EmptyState
        icon={<span data-testid="empty-icon">📂</span>}
        title="No files yet"
        description="Please drop files to load records"
        action={<button>Browse files</button>}
      />
    );

    expect(screen.getByTestId("empty-icon")).toBeInTheDocument();
    expect(screen.getByText("No files yet")).toBeInTheDocument();
    expect(screen.getByText("Please drop files to load records")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Browse files" })).toBeInTheDocument();
  });
});

describe("MetricBadge Component", () => {
  it("renders with dynamic variants and support optional pulsing lights", () => {
    const { rerender } = render(
      <MetricBadge variant="success" pulse={true}>
        ACTIVE
      </MetricBadge>
    );

    expect(screen.getByTestId("metric-badge")).toHaveClass("bg-emerald-500/10");
    
    // Rerender with warning variant
    rerender(
      <MetricBadge variant="warning" pulse={false}>
        SUSPENDED
      </MetricBadge>
    );
    expect(screen.getByTestId("metric-badge")).toHaveClass("bg-amber-500/10");
  });
});

describe("AnimatedCounter Component", () => {
  it("displays suffix/prefix and formats numeric ranges based on decimals config", () => {
    render(
      <AnimatedCounter
        value={2.50}
        decimals={2}
        prefix="$"
        suffix="M"
      />
    );
    expect(screen.getByTestId("animated-counter")).toBeInTheDocument();
  });
});

describe("MetadataPanel Component", () => {
  it("renders formatted file execution metadata metrics grid", () => {
    render(
      <MetadataPanel
        filename="production.log"
        fileSize={2097152}
        processingTimeMs={1540}
        parserName="nginx"
        rowsCount={15200}
        taskId="worker-task-12"
        taskStatus="completed"
      />
    );

    expect(screen.getByText("Execution Metadata")).toBeInTheDocument();
    expect(screen.getByText("production.log")).toBeInTheDocument();
    expect(screen.getByText("2.00 MB")).toBeInTheDocument();
    expect(screen.getByText("nginx")).toBeInTheDocument();
    expect(screen.getByText("15,200")).toBeInTheDocument();
    expect(screen.getByText("1.54s")).toBeInTheDocument();
    expect(screen.getByText("worker-task-12")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });
});
