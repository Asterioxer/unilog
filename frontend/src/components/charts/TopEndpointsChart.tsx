import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

interface TopEndpointsChartProps {
  data: { endpoint: string; count: number; percentage: number }[];
}

export default function TopEndpointsChart({ data }: TopEndpointsChartProps) {
  return (
    <div className="w-full h-full" role="img" aria-label="Top Endpoint Resource Requests Bar Chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 10 }}
        >
          <XAxis
            dataKey="endpoint"
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
          <Bar dataKey="count" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
