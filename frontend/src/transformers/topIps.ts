import type { StatsResponse, TopIpInfo } from "../types/api";

export const selectTopIps = (stats: StatsResponse | null): TopIpInfo[] => {
  if (!stats || !stats.top_ips) {
    return [];
  }
  return stats.top_ips;
};
