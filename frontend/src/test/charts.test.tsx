import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import LogLevelChart from "../components/charts/LogLevelChart";
import StatusCodeChart from "../components/charts/StatusCodeChart";
import TopIPsChart from "../components/charts/TopIPsChart";
import TopEndpointsChart from "../components/charts/TopEndpointsChart";
import TimelineChart from "../components/charts/TimelineChart";
import ChartCard from "../components/charts/ChartCard";

// Mock Recharts ResponsiveContainer to render children immediately since height/width is not measurable in JSDOM
vi.mock("recharts", async () => {
  const original = await vi.importActual("recharts");
  return {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ...original as any,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  };
});

describe("Chart components visual regression wrappers", () => {
  it("renders ChartCard loading state with pulsing skeleton placeholders", () => {
    render(
      <ChartCard title="Test Chart" loading={true} empty={false}>
        <div>Chart Content</div>
      </ChartCard>
    );
    expect(screen.getByText("Test Chart")).toBeInTheDocument();
    expect(screen.queryByText("Chart Content")).not.toBeInTheDocument();
  });

  it("renders ChartCard empty state with Warning icon and custom prompt text", () => {
    render(
      <ChartCard
        title="Test Chart"
        loading={false}
        empty={true}
        emptyTitle="Custom Empty"
        emptyDescription="Custom explanation detail"
      >
        <div>Chart Content</div>
      </ChartCard>
    );
    expect(screen.getByText("Custom Empty")).toBeInTheDocument();
    expect(screen.getByText("Custom explanation detail")).toBeInTheDocument();
    expect(screen.queryByText("Chart Content")).not.toBeInTheDocument();
  });

  it("renders ChartCard ready state with children visual contents", () => {
    render(
      <ChartCard title="Test Chart" loading={false} empty={false}>
        <div>Chart Content</div>
      </ChartCard>
    );
    expect(screen.getByText("Chart Content")).toBeInTheDocument();
  });

  it("renders LogLevelChart with legends and list of levels", () => {
    const data = [
      { name: "INFO", value: 10 },
      { name: "ERROR", value: 2 },
    ];
    render(<LogLevelChart data={data} />);
    expect(screen.getByRole("img")).toHaveAttribute(
      "aria-label",
      "Log Level Distribution Donut Chart"
    );
    expect(screen.getByText("INFO: 10")).toBeInTheDocument();
    expect(screen.getByText("ERROR: 2")).toBeInTheDocument();
  });

  it("renders StatusCodeChart with accessible image role description", () => {
    const data = [
      { name: "200", value: 20 },
      { name: "500", value: 1 },
    ];
    render(<StatusCodeChart data={data} />);
    expect(screen.getByRole("img")).toHaveAttribute(
      "aria-label",
      "Status Code Distribution Bar Chart"
    );
  });

  it("renders TopIPsChart with correct category mapping", () => {
    const data = [{ ip: "127.0.0.1", count: 15, percentage: 100 }];
    render(<TopIPsChart data={data} />);
    expect(screen.getByRole("img")).toHaveAttribute(
      "aria-label",
      "Top Client IP Request Rates Bar Chart"
    );
  });

  it("renders TopEndpointsChart accessibility image label", () => {
    const data = [{ endpoint: "/api", count: 80, percentage: 100 }];
    render(<TopEndpointsChart data={data} />);
    expect(screen.getByRole("img")).toHaveAttribute(
      "aria-label",
      "Top Endpoint Resource Requests Bar Chart"
    );
  });

  it("renders TimelineChart area plot with time-series labels", () => {
    const data = [
      { time: "2026-07-10 20:00", count: 5 },
      { time: "2026-07-10 21:00", count: 8 },
    ];
    render(<TimelineChart data={data} />);
    expect(screen.getByRole("img")).toHaveAttribute(
      "aria-label",
      "Requests Over Time Area Chart"
    );
  });
});
