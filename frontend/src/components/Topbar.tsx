export default function Topbar() {
  return (
    <header className="glass-card relative overflow-hidden px-5 py-4">
      <div className="absolute inset-0 bg-grid bg-[size:24px_24px] opacity-[0.04]" />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan/60 to-transparent" />
      <div className="relative z-10 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-display text-xs uppercase tracking-[0.32em] text-neon">Sentinel Command Layer</div>
          <div className="mt-2 text-sm uppercase tracking-[0.22em] text-muted">
            Real-time media fingerprinting and enforcement
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-full border border-neon/40 bg-neon/10 px-4 py-2 font-display text-xs uppercase tracking-[0.22em] text-neon shadow-neon">
            Live Scanning
          </div>
          <div className="rounded-full border border-cyan/30 bg-cyan/10 px-4 py-2 font-display text-xs uppercase tracking-[0.22em] text-cyan shadow-cyan">
            Sentinel 8829-X
          </div>
        </div>
      </div>
    </header>
  );
}
