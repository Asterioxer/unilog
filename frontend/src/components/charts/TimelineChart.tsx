import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts";

interface TimelineChartProps {
  data: { time: string; count: number }[];
}

export default function TimelineChart({ data }: TimelineChartProps) {
  return (
    <div className="w-full h-full" role="img" aria-label="Requests Over Time Area Chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 10 }}
        >
          <defs>
            <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="time"
            tick={{ fill: "var(--color-muted-foreground)", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "var(--color-muted-foreground)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--color-popover)",
              borderColor: "var(--color-border)",
              borderRadius: "8px",
            }}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="var(--color-primary)"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorRequests)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
