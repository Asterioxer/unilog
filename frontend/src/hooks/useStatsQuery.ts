import { useMutation } from "@tanstack/react-query";
import { apiService } from "../services/apiService";
import { queryKeys } from "../services/queryKeys";

interface StatsPayload {
  logText: string;
  format?: string;
}

export const useStatsQuery = () => {
  return useMutation({
    mutationKey: queryKeys.stats,
    mutationFn: async ({ logText, format }: StatsPayload) => {
      return apiService.generateStats(logText, format === "auto" ? undefined : format);
    },
  });
};
