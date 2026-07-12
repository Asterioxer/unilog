export const buildRecordId = (
  record: Record<string, unknown>,
  index: number
): string => {
  const ts = String(record.timestamp || record.time || record.datetime || "");
  const ip = String(record.client_ip || record.source_ip || record.ip || "");
  const lineNo = String(record.line_number || record.index || index);

  // Generate a fast hash of the raw string if present to tie break
  const rawText = String(record.raw || "");
  let hash = 0;
  for (let i = 0; i < rawText.length; i++) {
    hash = (hash << 5) - hash + rawText.charCodeAt(i);
    hash |= 0; // Convert to 32bit integer
  }

  return `${ts}_${ip}_${lineNo}_${Math.abs(hash)}`;
};
