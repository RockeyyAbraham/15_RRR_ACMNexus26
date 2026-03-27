import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/ingest", label: "Ingest", code: "IN" },
  { to: "/detection", label: "Detection", code: "DT" },
  { to: "/evidence", label: "Evidence", code: "EV" },
  { to: "/legal", label: "Legal", code: "LG" },
];

export default function Sidebar() {
  return (
    <aside className="relative flex h-full w-full flex-col overflow-hidden border-r border-neon/15 bg-[linear-gradient(180deg,rgba(6,10,19,0.98),rgba(8,12,20,0.9))] px-4 py-6 backdrop-blur-xl">
      <div className="absolute inset-0 scanline-overlay opacity-30" />
      <div className="absolute inset-y-0 right-0 w-px bg-gradient-to-b from-transparent via-neon/50 to-transparent" />
      <div className="relative z-10 flex items-center gap-3 px-2">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-neon/40 bg-[radial-gradient(circle_at_30%_30%,rgba(212,255,0,0.22),rgba(0,234,255,0.08),transparent_72%)] font-display text-sm tracking-[0.24em] text-neon shadow-neon">
          ST
        </div>
        <div>
          <div className="font-display text-lg uppercase tracking-[0.18em] text-neon">Sentinel</div>
          <div className="text-xs uppercase tracking-[0.28em] text-muted">Threat Command Grid</div>
        </div>
      </div>

      <div className="relative z-10 mt-6 rounded-2xl border border-cyan/10 bg-cyan/5 px-4 py-3">
        <div className="font-display text-[10px] uppercase tracking-[0.34em] text-cyan">Core System</div>
        <div className="mt-2 text-sm uppercase tracking-[0.18em] text-slate-200">Realtime Enforcement Interface</div>
      </div>

      <div className="relative z-10 mt-8 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              [
                "group flex items-center gap-3 rounded-2xl border px-3 py-3 transition duration-200",
                isActive
                  ? "border-neon/70 bg-neon/10 shadow-neon"
                  : "border-white/10 bg-white/[0.02] hover:scale-[1.02] hover:border-neon/40 hover:bg-neon/5 hover:shadow-neon",
              ].join(" ")
            }
          >
            {({ isActive }) => (
              <>
                <div
                  className={[
                    "flex h-11 w-11 items-center justify-center rounded-xl border font-display text-xs tracking-[0.22em] transition duration-200",
                    isActive
                      ? "border-neon/80 bg-neon text-slate-950"
                      : "border-cyan/30 bg-cyan/5 text-cyan group-hover:border-neon/50 group-hover:text-neon",
                  ].join(" ")}
                >
                  {item.code}
                </div>
                <div>
                  <div className="font-display text-sm uppercase tracking-[0.18em] text-white">{item.label}</div>
                  <div className="text-xs uppercase tracking-[0.24em] text-muted">
                    {isActive ? "Active Module" : "Open Module"}
                  </div>
                </div>
              </>
            )}
          </NavLink>
        ))}
      </div>

      <div className="relative z-10 mt-auto rounded-2xl border border-cyan/20 bg-[linear-gradient(180deg,rgba(0,234,255,0.08),rgba(7,10,19,0.82))] p-4 shadow-cyan">
        <div className="font-display text-xs uppercase tracking-[0.28em] text-cyan">Sentinel Core</div>
        <div className="mt-3 flex items-center gap-2 text-sm uppercase tracking-[0.2em] text-white">
          <span className="h-2.5 w-2.5 rounded-full bg-neon shadow-neon" />
          Live Scanning
        </div>
        <div className="mt-3 text-xs uppercase tracking-[0.2em] text-muted">Grid ID: 8829-X</div>
      </div>
    </aside>
  );
}
