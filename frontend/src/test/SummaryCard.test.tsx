import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import SummaryCard from "../components/SummaryCard";

describe("SummaryCard Component", () => {
  it("renders metric title, value, subtitle and custom icon slot", () => {
    render(
      <SummaryCard
        title="Error rate"
        value="5.62%"
        subtitle="Ratio of bad responses"
        icon={<span data-testid="test-icon">💡</span>}
      />
    );

    expect(screen.getByText("Error rate")).toBeInTheDocument();
    expect(screen.getByText("5.62%")).toBeInTheDocument();
    expect(screen.getByText("Ratio of bad responses")).toBeInTheDocument();
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("renders a shimmer skeleton during active load states", () => {
    render(<SummaryCard title="Total lines" isLoading={true} />);
    
    expect(screen.getByText("Total lines")).toBeInTheDocument();
    const skeletons = screen.getAllByTestId("skeleton-element");
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("5.62%")).toBeNull();
  });

  it("renders fallback error text when processing fails", () => {
    render(<SummaryCard title="Format" error="Could not read logs" />);

    expect(screen.getByText("Format")).toBeInTheDocument();
    expect(screen.getByText("Could not read logs")).toBeInTheDocument();
  });
});
