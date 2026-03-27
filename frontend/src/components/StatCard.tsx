type StatCardProps = {
  label: string;
  value: string;
  hint?: string;
  accent?: "neon" | "cyan" | "danger" | "default";
};

export default function StatCard({ label, value, hint, accent = "default" }: StatCardProps) {
  const accentStyles = {
    default: "text-white",
    neon: "text-neon [text-shadow:0_0_18px_rgba(212,255,0,0.65)]",
    cyan: "text-cyan [text-shadow:0_0_18px_rgba(0,234,255,0.4)]",
    danger: "text-rose-300 [text-shadow:0_0_18px_rgba(251,113,133,0.35)]",
  };

  return (
    <div className="glass-card h-full p-5">
      <div className="font-display text-[11px] uppercase tracking-[0.28em] text-muted">{label}</div>
      <div className={`mt-3 font-display text-4xl tracking-[0.04em] ${accentStyles[accent]}`}>{value}</div>
      {hint ? <div className="mt-2 text-sm text-slate-300/80">{hint}</div> : null}
    </div>
  );
}
