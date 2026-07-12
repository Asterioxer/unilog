import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import { STATUS_COLORS, fallbackStatusColor } from "./chartTheme";

interface StatusCodeChartProps {
  data: { name: string; value: number }[];
}

export default function StatusCodeChart({ data }: StatusCodeChartProps) {
  return (
    <div className="w-full h-full" role="img" aria-label="Status Code Distribution Bar Chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 10 }}
        >
          <XAxis
            dataKey="name"
            tick={{ fill: "var(--color-muted-foreground)", fontSize: 11 }}
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
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry) => {
              const rangeKey = entry.name.charAt(0);
              const color = STATUS_COLORS[rangeKey] || fallbackStatusColor;
              return <Cell key={`cell-${entry.name}`} fill={color} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
