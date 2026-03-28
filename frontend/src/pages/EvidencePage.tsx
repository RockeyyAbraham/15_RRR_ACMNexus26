import { useCallback, useEffect, useMemo } from "react";
import { fetchDetections, fetchMetricsSummary, getDmcaDownloadUrl } from "../services/api";
import StatCard from "../components/StatCard";
import type { DetectionApiItem, MetricsSummaryApi } from "../types";
import usePersistedState from "../hooks/usePersistedState";
import { extractPlatform } from "../utils/platform";
import { POLLING_INTERVALS } from "../constants/thresholds";

export default function EvidencePage() {
  const [summary, setSummary] = usePersistedState<MetricsSummaryApi | null>("sentinel.evidence.summary", null);
  const [detections, setDetections] = usePersistedState<DetectionApiItem[]>("sentinel.evidence.detections", []);

  useEffect(() => {
    let mounted = true;
    let pollInterval: number | null = null;

    const loadData = async () => {
      if (!mounted) return;

      const [summaryData, items] = await Promise.all([
        fetchMetricsSummary().catch(() => null),
        fetchDetections().catch(() => []),
      ]);

      if (!mounted) return;

      setSummary(summaryData);
      setDetections(items);
    };

    loadData();

    pollInterval = window.setInterval(() => {
      if (mounted) {
        loadData();
      }
    }, POLLING_INTERVALS.METRICS);

    return () => {
      mounted = false;
      if (pollInterval !== null) {
        window.clearInterval(pollInterval);
      }
    };
  }, []);

  const topDetection = detections[0] ?? null;

  const handleApproveForDmca = useCallback(() => {
    if (!topDetection) {
      return;
    }
    window.open(getDmcaDownloadUrl(topDetection.id), "_blank", "noopener,noreferrer");
  }, [topDetection]);

  const evidenceCards = useMemo(
    () => [
      {
        title: "Latest Case Reference",
        value: topDetection ? `DET-${String(topDetection.id).padStart(4, "0")}` : "NO CASE",
        meta: `STREAM: ${topDetection?.stream_url ?? "N/A"}`,
      },
      {
        title: "Detection Correlation",
        value: `${(topDetection?.confidence_score ?? 0).toFixed(1)}%`,
        meta: `PLATFORM: ${topDetection ? extractPlatform(topDetection.stream_url) : "UNKNOWN"}`,
      },
      {
        title: "Evidence Packet Queue",
        value: String(summary?.manual_review_count ?? 0),
        meta: "Cases pending legal/manual escalation",
      },
    ],
    [summary, topDetection],
  );

  return (
    <div className="space-y-8">
      <div className="section-shell">
        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="panel-title mb-2">Forensic Intelligence</div>
            <h1 className="panel-heading">Evidence Vault</h1>
            <div className="mt-4 max-w-2xl text-[13px] font-medium leading-relaxed tracking-wide text-slate-400">
              Inspect captured evidence packets, cross-match target metadata, and stage escalation-ready proof bundles for platform removal.
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <span className="data-chip">Forensic Cache</span>
            <span className="data-chip">Frame Match</span>
            <span className="data-chip">Escalation Ready</span>
          </div>
        </div>
      </div>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,2.2fr)_minmax(340px,1fr)]">
        <div className="hud-panel p-10">
          <div className="panel-title mb-8">Forensic Analysis Matrix</div>
          <div className="flex h-[380px] flex-col items-center justify-center rounded-3xl border border-white/5 bg-slate-950/40 font-display text-sm uppercase tracking-[0.2em] text-muted/40 shadow-inner">
            <div className="mb-4 h-16 w-16 animate-pulse rounded-full border border-neon/20 bg-neon/5" />
            {topDetection
              ? `Detection ${topDetection.id} | ${(topDetection.confidence_score ?? 0).toFixed(1)}% confidence`
              : "No detections captured yet"}
          </div>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {evidenceCards.map((card) => (
              <div key={card.title} className="glass-card p-6 border-white/5 bg-white/[0.02]">
                <div className="font-display text-[9px] font-bold uppercase tracking-[0.3em] text-muted/60">{card.title}</div>
                <div className="mt-4 font-display text-2xl font-extrabold tracking-tight text-neon">{card.value}</div>
                <div className="mt-2 text-[11px] font-medium tracking-wide text-slate-400">{card.meta}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <StatCard
            label="Match Probability"
            value={`${(topDetection?.confidence_score ?? 0).toFixed(1)}%`}
            hint={topDetection ? `Detection ID: ${topDetection.id}` : "No active detection"}
            accent="neon"
          />
          <div className="glass-card space-y-6 p-8">
            <div>
              <label htmlFor="source-ip" className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">
                Source Stream
              </label>
              <input id="source-ip" className="field-shell w-full" value={topDetection?.stream_url ?? "N/A"} readOnly />
            </div>
            <div>
              <label htmlFor="source-location" className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">
                Network Platform
              </label>
              <input
                id="source-location"
                className="field-shell w-full"
                value={topDetection ? extractPlatform(topDetection.stream_url) : "N/A"}
                readOnly
              />
            </div>
            <button
              type="button"
              className="cyber-button w-full mt-2"
              onClick={handleApproveForDmca}
              disabled={!topDetection}
              aria-label="Approve detection for DMCA notice generation"
            >
              Approve For DMCA
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
            <StatCard label="Protected Assets" value={String(summary?.protected_content_count ?? 0)} accent="neon" />
            <StatCard label="Avg Confidence" value={`${summary?.average_confidence?.toFixed(1) ?? "0.0"}%`} />
            <StatCard label="DMCA Batch Queue" value={String(summary?.manual_review_count ?? 0)} />
          </div>
        </div>
      </div>
    </div>
  );
}
