import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import ChartPanel from "../components/ChartPanel";
import StatCard from "../components/StatCard";
import UploadBox from "../components/UploadBox";
import { fetchDetections, fetchHealth, fetchMetricsSummary, generateFingerprint, runPiracyBenchmark } from "../services/api";
import type { HealthApi, MetricsSummaryApi, PiracyBenchmarkResponse } from "../types";

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [leagueName, setLeagueName] = useState("");
  const [matchId, setMatchId] = useState("");
  const [broadcastDate, setBroadcastDate] = useState(new Date().toISOString().slice(0, 10));
  const [contentTitle, setContentTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobStage, setJobStage] = useState<string | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<PiracyBenchmarkResponse | null>(null);
  const [progress, setProgress] = useState({ video: 91, audio: 64 });
  const [variantProgress, setVariantProgress] = useState<{
    current: number;
    total: number;
    currentVariant: string;
    currentDescription: string;
    stage: 'generating' | 'analyzing' | 'complete' | null;
    results: Array<{
      name: string;
      description: string;
      videoConfidence: number;
      audioConfidence: number;
      combinedConfidence: number;
      isDetected: boolean;
    }>;
  } | null>(null);
  const [summary, setSummary] = useState<MetricsSummaryApi | null>(null);
  const [health, setHealth] = useState<HealthApi | null>(null);
  const [recentConfidence, setRecentConfidence] = useState<Array<{ label: string; value: number }>>([]);
  // Auto-detect content info from filename
  useEffect(() => {
    if (file) {
      const filename = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
      
      // Extract title from filename if fields are empty
      if (!contentTitle) {
        setContentTitle(filename);
      }
      if (!matchId) {
        // Generate a simple match ID from filename
        const id = filename.replace(/[^a-zA-Z0-9]/g, '_').toUpperCase();
        setMatchId(id);
      }
      if (!leagueName) {
        // Try to detect league from common patterns
        if (filename.toLowerCase().includes('formula') || filename.toLowerCase().includes('f1')) {
          setLeagueName("FORMULA_1");
        } else if (filename.toLowerCase().includes('premier') || filename.toLowerCase().includes('epl')) {
          setLeagueName("PREMIER_LEAGUE");
        } else if (filename.toLowerCase().includes('champions') || filename.toLowerCase().includes('ucl')) {
          setLeagueName("CHAMPIONS_LEAGUE");
        } else {
          setLeagueName("GENERAL_SPORTS");
        }
      }
    }
  }, [file, contentTitle, matchId, leagueName]);

  const sortedBenchmarkVariants = useMemo(
    () =>
      benchmarkResult
        ? benchmarkResult.variants.slice().sort((a, b) => b.combined_confidence - a.combined_confidence)
        : [],
    [benchmarkResult],
  );
  const benchmarkAverageConfidence = useMemo(() => {
    if (!benchmarkResult || benchmarkResult.variants.length === 0) {
      return 0;
    }
    const totalConfidence = benchmarkResult.variants.reduce(
      (sum, variant) => sum + variant.combined_confidence,
      0,
    );
    return totalConfidence / benchmarkResult.variants.length;
  }, [benchmarkResult]);

  useEffect(() => {
    let mounted = true;
    let pollInterval: number | null = null;

    const loadData = async () => {
      if (!mounted) return;

      const [summaryData, healthData, items] = await Promise.all([
        fetchMetricsSummary().catch(() => null),
        fetchHealth().catch(() => null),
        fetchDetections().catch(() => []),
      ]);

      if (!mounted) return;

      setSummary(summaryData);
      setHealth(healthData);

      if (items.length > 0) {
        const trend = items
          .slice(0, 7)
          .reverse()
          .map((item, index) => ({
            label: String(index + 1).padStart(2, "0"),
            value: Math.round(item.confidence_score),
          }));
        setRecentConfidence(trend);
      }
    };

    loadData();

    pollInterval = window.setInterval(() => {
      if (mounted) {
        fetchMetricsSummary().then((data) => {
          if (mounted) setSummary(data);
        });
        fetchHealth().then((data) => {
          if (mounted) setHealth(data);
        });
      }
    }, 5000);

    return () => {
      mounted = false;
      if (pollInterval !== null) {
        window.clearInterval(pollInterval);
      }
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
    setJobStage("queued");
    setProgress({ video: 28, audio: 12 });

    let interval: number | null = null;

    try {
      interval = window.setInterval(() => {
        setProgress((current) => ({
          video: Math.min(current.video + 11, 94),
          audio: Math.min(current.audio + 9, 88),
        }));
      }, 220);

      const result = await generateFingerprint({
        title: contentTitle || matchId || file?.name || "Protected Content",
        league: leagueName || "UNKNOWN_LEAGUE",
        broadcastDate,
        file,
      }, {
        onProgress: (progress) => {
          setJobStage(progress.stage ?? progress.status);
        },
      });

      setProgress({ video: 100, audio: 100 });
      setMessage(
        `${result.message}. Content ID ${result.content_id} indexed with ${result.video_hash_count} protected hashes.`,
      );
      const refreshedSummary = await fetchMetricsSummary();
      setSummary(refreshedSummary);
      setBenchmarkResult(null);
    } catch {
      setError("Fingerprint generation failed. Verify the Flask backend is online.");
      setProgress({ video: 0, audio: 0 });
    } finally {
      if (interval !== null) {
        window.clearInterval(interval);
      }
      setJobStage(null);
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
    setJobStage("queued");
    setVariantProgress(null);

    try {
      const result = await runPiracyBenchmark({
        title: contentTitle || matchId || file?.name || "Protected Content",
        league: leagueName || "UNKNOWN_LEAGUE",
        broadcastDate,
        file,
      }, {
        onProgress: (progress) => {
          console.log('Progress received:', progress);
          const stage = progress.stage ?? progress.status;
          setJobStage(stage);
          
          if (progress.progress_data) {
            const data = progress.progress_data;
            console.log('Progress data:', data);
            
            if (stage === 'generating_variants') {
              setVariantProgress({
                current: 0,
                total: data.total_variants || 17,
                currentVariant: '',
                currentDescription: 'Initializing variant generation...',
                stage: 'generating',
                results: [],
              });
            } else if (stage === 'variant_generating') {
              setVariantProgress(prev => prev ? {
                ...prev,
                current: data.variant_index || 0,
                total: data.variant_total || 17,
                currentVariant: data.variant_name || '',
                currentDescription: data.variant_description || '',
                stage: 'generating',
              } : null);
            } else if (stage === 'variant_generated') {
              setVariantProgress(prev => prev ? {
                ...prev,
                current: data.variant_index || 0,
                total: data.variant_total || 17,
                currentVariant: data.variant_name || '',
                currentDescription: `✓ ${data.variant_description || ''}`,
                stage: 'generating',
              } : null);
            } else if (stage === 'variant_analyzing') {
              setVariantProgress(prev => prev ? {
                ...prev,
                current: data.variant_index || 0,
                total: data.variant_total || 17,
                currentVariant: data.variant_name || '',
                currentDescription: `Analyzing: ${data.variant_description || ''}`,
                stage: 'analyzing',
              } : null);
            } else if (stage === 'variant_analyzed') {
              setVariantProgress(prev => {
                const newResults = [...(prev?.results || [])];
                newResults.push({
                  name: data.variant_name || '',
                  description: data.variant_description || '',
                  videoConfidence: data.video_confidence || 0,
                  audioConfidence: data.audio_confidence || 0,
                  combinedConfidence: data.combined_confidence || 0,
                  isDetected: data.is_detected || false,
                });
                
                return prev ? {
                  ...prev,
                  current: data.variant_index || 0,
                  total: data.variant_total || 17,
                  currentVariant: data.variant_name || '',
                  currentDescription: `${data.is_detected ? '🔴 DETECTED' : '✓ Analyzed'}: ${data.variant_description || ''} (${data.combined_confidence?.toFixed(1)}%)`,
                  stage: 'analyzing',
                  results: newResults,
                } : null;
              });
            }
          }
        },
      });

      setBenchmarkResult(result);
      setVariantProgress(prev => prev ? { ...prev, stage: 'complete' } : null);
      
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
      setVariantProgress(null);
    } finally {
      setJobStage(null);
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
                  <span className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">Content Title</span>
                  <input
                    className="field-shell w-full"
                    placeholder="Auto-detected from filename"
                    value={contentTitle}
                    onChange={(event) => setContentTitle(event.target.value)}
                  />
                </label>

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
                  className="subtle-button w-full flex items-center justify-center gap-3 py-4 text-[10px] font-bold uppercase tracking-[0.2em]"
                  onClick={handleRunBenchmark}
                  disabled={loading || benchmarkLoading}
                >
                  {benchmarkLoading ? (
                    <>
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/20 border-t-white" />
                      Benchmarking 17-Variants...
                    </>
                  ) : (
                    "Execute Piracy Benchmark"
                  )}
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
                {jobStage ? (
                  <div className="rounded-2xl border border-cyan/20 bg-cyan/5 px-5 py-4 text-xs font-bold uppercase tracking-widest text-cyan leading-relaxed">
                    Background Stage: {jobStage.replace(/_/g, " ")}
                  </div>
                ) : null}
                {variantProgress ? (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-2xl border border-neon/20 bg-slate-950/60 p-6 space-y-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-display text-sm font-bold uppercase tracking-[0.2em] text-neon">
                        {variantProgress.stage === 'generating' ? '⚙️ Generating Variants' : 
                         variantProgress.stage === 'analyzing' ? '🔬 Analyzing Variants' : 
                         '✅ Benchmark Complete'}
                      </div>
                      <div className="font-mono text-xs text-slate-400">
                        {variantProgress.current}/{variantProgress.total}
                      </div>
                    </div>
                    
                    <div className="h-2 overflow-hidden rounded-full bg-slate-900/50">
                      <motion.div
                        className="h-full rounded-full bg-gradient-to-r from-neon/40 via-neon to-neon shadow-[0_0_15px_rgba(212,255,0,0.3)]"
                        animate={{ width: `${(variantProgress.current / variantProgress.total) * 100}%` }}
                        transition={{ type: "spring", bounce: 0, duration: 0.5 }}
                      />
                    </div>
                    
                    {variantProgress.currentVariant && (
                      <div className="text-xs font-medium text-slate-300 leading-relaxed">
                        <span className="text-cyan font-bold">{variantProgress.currentVariant}</span>: {variantProgress.currentDescription}
                      </div>
                    )}
                    
                    {variantProgress.results.length > 0 && (
                      <div className="mt-4 max-h-48 overflow-y-auto space-y-2 border-t border-white/5 pt-4">
                        {variantProgress.results.slice(-5).reverse().map((result, idx) => (
                          <div key={idx} className="flex items-center justify-between text-[10px] font-medium">
                            <span className={result.isDetected ? 'text-neon' : 'text-slate-500'}>
                              {result.isDetected ? '🔴' : '✓'} {result.description}
                            </span>
                            <span className="font-mono text-cyan">
                              {result.combinedConfidence.toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
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
            <div className="glass-card p-8 border-white/5 bg-white/[0.02]">
              <div className="font-display text-[10px] font-bold uppercase tracking-[0.35em] text-muted/40 mb-5">
                Benchmark Stats
              </div>
              <div className="space-y-8">
                <div>
                  <div className="font-display text-[9px] font-bold uppercase tracking-[0.2em] text-muted/60 mb-1">Detected Variants</div>
                  <div className="font-display text-4xl font-extrabold tracking-tighter text-neon">
                    {benchmarkResult.detected_count}<span className="text-xl text-muted/30 mx-1">/</span>{benchmarkResult.variant_count}
                  </div>
                </div>
                <div>
                  <div className="font-display text-[9px] font-bold uppercase tracking-[0.2em] text-muted/60 mb-1">Detection Rate</div>
                  <div className="font-display text-4xl font-extrabold tracking-tighter text-cyan">
                    {benchmarkResult.detection_rate.toFixed(1)}<span className="text-xl">%</span>
                  </div>
                </div>
                <div className="pt-4 border-t border-white/5">
                  <div className="font-display text-[9px] font-bold uppercase tracking-[0.2em] text-muted/60 mb-2">Output Directory</div>
                  <div className="font-mono text-[10px] text-slate-500 break-all leading-relaxed">
                    {benchmarkResult.output_dir}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {benchmarkResult ? (
        <div className="glass-card overflow-hidden">
          <div className="border-b border-white/5 bg-white/[0.02] px-8 py-6">
            <div className="font-display text-[10px] font-bold uppercase tracking-[0.35em] text-muted/40 mb-2">
              Final Report - Sentinel Benchmark
            </div>
            <div className="font-display text-2xl font-extrabold tracking-tight text-white">
              Piracy Detection Results
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-0">
              <thead>
                <tr className="border-b border-white/5 bg-slate-950/40 text-left">
                  <th className="px-8 py-5 font-display text-[9px] font-bold uppercase tracking-[0.35em] text-muted/60">Type</th>
                  <th className="px-8 py-5 font-display text-[9px] font-bold uppercase tracking-[0.35em] text-muted/60 text-center">Confidence</th>
                  <th className="px-8 py-5 font-display text-[9px] font-bold uppercase tracking-[0.35em] text-muted/60 text-center">Consistency</th>
                  <th className="px-8 py-5 font-display text-[9px] font-bold uppercase tracking-[0.35em] text-muted/60">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {sortedBenchmarkVariants.map((variant) => (
                  <tr key={variant.filename} className="group transition-colors hover:bg-white/[0.01]">
                    <td className="px-8 py-5 font-display text-[11px] font-bold uppercase tracking-[0.12em] text-white">
                      {variant.description}
                    </td>
                    <td className="px-8 py-5 text-center font-mono text-[11px] font-bold text-neon">
                      {variant.combined_confidence.toFixed(2)}%
                    </td>
                    <td className="px-8 py-5 text-center font-mono text-[11px] font-bold text-cyan/80">
                      {typeof variant.consistency_ratio === "number"
                        ? `${(variant.consistency_ratio * 100).toFixed(1)}%`
                        : "-"}
                    </td>
                    <td className="px-8 py-5">
                      <span
                        className={[
                          "inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest",
                          variant.is_detected
                            ? "border-neon/20 bg-neon/10 text-neon"
                            : "border-rose-500/20 bg-rose-500/5 text-rose-300",
                        ].join(" ")}
                      >
                        <span
                          className={[
                            "h-1.5 w-1.5 rounded-full",
                            variant.is_detected ? "bg-neon" : "bg-rose-500",
                          ].join(" ")}
                        />
                        {variant.is_detected ? "Detected" : "Missed"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="border-t border-white/5 bg-slate-950/30 px-8 py-5 text-[11px] font-bold uppercase tracking-[0.2em] text-slate-300">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <span>
                Detection Rate: {benchmarkResult.detected_count}/{benchmarkResult.variant_count} ({benchmarkResult.detection_rate.toFixed(1)}%)
              </span>
              <span>Average Confidence: {benchmarkAverageConfidence.toFixed(2)}%</span>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
