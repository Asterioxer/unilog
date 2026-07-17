import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import SessionObserver from "../components/SessionObserver";
import type { SessionMetrics, JourneyMetrics } from "../types/api";

const MOCK_SESSION_METRICS: SessionMetrics = {
  average_session_duration_seconds: 120.0,
  bounce_rate: 25.0,
  pages_per_session: 3.5,
  requests_per_session: 8.2,
  active_sessions_count: 4,
  longest_session_duration_seconds: 400.0,
  possible_bot_count: 1,
  credential_stuffing_count: 0,
  endpoint_enumeration_count: 1,
  sessions: [
    {
      session_id: "session_192_168_1_1_0",
      client_ip: "192.168.1.1",
      start_time: "2026-07-17T12:00:00Z",
      end_time: "2026-07-17T12:02:00Z",
      duration_seconds: 120.0,
      request_count: 3,
      requests: [
        {
          timestamp: "2026-07-17T12:00:00Z",
          method: "GET",
          path: "/",
          status_code: 200,
          size: 100,
          journey_stage: "Landing"
        },
        {
          timestamp: "2026-07-17T12:01:00Z",
          method: "GET",
          path: "/products",
          status_code: 200,
          size: 150,
          journey_stage: "Products"
        },
        {
          timestamp: "2026-07-17T12:02:00Z",
          method: "GET",
          path: "/checkout",
          status_code: 200,
          size: 200,
          journey_stage: "Checkout"
        }
      ],
      journey: ["Landing", "Products", "Checkout"]
    }
  ]
};

const MOCK_JOURNEY_METRICS: JourneyMetrics = {
  journeys: [["Landing", "Products", "Checkout"]],
  stage_counts: {
    Landing: 1,
    Products: 1,
    Product: 0,
    Cart: 0,
    Checkout: 1,
    Other: 0
  },
  funnel: {
    Landing: 1,
    Products: 1,
    Product: 0,
    Cart: 0,
    Checkout: 1
  }
};

describe("SessionObserver Component", () => {
  it("renders loader while processing sessions", () => {
    render(<SessionObserver sessionMetrics={null} journeyMetrics={null} isProcessing={true} />);
    expect(screen.getByText("Reconstructing user session graphs...")).toBeInTheDocument();
  });

  it("renders empty state fallback if no sessions mapped", () => {
    render(<SessionObserver sessionMetrics={null} journeyMetrics={null} />);
    expect(screen.getByText("No Sessions Reconstructed")).toBeInTheDocument();
  });

  it("renders statistics grids, timelines, and anomaly alerts when sessions are loaded", () => {
    render(
      <SessionObserver 
        sessionMetrics={MOCK_SESSION_METRICS} 
        journeyMetrics={MOCK_JOURNEY_METRICS} 
      />
    );

    // Active sessions count card
    expect(screen.getByText("Active Sessions")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();

    // Session list IP item
    expect(screen.getByText("192.168.1.1")).toBeInTheDocument();

    // Security warning banner
    expect(screen.getByText("Behavioral Security Anomalies Detected")).toBeInTheDocument();
    expect(screen.getByText("Suspected Bot Traffic")).toBeInTheDocument();
    expect(screen.getByText("Suspected Endpoint Enumeration")).toBeInTheDocument();
  });
});
