export const queryKeys = {
  formats: ["formats"] as const,
  stats: ["stats"] as const,
  detect: ["detect"] as const,
  upload: ["upload"] as const,
  task: (id: string) => ["task", id] as const,
  records: ["records"] as const,
};
