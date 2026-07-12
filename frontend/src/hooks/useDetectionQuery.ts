import { useMutation } from "@tanstack/react-query";
import { apiService } from "../services/apiService";
import { queryKeys } from "../services/queryKeys";

interface DetectionPayload {
  logText: string;
}

export const useDetectionQuery = () => {
  return useMutation({
    mutationKey: queryKeys.detect,
    mutationFn: async ({ logText }: DetectionPayload) => {
      return apiService.detectFormat(logText);
    },
  });
};
