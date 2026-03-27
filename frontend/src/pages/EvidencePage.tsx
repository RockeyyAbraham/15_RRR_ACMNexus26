import StatCard from "../components/StatCard";

const evidenceCards = [
  {
    title: "Original Frame Reference",
    value: "FRAME PREVIEW BUFFER",
    meta: "HASH: f3e2...9a11 | RESOLUTION: 3840x2160 | PROTOCOL: HEVC_S_01",
  },
  {
    title: "Detection Correlation",
    value: "99.8%",
    meta: "TARGET_ID: 0X8829-X-DELTA | HAMMING DELTA: 04",
  },
  {
    title: "Evidence Packet Queue",
    value: "492",
    meta: "Ready for legal escalation review",
  },
];

export default function EvidencePage() {
  return (
    <div className="space-y-6">
      <div className="section-shell">
        <div className="relative z-10 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="panel-title">Forensic Intelligence</div>
            <h1 className="panel-heading mt-3">Evidence Vault</h1>
            <div className="mt-3 max-w-2xl text-sm text-slate-300">
              Inspect captured evidence packets, cross-match target metadata, and stage escalation-ready proof bundles.
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="data-chip">Forensic Cache</span>
            <span className="data-chip">Frame Match</span>
            <span className="data-chip">Escalation Ready</span>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2.2fr)_minmax(320px,1fr)]">
        <div className="hud-panel p-6">
          <div className="panel-title mb-4">Forensic Analysis</div>
          <div className="flex h-[340px] items-center justify-center rounded-2xl border border-neon/20 bg-slate-950/80 font-display text-lg uppercase tracking-[0.18em] text-muted">
            Frame Preview Buffer
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {evidenceCards.map((card) => (
              <div key={card.title} className="glass-card p-4">
                <div className="font-display text-xs uppercase tracking-[0.22em] text-muted">{card.title}</div>
                <div className="mt-3 font-display text-2xl tracking-[0.04em] text-neon">{card.value}</div>
                <div className="mt-2 text-sm text-slate-300">{card.meta}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <StatCard label="Match Probability" value="99.8%" hint="TARGET_ID: 0X8829-X-DELTA" accent="neon" />
          <div className="glass-card space-y-4 p-5">
            <div>
              <label htmlFor="source-ip" className="mb-2 block text-sm text-slate-300">
                Source IP
              </label>
              <input id="source-ip" className="field-shell w-full" value="185.158.113.44" readOnly />
            </div>
            <div>
              <label htmlFor="source-location" className="mb-2 block text-sm text-slate-300">
                Location
              </label>
              <input id="source-location" className="field-shell w-full" value="MOSCOW_REGION [RU]" readOnly />
            </div>
            <button type="button" className="cyber-button w-full">
              Approve For DMCA
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
            <StatCard label="Active Nodes" value="1,204" accent="neon" />
            <StatCard label="Latency Avg" value="14ms" />
            <StatCard label="DMCA Batch Queue" value="492" />
            <StatCard label="Network Integrity" value="OPTIMAL" accent="neon" />
          </div>
        </div>
      </div>
    </div>
  );
}
