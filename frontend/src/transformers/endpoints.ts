import type { StatsResponse, TopEndpointInfo } from "../types/api";

export const selectTopEndpoints = (
  stats: StatsResponse | null
): TopEndpointInfo[] => {
  if (!stats || !stats.top_endpoints) {
    return [];
  }
  return stats.top_endpoints;
};
