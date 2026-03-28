import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/ingest", label: "Ingest", code: "IN" },
  { to: "/detection", label: "Detection", code: "DT" },
  { to: "/evidence", label: "Evidence", code: "EV" },
  { to: "/legal", label: "Legal", code: "LG" },
];

export default function Sidebar() {
  return (
    <aside className="relative flex h-full w-full flex-col overflow-hidden border-r border-white/5 bg-slate-950/80 px-6 py-8 backdrop-blur-3xl">
      <div className="absolute inset-0 scanline-overlay opacity-5" />
      
      <div className="relative z-10 flex items-center gap-4 px-2">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-neon/30 bg-neon/10 font-display text-sm font-bold tracking-[0.2em] text-neon shadow-[0_0_20px_rgba(212,255,0,0.15)]">
          ST
        </div>
        <div>
          <div className="font-display text-lg font-extrabold uppercase tracking-tight text-white leading-tight">Sentinel</div>
          <div className="text-[10px] uppercase font-medium tracking-[0.4em] text-muted/80">Command Grid</div>
        </div>
      </div>

      <div className="relative z-10 mt-10 rounded-2xl border border-white/5 bg-white/[0.02] px-5 py-4">
        <div className="font-display text-[9px] font-bold uppercase tracking-[0.4em] text-cyan/70">Core Status</div>
        <div className="mt-2 text-[11px] font-medium uppercase tracking-[0.2em] text-slate-300">Realtime Enforcement</div>
      </div>

      <div className="relative z-10 mt-10 space-y-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              [
                "group flex items-center gap-4 rounded-2xl border px-3 py-3 transition-all duration-300",
                isActive
                  ? "border-neon/40 bg-neon/5 shadow-[0_0_30px_rgba(212,255,0,0.05)]"
                  : "border-transparent bg-transparent hover:bg-white/[0.03] hover:border-white/10",
              ].join(" ")
            }
          >
            {({ isActive }) => (
              <>
                <div
                  className={[
                    "flex h-10 w-10 items-center justify-center rounded-xl border font-display text-[10px] font-bold tracking-[0.1em] transition-all duration-300",
                    isActive
                      ? "border-neon/60 bg-neon text-slate-950 shadow-[0_0_15px_rgba(212,255,0,0.3)]"
                      : "border-white/10 bg-white/5 text-slate-400 group-hover:border-neon/40 group-hover:text-neon",
                  ].join(" ")}
                >
                  {item.code}
                </div>
                <div>
                  <div className={["font-display text-xs font-bold uppercase tracking-[0.15em] transition-colors", isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200"].join(" ")}>
                    {item.label}
                  </div>
                  <div className="text-[9px] uppercase font-medium tracking-[0.2em] text-muted/60 mt-0.5">
                    {isActive ? "Viewing Module" : "Open System"}
                  </div>
                </div>
              </>
            )}
          </NavLink>
        ))}
      </div>

      <div className="relative z-10 mt-auto rounded-3xl border border-white/5 bg-white/[0.02] p-5">
        <div className="font-display text-[9px] font-bold uppercase tracking-[0.4em] text-cyan/70 mb-4">System Integrity</div>
        <div className="flex items-center gap-3 text-[11px] font-bold uppercase tracking-[0.2em] text-white">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-neon shadow-[0_0_8px_rgba(212,255,0,1)]"></span>
          </span>
          Live Scanning
        </div>
        <div className="mt-4 text-[9px] font-medium uppercase tracking-[0.3em] text-muted/40">ID: SG-8829-X</div>
      </div>
    </aside>
  );
}
