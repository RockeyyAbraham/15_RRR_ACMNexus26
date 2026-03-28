export default function Topbar() {
  return (
    <header className="glass-card relative overflow-hidden px-8 py-6">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan/30 to-transparent" />
      <div className="relative z-10 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="panel-title mb-1">Command Layer</div>
          <div className="font-display text-lg font-bold uppercase tracking-[0.1em] text-white">
            Sentinel Network
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 rounded-full border border-neon/20 bg-neon/5 px-4 py-2 font-display text-[10px] uppercase tracking-[0.2em] text-neon">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-neon shadow-[0_0_8px_rgba(212,255,0,1)]" />
            Live Scanning
          </div>
          <div className="rounded-full border border-cyan/20 bg-cyan/5 px-4 py-2 font-display text-[10px] uppercase tracking-[0.2em] text-cyan">
            Grid ID: 8829-X
          </div>
        </div>
      </div>
    </header>
  );
}
