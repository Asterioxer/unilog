import { describe, it, expect } from "vitest";
import { selectStatusCodeDistribution } from "../transformers/statusCodes";
import type { StatsResponse } from "../types/api";

describe("selectStatusCodeDistribution transformer", () => {
  it("returns empty array when stats is null or status_codes is missing", () => {
    expect(selectStatusCodeDistribution(null)).toEqual([]);
    expect(
      selectStatusCodeDistribution({
        format: "nginx",
        total_lines: 10,
        error_rate: 0,
        http_5xx_rate: null,
        time_range: null,
        top_ips: [],
        log_levels: {},
        top_endpoints: [],
        bytes_transferred: 0,
      })
    ).toEqual([]);
  });

  it("successfully transforms status codes dict to name value objects", () => {
    const stats: StatsResponse = {
      format: "nginx",
      total_lines: 10,
      error_rate: 0.1,
      http_5xx_rate: 0,
      time_range: null,
      top_ips: [],
      log_levels: {},
      top_endpoints: [],
      bytes_transferred: 0,
      status_codes: {
        "200": 8,
        "404": 2,
      },
    };

    const result = selectStatusCodeDistribution(stats);
    expect(result).toEqual([
      { name: "200", value: 8 },
      { name: "404", value: 2 },
    ]);
  });
});
