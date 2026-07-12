import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

interface TopIPsChartProps {
  data: { ip: string; count: number; percentage: number }[];
}

export default function TopIPsChart({ data }: TopIPsChartProps) {
  return (
    <div className="w-full h-full" role="img" aria-label="Top Client IP Request Rates Bar Chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 10, right: 10, top: 10, bottom: 10 }}
        >
          <XAxis
            type="number"
            tick={{ fill: "var(--color-muted-foreground)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            dataKey="ip"
            type="category"
            width={110}
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
          <Bar dataKey="count" fill="var(--color-primary)" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
