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
    <div className="glass-card p-6 transition-all duration-300 hover:border-white/10">
      <div className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-muted/60 mb-6">{title}</div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.03)" vertical={false} strokeDasharray="3 3" />
            <XAxis
              dataKey="label"
              tick={{ fill: "rgba(148,163,184,0.5)", fontSize: 10, fontWeight: 600 }}
              axisLine={false}
              tickLine={false}
              dy={10}
            />
            <YAxis 
              tick={{ fill: "rgba(148,163,184,0.5)", fontSize: 10, fontWeight: 600 }} 
              axisLine={false} 
              tickLine={false} 
            />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.03)", radius: 8 }}
              contentStyle={{
                background: "rgba(2,6,23,0.9)",
                backdropFilter: "blur(12px)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "12px",
                fontSize: "11px",
                fontWeight: "bold",
                color: "#f8fafc",
                boxShadow: "0 10px 15px -3px rgba(0,0,0,0.5)"
              }}
              itemStyle={{ color: "#d4ff00" }}
              labelStyle={{ marginBottom: "4px", opacity: 0.5, fontSize: "9px", textTransform: "uppercase", letterSpacing: "0.1em" }}
            />
            <Bar 
              dataKey="value" 
              fill="#d4ff00" 
              radius={[4, 4, 4, 4]} 
              barSize={24}
              className="opacity-80 hover:opacity-100 transition-opacity"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
