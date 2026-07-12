import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { LEVEL_COLORS } from "./chartTheme";

interface LogLevelChartProps {
  data: { name: string; value: number }[];
}

export default function LogLevelChart({ data }: LogLevelChartProps) {
  return (
    <div className="w-full h-full flex flex-col justify-between">
      <div className="h-48" role="img" aria-label="Log Level Distribution Donut Chart">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={70}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry) => (
                <Cell
                  key={`cell-${entry.name}`}
                  fill={LEVEL_COLORS[entry.name] || LEVEL_COLORS.unknown}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-popover)",
                borderColor: "var(--color-border)",
                borderRadius: "8px",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-2 justify-center mt-4 border-t border-border/30 pt-3">
        {data.map((entry) => (
          <div key={entry.name} className="flex items-center gap-1.5 text-xs">
            <span
              className="h-2.5 w-2.5 rounded-xs"
              style={{
                backgroundColor: LEVEL_COLORS[entry.name] || LEVEL_COLORS.unknown,
              }}
            />
            <span className="font-medium text-muted-foreground">
              {entry.name}: {entry.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
