import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type ChartPanelProps = {
  title: string;
  data: Array<{ label: string; value: number }>;
};

export default function ChartPanel({ title, data }: ChartPanelProps) {
  return (
    <div className="glass-card p-4">
      <div className="font-display text-xs uppercase tracking-[0.28em] text-neon">{title}</div>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(212,255,0,0.1)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: "#98a5ba", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fill: "#98a5ba", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip
              cursor={{ fill: "rgba(212,255,0,0.06)" }}
              contentStyle={{
                background: "rgba(11,17,31,0.96)",
                border: "1px solid rgba(212,255,0,0.24)",
                borderRadius: "16px",
                color: "#e8edf4",
              }}
            />
            <Bar dataKey="value" fill="#d4ff00" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
