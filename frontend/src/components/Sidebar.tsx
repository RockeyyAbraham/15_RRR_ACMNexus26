import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/ingest", label: "Ingest", code: "IN" },
  { to: "/detection", label: "Detection", code: "DT" },
  { to: "/evidence", label: "Evidence", code: "EV" },
  { to: "/legal", label: "Legal", code: "LG" },
];

export default function Sidebar() {
  return (
    <aside className="relative flex h-full w-full flex-col overflow-hidden border-r border-neon/15 bg-slate-950/85 px-4 py-6 backdrop-blur-xl">
      <div className="absolute inset-0 scanline-overlay opacity-30" />
      <div className="relative z-10 flex items-center gap-3 px-2">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-neon/40 bg-neon/10 font-display text-sm tracking-[0.24em] text-neon shadow-neon">
          SN
        </div>
        <div>
          <div className="font-display text-lg uppercase tracking-[0.18em] text-neon">Sentinel_Node</div>
          <div className="text-xs uppercase tracking-[0.28em] text-muted">Fingerprint Grid</div>
        </div>
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

      <div className="relative z-10 mt-auto rounded-2xl border border-cyan/20 bg-cyan/5 p-4 shadow-cyan">
        <div className="font-display text-xs uppercase tracking-[0.28em] text-cyan">Node Status</div>
        <div className="mt-3 flex items-center gap-2 text-sm uppercase tracking-[0.2em] text-white">
          <span className="h-2.5 w-2.5 rounded-full bg-neon shadow-neon" />
          Live Scanning
        </div>
        <div className="mt-3 text-xs uppercase tracking-[0.2em] text-muted">Node ID: 8829-X</div>
      </div>
    </aside>
  );
}
