import type { StatsResponse } from "../types/api";

export const selectStatusCodeDistribution = (
  stats: StatsResponse | null
): { name: string; value: number }[] => {
  if (!stats || !stats.status_codes) {
    return [];
  }
  return Object.entries(stats.status_codes).map(([name, value]) => ({
    name,
    value,
  }));
};
