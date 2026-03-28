type StatCardProps = {
  label: string;
  value: string;
  hint?: string;
  accent?: "neon" | "cyan" | "danger" | "default";
};

export default function StatCard({ label, value, hint, accent = "default" }: StatCardProps) {
  const accentStyles = {
    default: "text-white",
    neon: "text-neon shadow-[0_0_20px_rgba(212,255,0,0.15)]",
    cyan: "text-cyan shadow-[0_0_20px_rgba(0,234,255,0.1)]",
    danger: "text-rose-400 shadow-[0_0_20px_rgba(244,63,94,0.1)]",
  };

  return (
    <div className="glass-card flex h-full flex-col justify-between p-6 transition-all duration-300 hover:border-white/20 hover:bg-white/[0.04]">
      <div>
        <div className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-muted/60">{label}</div>
        <div className={`mt-4 font-display text-4xl font-extrabold tracking-tight ${accentStyles[accent]}`}>
          {value}
        </div>
      </div>
      {hint ? (
        <div className="mt-4 border-t border-white/5 pt-4 text-[11px] font-medium leading-relaxed tracking-wide text-slate-400/80">
          {hint}
        </div>
      ) : null}
    </div>
  );
}
