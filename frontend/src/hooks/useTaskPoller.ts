import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiService } from "../services/apiService";
import { type TaskResponse } from "../types/api";

export function useTaskPoller(
  taskId: string | null,
  onComplete?: (data: TaskResponse) => void,
  onFailure?: (error: string) => void
) {
  const query = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => apiService.getTaskStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data as TaskResponse | undefined;
      if (data && (data.status === "completed" || data.status === "failed")) {
        return false; // Stop polling when finished
      }
      return 1000; // Poll every 1 second
    },
  });

  const { data } = query;

  useEffect(() => {
    if (!data) return;

    if (data.status === "completed" && onComplete) {
      onComplete(data);
    } else if (data.status === "failed" && onFailure) {
      onFailure(data.error || "Background task processing failed");
    }
  }, [data, onComplete, onFailure]);

  return query;
}
