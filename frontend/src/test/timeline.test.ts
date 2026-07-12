import { describe, it, expect } from "vitest";
import { buildTimelineSeries } from "../transformers/timeline";

describe("buildTimelineSeries transformer", () => {
  it("returns empty array for empty records", () => {
    expect(buildTimelineSeries(null)).toEqual([]);
    expect(buildTimelineSeries([])).toEqual([]);
  });

  it("safely ignores records missing timestamps or containing invalid formats", () => {
    const records = [
      { text: "garbage" },
      { timestamp: "invalid-date-format" },
      { timestamp: "2026-07-10T20:53:59Z", value: 1 },
    ];
    const result = buildTimelineSeries(records, "minute");
    expect(result).toEqual([{ time: "2026-07-10 20:53", count: 1 }]);
  });

  it("buckets logs correctly by minute, 15-minute, hour, and day", () => {
    const records = [
      { timestamp: "2026-07-10T20:03:00Z" },
      { timestamp: "2026-07-10T20:04:30Z" },
      { timestamp: "2026-07-10T20:18:00Z" },
      { timestamp: "2026-07-10T21:05:00Z" },
      { timestamp: "2026-07-11T12:00:00Z" },
    ];

    // Minutes bucketing
    expect(buildTimelineSeries(records, "minute")).toEqual([
      { time: "2026-07-10 20:03", count: 1 },
      { time: "2026-07-10 20:04", count: 1 },
      { time: "2026-07-10 20:18", count: 1 },
      { time: "2026-07-10 21:05", count: 1 },
      { time: "2026-07-11 12:00", count: 1 },
    ]);

    // 15-Minutes bucketing
    expect(buildTimelineSeries(records, "15-minute")).toEqual([
      { time: "2026-07-10 20:00", count: 2 },
      { time: "2026-07-10 20:15", count: 1 },
      { time: "2026-07-10 21:00", count: 1 },
      { time: "2026-07-11 12:00", count: 1 },
    ]);

    // Hour bucketing
    expect(buildTimelineSeries(records, "hour")).toEqual([
      { time: "2026-07-10 20:00", count: 3 },
      { time: "2026-07-10 21:00", count: 1 },
      { time: "2026-07-11 12:00", count: 1 },
    ]);

    // Day bucketing
    expect(buildTimelineSeries(records, "day")).toEqual([
      { time: "2026-07-10", count: 4 },
      { time: "2026-07-11", count: 1 },
    ]);
  });

  it("ensures chronological sorting order output is deterministic", () => {
    const records = [
      { timestamp: "2026-07-11T12:00:00Z" },
      { timestamp: "2026-07-10T20:03:00Z" },
    ];
    const result = buildTimelineSeries(records, "day");
    expect(result).toEqual([
      { time: "2026-07-10", count: 1 },
      { time: "2026-07-11", count: 1 },
    ]);
  });
});
