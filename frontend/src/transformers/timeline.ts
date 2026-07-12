export type TimeBucket = "minute" | "5-minute" | "15-minute" | "hour" | "day";

export interface TimelineDataPoint {
  time: string;
  count: number;
}

export const buildTimelineSeries = (
  records: Record<string, unknown>[] | null,
  bucket: TimeBucket = "hour"
): TimelineDataPoint[] => {
  if (!records || records.length === 0) {
    return [];
  }

  const groups: Record<string, number> = {};

  records.forEach((rec) => {
    const rawTs = rec.timestamp || rec.time || rec.datetime;
    if (!rawTs) {
      return;
    }

    // Try parsing the timestamp
    const date = new Date(String(rawTs));
    if (isNaN(date.getTime())) {
      return;
    }

    const key = getBucketKey(date, bucket);
    groups[key] = (groups[key] || 0) + 1;
  });

  return Object.entries(groups)
    .map(([time, count]) => ({ time, count }))
    .sort((a, b) => a.time.localeCompare(b.time));
};

function getBucketKey(date: Date, bucket: TimeBucket): string {
  const y = date.getUTCFullYear();
  const m = String(date.getUTCMonth() + 1).padStart(2, "0");
  const d = String(date.getUTCDate()).padStart(2, "0");
  const h = String(date.getUTCHours()).padStart(2, "0");
  const min = date.getUTCMinutes();

  if (bucket === "day") {
    return `${y}-${m}-${d}`;
  }
  if (bucket === "hour") {
    return `${y}-${m}-${d} ${h}:00`;
  }

  let roundedMin = min;
  if (bucket === "5-minute") {
    roundedMin = Math.floor(min / 5) * 5;
  } else if (bucket === "15-minute") {
    roundedMin = Math.floor(min / 15) * 15;
  } else if (bucket === "minute") {
    roundedMin = min;
  }

  const minStr = String(roundedMin).padStart(2, "0");
  return `${y}-${m}-${d} ${h}:${minStr}`;
}
