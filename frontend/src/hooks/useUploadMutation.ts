import { useMutation } from "@tanstack/react-query";
import { apiService } from "../services/apiService";
import { queryKeys } from "../services/queryKeys";

interface UploadPayload {
  file: File;
  format?: string;
  onProgress?: (percent: number) => void;
  signal?: AbortSignal;
}

export const useUploadMutation = () => {
  return useMutation({
    mutationKey: queryKeys.upload,
    mutationFn: ({ file, format, onProgress, signal }: UploadPayload) => {
      return apiService.uploadFile(file, format, signal, onProgress);
    },
  });
};
