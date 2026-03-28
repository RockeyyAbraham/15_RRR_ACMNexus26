import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import ChartPanel from "../components/ChartPanel";
import StatCard from "../components/StatCard";
import UploadBox from "../components/UploadBox";
import { fetchDetections, fetchHealth, fetchMetricsSummary, generateFingerprint, runPiracyBenchmark } from "../services/api";
import type { HealthApi, MetricsSummaryApi, PiracyBenchmarkResponse } from "../types";

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [leagueName, setLeagueName] = useState("EURO_PREMIER_CHAMPIONSHIP");
  const [matchId, setMatchId] = useState("UUID_88392_B");
  const [broadcastDate, setBroadcastDate] = useState(new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<PiracyBenchmarkResponse | null>(null);
  const [progress, setProgress] = useState({ video: 91, audio: 64 });
  const [summary, setSummary] = useState<MetricsSummaryApi | null>(null);
  const [health, setHealth] = useState<HealthApi | null>(null);
  const [recentConfidence, setRecentConfidence] = useState<Array<{ label: string; value: number }>>([]);
  const sortedBenchmarkVariants = useMemo(
    () =>
      benchmarkResult
        ? benchmarkResult.variants.slice().sort((a, b) => b.combined_confidence - a.combined_confidence)
        : [],
    [benchmarkResult],
  );

  useEffect(() => {
    let mounted = true;

    fetchMetricsSummary().then((data) => {
      if (mounted) {
        setSummary(data);
      }
    });

    fetchHealth().then((data) => {
      if (mounted) {
        setHealth(data);
      }
    });

    fetchDetections().then((items) => {
      if (mounted) {
        const trend = items
          .slice(0, 7)
          .reverse()
          .map((item, index) => ({
            label: String(index + 1).padStart(2, "0"),
            value: Math.round(item.confidence_score),
          }));
        setRecentConfidence(trend);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  const fingerprintDetails = useMemo(
    () => [
      {
        label: "Engine Matrix",
        value: `${health?.engines?.length ?? 0} ONLINE`,
        hint: health?.engines?.join(", ") ?? "No engine telemetry available",
        accent: "neon" as const,
      },
      {
        label: "Queue Pressure",
        value: `${summary?.async.active_jobs ?? 0}/${summary?.async.max_queue_size ?? 0}`,
        hint: `Workers: ${summary?.async.max_workers ?? 0}`,
        accent: "cyan" as const,
      },
      {
        label: "Review Threshold",
        value: `${summary?.thresholds.manual_review ?? 0}%`,
        hint: `Auto action: ${summary?.thresholds.auto_action ?? 0}%`,
        accent: "default" as const,
      },
    ],
    [health, summary],
  );

  const handleSubmit = async () => {
    if (!file) {
      setError("Upload a source video before generating a fingerprint.");
      setMessage(null);
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);
    setProgress({ video: 28, audio: 12 });

    let interval: number | undefined;

    try {
      interval = window.setInterval(() => {
        setProgress((current) => ({
          video: Math.min(current.video + 11, 94),
          audio: Math.min(current.audio + 9, 88),
        }));
      }, 220);

      const response = await generateFingerprint({
        title: matchId,
        league: leagueName,
        broadcastDate,
        file,
      });

      setProgress({ video: 100, audio: 100 });
      setMessage(
        `${response.message}. Content ID ${response.content_id} indexed with ${response.video_hash_count} protected hashes.`,
      );
      const refreshedSummary = await fetchMetricsSummary();
      setSummary(refreshedSummary);
      setBenchmarkResult(null);
    } catch {
      setError("Fingerprint generation failed. Verify the Flask backend is online.");
      setProgress({ video: 0, audio: 0 });
    } finally {
      if (interval) {
        window.clearInterval(interval);
      }
      setLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    if (!file) {
      setError("Upload a source video before running the piracy benchmark.");
      setMessage(null);
      return;
    }

    setBenchmarkLoading(true);
    setError(null);
    setMessage(null);

    try {
      const result = await runPiracyBenchmark({
        title: matchId,
        league: leagueName,
        broadcastDate,
        file,
      });

      setBenchmarkResult(result);
      const weakVariant = result.variants
        .slice()
        .sort((a, b) => a.combined_confidence - b.combined_confidence)[0];

      setMessage(
        `Benchmark complete: ${result.detected_count}/${result.variant_count} variants detected (${result.detection_rate.toFixed(2)}%). Weakest case: ${weakVariant?.description ?? "N/A"}.`,
      );

      const refreshedSummary = await fetchMetricsSummary();
      setSummary(refreshedSummary);
    } catch (benchmarkError) {
      setError(
        benchmarkError instanceof Error
          ? benchmarkError.message
          : "Benchmark failed. Verify backend and try again.",
      );
    } finally {
      setBenchmarkLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="section-shell">
        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="panel-title mb-2">Ingestion Command</div>
            <h1 className="panel-heading">Ingest Portal</h1>
            <div className="mt-4 max-w-2xl text-[13px] font-medium leading-relaxed tracking-wide text-slate-400">
              Register protected media, generate hash signatures, and push a new asset into the Sentinel monitoring mesh via forensic ingestion.
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <span className="data-chip">Video Lock</span>
            <span className="data-chip">Hash Mesh</span>
            <span className="data-chip">Live Index</span>
          </div>
        </div>
      </div>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,3fr)_360px]">
        <div className="space-y-8">
          <div className="hud-panel p-8 md:p-10">
            <div className="grid gap-10 xl:grid-cols-[minmax(0,1.6fr)_minmax(340px,1fr)]">
              <div>
                <div className="panel-title mb-6">Reference Video Source</div>
                <UploadBox file={file} onFileSelect={setFile} />
              </div>

              <div className="space-y-6">
                <label className="block">
                  <span className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">League Name</span>
                  <input
                    className="field-shell w-full"
                    placeholder="e.g. EURO_PREMIER_CHAMPIONSHIP"
                    value={leagueName}
                    onChange={(event) => setLeagueName(event.target.value)}
                  />
                </label>

                <label className="block">
                  <span className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">Match ID</span>
                  <input
                    className="field-shell w-full"
                    placeholder="e.g. UUID_88392_B"
                    value={matchId}
                    onChange={(event) => setMatchId(event.target.value)}
                  />
                </label>

                <label className="block">
                  <span className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">Broadcast Date</span>
                  <input
                    type="date"
                    className="field-shell w-full"
                    value={broadcastDate}
                    onChange={(event) => setBroadcastDate(event.target.value)}
                  />
                </label>

                <motion.button
                  type="button"
                  className="cyber-button w-full mt-2"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleSubmit}
                  disabled={loading || benchmarkLoading}
                >
                  {loading ? (
                    <span className="flex items-center gap-3">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
                      Processing...
                    </span>
                  ) : "Generate Fingerprint"}
                </motion.button>

                <button
                  type="button"
                  className="subtle-button w-full"
                  onClick={handleRunBenchmark}
                  disabled={loading || benchmarkLoading}
                >
                  {benchmarkLoading ? "Running 17-Variant Benchmark..." : "Run 17-Variant Piracy Benchmark"}
                </button>

                {message ? (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-2xl border border-neon/20 bg-neon/10 px-5 py-4 text-xs font-bold uppercase tracking-widest text-neon leading-relaxed"
                  >
                    {message}
                  </motion.div>
                ) : null}
                {error ? (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-5 py-4 text-xs font-bold uppercase tracking-widest text-rose-300 leading-relaxed"
                  >
                    {error}
                  </motion.div>
                ) : null}
              </div>
            </div>

            <div className="mt-10 grid gap-8 md:grid-cols-2">
              <div className="rounded-3xl border border-white/5 bg-white/[0.02] p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="font-display text-[10px] font-bold uppercase tracking-[0.2em] text-muted/60">Video pHash Matrix</div>
                  <div className="text-[10px] font-bold text-neon">{progress.video}%</div>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-900/50">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-neon/40 via-neon to-neon shadow-[0_0_15px_rgba(212,255,0,0.3)]"
                    animate={{ width: `${progress.video}%` }}
                    transition={{ type: "spring", bounce: 0, duration: 0.8 }}
                  />
                </div>
              </div>
              <div className="rounded-3xl border border-white/5 bg-white/[0.02] p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="font-display text-[10px] font-bold uppercase tracking-[0.2em] text-muted/60">Audio Spectrogram</div>
                  <div className="text-[10px] font-bold text-cyan">{progress.audio}%</div>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-900/50">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-cyan/40 via-cyan to-cyan shadow-[0_0_15px_rgba(0,234,255,0.3)]"
                    animate={{ width: `${progress.audio}%` }}
                    transition={{ type: "spring", bounce: 0, duration: 0.8 }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {fingerprintDetails.map((card) => (
              <StatCard key={card.label} {...card} />
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="panel-title px-1">Global Intelligence</div>
          <StatCard
            label="Total Protected Hashes"
            value={String(summary?.protected_content_count ?? 0)}
            hint={`Detections: ${summary?.detections_count ?? 0}`}
            accent="neon"
          />
          <StatCard
            label="System Sync Status"
            value={(health?.status ?? "offline").toUpperCase()}
            hint={`Engines online: ${health?.engines?.length ?? 0}`}
            accent="default"
          />
          <ChartPanel
            title="Threat Confidence History"
            data={recentConfidence.length > 0 ? recentConfidence : [{ label: "00", value: 0 }]}
          />
          <div className="glass-card p-6">
            <div className="font-display text-[9px] font-bold uppercase tracking-[0.3em] text-muted/60 mb-4">Worker Telemetry</div>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-widest text-slate-300">
                <span>Active Jobs</span>
                <span className="text-neon">{summary?.async.active_jobs ?? 0}</span>
              </div>
              <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-widest text-slate-300">
                <span>Queue Load</span>
                <span className="text-cyan">{summary?.async.tracked_jobs ?? 0}/{summary?.async.max_queue_size ?? 0}</span>
              </div>
            </div>
          </div>
          {benchmarkResult ? (
            <div className="glass-card p-6">
              <div className="font-display text-[9px] font-bold uppercase tracking-[0.3em] text-muted/60 mb-4">
                Piracy Benchmark Analytics
              </div>
              <div className="space-y-3 text-[11px] font-bold uppercase tracking-widest text-slate-300">
                <div className="flex items-center justify-between">
                  <span>Detected Variants</span>
                  <span className="text-neon">
                    {benchmarkResult.detected_count}/{benchmarkResult.variant_count}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Detection Rate</span>
                  <span className="text-cyan">{benchmarkResult.detection_rate.toFixed(2)}%</span>
                </div>
                <div className="text-[10px] text-slate-400 normal-case tracking-normal pt-2">
                  Results saved at: {benchmarkResult.output_dir}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {benchmarkResult ? (
        <div className="glass-card overflow-hidden">
          <div className="border-b border-white/5 bg-white/[0.02] px-6 py-5 md:px-8">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="font-display text-[9px] font-bold uppercase tracking-[0.3em] text-muted/60">
                  Variant Forensics
                </div>
                <div className="mt-2 font-display text-lg font-extrabold tracking-tight text-white">
                  17-Variant Detection Breakdown
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="data-chip">Detected {benchmarkResult.detected_count}/{benchmarkResult.variant_count}</span>
                <span className="data-chip">Rate {benchmarkResult.detection_rate.toFixed(2)}%</span>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-slate-950/40 text-left">
                  <th className="px-6 py-4 font-display text-[9px] font-bold uppercase tracking-[0.28em] text-muted/60">Variant</th>
                  <th className="px-6 py-4 font-display text-[9px] font-bold uppercase tracking-[0.28em] text-muted/60">Issue</th>
                  <th className="px-6 py-4 font-display text-[9px] font-bold uppercase tracking-[0.28em] text-muted/60">Video</th>
                  <th className="px-6 py-4 font-display text-[9px] font-bold uppercase tracking-[0.28em] text-muted/60">Audio</th>
                  <th className="px-6 py-4 font-display text-[9px] font-bold uppercase tracking-[0.28em] text-muted/60">Combined</th>
                  <th className="px-6 py-4 font-display text-[9px] font-bold uppercase tracking-[0.28em] text-muted/60">Threshold</th>
                  <th className="px-6 py-4 font-display text-[9px] font-bold uppercase tracking-[0.28em] text-muted/60">Decision</th>
                  <th className="px-6 py-4 font-display text-[9px] font-bold uppercase tracking-[0.28em] text-muted/60">Status</th>
                </tr>
              </thead>
              <tbody>
                {sortedBenchmarkVariants.map((variant) => (
                  <tr key={variant.filename} className="border-b border-white/5 text-[12px] text-slate-300 transition-colors hover:bg-white/[0.02]">
                    <td className="px-6 py-4">
                      <div className="font-display text-[10px] font-bold uppercase tracking-[0.14em] text-white">
                        {variant.description}
                      </div>
                      <div className="mt-1 font-mono text-[10px] text-slate-500">{variant.filename}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-slate-300">
                        {variant.issue_type.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-[11px] text-slate-200">{variant.video_confidence.toFixed(2)}%</td>
                    <td className="px-6 py-4 font-mono text-[11px] text-slate-200">{variant.audio_confidence.toFixed(2)}%</td>
                    <td className="px-6 py-4 font-mono text-[11px] font-bold text-neon">{variant.combined_confidence.toFixed(2)}%</td>
                    <td className="px-6 py-4 font-mono text-[11px] text-cyan">{variant.adaptive_threshold.toFixed(2)}%</td>
                    <td className="px-6 py-4 text-[11px] text-slate-400">{variant.decision_reason}</td>
                    <td className="px-6 py-4">
                      <span
                        className={[
                          "inline-flex items-center rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-widest",
                          variant.is_detected
                            ? "border-neon/30 bg-neon/10 text-neon"
                            : "border-rose-500/30 bg-rose-500/10 text-rose-300",
                        ].join(" ")}
                      >
                        {variant.is_detected ? "Detected" : "Missed"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
