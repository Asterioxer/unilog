import type { StatsResponse } from "../types/api";

export const selectLogLevelDistribution = (
  stats: StatsResponse | null
): { name: string; value: number }[] => {
  if (!stats || !stats.log_levels) {
    return [];
  }
  return Object.entries(stats.log_levels).map(([name, value]) => ({
    name,
    value,
  }));
};
