import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import LiveMonitor from "../components/LiveMonitor";

// Mock WebSocket globally
class MockWebSocket {
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  readyState: number = 0;

  static mockInstances: MockWebSocket[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.mockInstances.push(this);
    setTimeout(() => {
      this.readyState = 1; // OPEN
      if (this.onopen) this.onopen();
    }, 10);
  }

  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose();
  });
}

describe("LiveMonitor Component", () => {
  let originalWebSocket: unknown;

  beforeEach(() => {
    originalWebSocket = (window as unknown as Record<string, unknown>).WebSocket;
    (window as unknown as Record<string, unknown>).WebSocket = MockWebSocket;
    MockWebSocket.mockInstances = [];
  });

  afterEach(() => {
    (window as unknown as Record<string, unknown>).WebSocket = originalWebSocket;
  });


  it("renders connection status, stats cards, and action controls", async () => {
    render(<LiveMonitor />);
    
    // Wait for mock constructor timeout (onopen)
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 20));
    });

    expect(screen.getByText("Live Log Monitoring Mode")).toBeInTheDocument();
    expect(screen.getByText("CONNECTED")).toBeInTheDocument();
    expect(screen.getByText("Stream Count")).toBeInTheDocument();
    expect(screen.getByText("Error Rate")).toBeInTheDocument();
  });

  it("adds records to terminal scroll buffer when receiving WebSocket messages", async () => {
    render(<LiveMonitor />);
    
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 20));
    });

    const instance = MockWebSocket.mockInstances[0];

    await act(async () => {
      instance.readyState = 1;
      if (instance.onopen) instance.onopen();
    });

    const testRecord = {
      timestamp: "2026-07-19T11:00:00Z",
      level: "ERROR",
      source_ip: "185.220.101.47",
      method: "GET",
      path: "/wp-admin",
      status_code: 500,
      size: 150,
      user_agent: "Mozilla",
      raw: '185.220.101.47 - - [19/Jul/2026:11:00:00 +0000] "GET /wp-admin" 500 150',
    };

    await act(async () => {
      if (instance.onmessage) {
        instance.onmessage({ data: JSON.stringify(testRecord) });
      }
    });

    // Check count and record display
    expect(screen.getByText("185.220.101.47")).toBeInTheDocument();
    expect(screen.getByText("ERROR")).toBeInTheDocument();
    expect(screen.getByText(/GET \/wp-admin/)).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument(); // Stream count
  });

  it("pauses and resumes stream when clicking the pause button", async () => {
    render(<LiveMonitor />);
    
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 30));
    });

    const instance = MockWebSocket.mockInstances.at(-1);
    if (instance && instance.onopen) {
      await act(async () => {
        instance.readyState = 1;
        instance.onopen!();
      });
    }

    const pauseBtn = screen.getByTitle("Pause Stream");
    expect(pauseBtn).not.toBeDisabled();

    await act(async () => {
      fireEvent.click(pauseBtn);
    });

    expect(screen.getByTitle("Resume Stream")).toBeInTheDocument();
  });















});
