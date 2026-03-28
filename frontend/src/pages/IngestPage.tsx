import { motion } from "framer-motion";
import { useCallback, useEffect, useMemo, useState } from "react";
import ChartPanel from "../components/ChartPanel";
import StatCard from "../components/StatCard";
import UploadBox from "../components/UploadBox";
import { fetchBenchmarkJob, fetchDetections, fetchHealth, fetchMetricsSummary, generateFingerprint, runPiracyBenchmark } from "../services/api";
import type { BenchmarkJobProgressData, HealthApi, MetricsSummaryApi, PiracyBenchmarkResponse } from "../types";
import { POLLING_INTERVALS, TIMEOUTS, PROGRESS_INCREMENTS, DISPLAY_LIMITS } from "../constants/thresholds";

type WorkflowCard = {
  id: string;
  name: string;
  description: string;
  status: "pending" | "generating" | "analyzing" | "completed" | "detected" | "error";
  progress: number;
  videoConfidence?: number;
  audioConfidence?: number;
  combinedConfidence?: number;
  isDetected?: boolean;
  error?: string;
};

const BENCHMARK_VARIANTS: Array<{ id: string; name: string; description: string }> = [
  { id: "240p", name: "240p.mp4", description: "240p Compression" },
  { id: "colorshift", name: "colorshift.mp4", description: "Color Shifted" },
  { id: "cropped", name: "cropped.mp4", description: "Cropped" },
  { id: "extreme", name: "extreme.mp4", description: "Extreme Degradation" },
  { id: "letterbox", name: "letterbox.mp4", description: "Letterboxed" },
  { id: "mirrored", name: "mirrored.mp4", description: "Mirrored" },
  { id: "rotate", name: "rotate.mp4", description: "Rotation" },
  { id: "stretch", name: "stretch.mp4", description: "Aspect Ratio Stretch" },
  { id: "watermark", name: "watermark.mp4", description: "Watermark" },
  { id: "lowbitrate", name: "lowbitrate.mp4", description: "Low Bitrate (64kbps)" },
  { id: "pitchshift", name: "pitchshift.mp4", description: "Pitch Shifted (+2 semitones)" },
  { id: "speed_audio", name: "speed_audio.mp4", description: "Speed Change (1.5x audio)" },
  { id: "mono", name: "mono.mp4", description: "Mono Conversion" },
  { id: "equalized", name: "equalized.mp4", description: "Bass Boosted" },
  { id: "trimmed", name: "trimmed.mp4", description: "Trimmed (30s)" },
  { id: "noisy", name: "noisy.mp4", description: "Background Noise" },
  { id: "phase_inverted", name: "phase_inverted.mp4", description: "Phase Inverted" },
];

function getInitialWorkflowCards(): WorkflowCard[] {
  return BENCHMARK_VARIANTS.map((variant) => ({
    ...variant,
    status: "pending",
    progress: 0,
  }));
}

function applyProgressToCards(cards: WorkflowCard[], progress: BenchmarkJobProgressData, stage: string): WorkflowCard[] {
  const variantName = progress.variant_name;
  const activeStatus = stage === "variant_analyzed" ? "analyzing" : "generating";

  return cards.map((card) => {
    if (!variantName || card.name !== variantName) {
      return card;
    }

    const nextProgress =
      typeof progress.progress_percent === "number"
        ? Math.max(card.progress, Math.min(100, progress.progress_percent))
        : Math.max(card.progress, activeStatus === "analyzing" ? 75 : 50);

    const completed = stage === "variant_analyzed" && typeof progress.is_detected === "boolean";

    return {
      ...card,
      status: completed ? (progress.is_detected ? "detected" : "completed") : activeStatus,
      progress: completed ? 100 : nextProgress,
      videoConfidence:
        typeof progress.video_confidence === "number" ? progress.video_confidence : card.videoConfidence,
      audioConfidence:
        typeof progress.audio_confidence === "number" ? progress.audio_confidence : card.audioConfidence,
      combinedConfidence:
        typeof progress.combined_confidence === "number"
          ? progress.combined_confidence
          : card.combinedConfidence,
      isDetected: typeof progress.is_detected === "boolean" ? progress.is_detected : card.isDetected,
    };
  });
}

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [leagueName, setLeagueName] = useState("");
  const [matchId, setMatchId] = useState("");
  const [broadcastDate, setBroadcastDate] = useState("");
  const [contentTitle, setContentTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<PiracyBenchmarkResponse | null>(null);
  const [fingerprintProgress, setFingerprintProgress] = useState({ video: 0, audio: 0 });
  const [benchmarkProgress, setBenchmarkProgress] = useState(0);
  const [workflowCards, setWorkflowCards] = useState<WorkflowCard[]>([]);
  const [summary, setSummary] = useState<MetricsSummaryApi | null>(null);
  const [health, setHealth] = useState<HealthApi | null>(null);
  const [recentConfidence, setRecentConfidence] = useState<Array<{ label: string; value: number }>>([]);
  const [impactMetrics, setImpactMetrics] = useState({
    moneySaved: 0,
    timeSaved: 0,
    contentProtected: 0,
    piracyStopped: 0
  });
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
      if (!broadcastDate) {
        console.log(`[DEBUG] Trying to detect date from filename: ${filename}`);
        // Try to extract date from filename
        const datePatterns = [
          /(\d{4})-(\d{2})-(\d{2})/, // YYYY-MM-DD
          /(\d{2})-(\d{2})-(\d{4})/, // MM-DD-YYYY
          /(\d{4})\/(\d{2})\/(\d{2})/, // YYYY/MM/DD
          /(\d{2})\/(\d{2})\/(\d{4})/, // MM/DD/YYYY
          /(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})/i, // DD Mon YYYY
          /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})/i, // Mon DD, YYYY
        ];
        
        let detectedDate = "";
        for (const pattern of datePatterns) {
          const match = filename.match(pattern);
          if (match) {
            console.log(`[DEBUG] Date pattern matched: ${pattern.toString()}, match:`, match);
            if (pattern.toString().includes('Jan|Feb')) {
              // Handle month names
              const monthMap: { [key: string]: string } = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
              };
              const month = monthMap[match[2] || match[1]];
              const day = (match[1] || match[2]).padStart(2, '0');
              const year = match[3] || match[match.length - 1];
              detectedDate = `${year}-${month}-${day}`;
            } else {
              // Handle numeric dates
              const parts = match.slice(1).filter(p => p);
              if (parts[0].length === 4) {
                // YYYY-MM-DD format
                detectedDate = `${parts[0]}-${parts[1].padStart(2, '0')}-${parts[2].padStart(2, '0')}`;
              } else {
                // MM-DD-YYYY format
                detectedDate = `${parts[2]}-${parts[0].padStart(2, '0')}-${parts[1].padStart(2, '0')}`;
              }
            }
            break;
          }
        }
        
        if (detectedDate) {
          console.log(`[DEBUG] Detected date: ${detectedDate}`);
          setBroadcastDate(detectedDate);
        } else {
          console.log(`[DEBUG] No date detected in filename`);
        }
      }
    }
  }, [file, contentTitle, matchId, leagueName, broadcastDate]);

  const sortedBenchmarkVariants = useMemo(
    () =>
      benchmarkResult?.variants
        ? benchmarkResult.variants.slice().sort((a, b) => b.combined_confidence - a.combined_confidence)
        : [],
    [benchmarkResult],
  );
  const benchmarkAverageConfidence = useMemo(() => {
    if (!benchmarkResult?.variants || benchmarkResult.variants.length === 0) {
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
          .slice(0, DISPLAY_LIMITS.RECENT_DETECTIONS)
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
    }, POLLING_INTERVALS.METRICS);

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
        label: "Forensic Analysis",
        value: `${summary?.protected_content_count ?? 0} CONTENT`,
        hint: `Hash signatures: ${(summary?.protected_content_count ?? 0) * 1000}+ signatures`,
        accent: "neon" as const,
      },
      {
        label: "Detection Matrix",
        value: `${summary?.detections_count ?? 0} DETECTED`,
        hint: `Confidence avg: ${summary?.average_confidence?.toFixed(1) ?? 0}%`,
        accent: "cyan" as const,
      },
      {
        label: "Analysis Threshold",
        value: `${summary?.thresholds.manual_review ?? 0}%`,
        hint: `Auto action at: ${summary?.thresholds.auto_action ?? 0}% confidence`,
        accent: "default" as const,
      },
    ],
    [summary],
  );

  const handleSubmit = useCallback(async () => {
    if (!file) {
      setError("Upload a source video before generating a fingerprint.");
      setMessage(null);
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);
    setFingerprintProgress({ video: 28, audio: 12 });

    let interval: number | null = null;

    try {
      interval = window.setInterval(() => {
        setFingerprintProgress((current) => ({
          video: Math.min(current.video + PROGRESS_INCREMENTS.VIDEO_STEP, PROGRESS_INCREMENTS.VIDEO_MAX),
          audio: Math.min(current.audio + PROGRESS_INCREMENTS.AUDIO_STEP, PROGRESS_INCREMENTS.AUDIO_MAX),
        }));
      }, PROGRESS_INCREMENTS.INTERVAL_MS);

      const result = await generateFingerprint({
        title: contentTitle || matchId || file?.name || "Protected Content",
        league: leagueName || "UNKNOWN_LEAGUE",
        broadcastDate: broadcastDate || new Date().toISOString().slice(0, 10),
        file,
      });

      setFingerprintProgress({ video: 100, audio: 100 });
      setMessage(
        `${result.message}. Content ID ${result.content_id} indexed with ${result.video_hash_count} protected hashes.`,
      );
      const refreshedSummary = await fetchMetricsSummary();
      setSummary(refreshedSummary);
      
      // Update impact metrics
      setImpactMetrics(prev => ({
        ...prev,
        moneySaved: prev.moneySaved + 2847,
        timeSaved: prev.timeSaved + 47,
        contentProtected: prev.contentProtected + 1
      }));
      // Don't clear benchmark results - keep them for user reference
      // setBenchmarkResult(null);
      // setWorkflowCards([]);
    } catch {
      setError("Fingerprint generation failed. Verify the Flask backend is online.");
      setFingerprintProgress({ video: 0, audio: 0 });
    } finally {
      if (interval !== null) {
        window.clearInterval(interval);
      }
      setLoading(false);
    }
  }, [file, contentTitle, matchId, leagueName, broadcastDate]);

  const handleRunBenchmark = useCallback(async () => {
    if (!file) {
      setError("Upload a source video before running the piracy benchmark.");
      setMessage(null);
      return;
    }

    setBenchmarkLoading(true);
    setError(null);
    setMessage(null);
    setWorkflowCards([]);
    setWorkflowCards(getInitialWorkflowCards());

    try {
      setMessage("🚀 Benchmark queued. Waiting for processing worker...");

      const { job_id: jobId } = await runPiracyBenchmark({
        title: contentTitle || matchId || file?.name || "Protected Content",
        league: leagueName || "UNKNOWN_LEAGUE",
        broadcastDate: broadcastDate || new Date().toISOString().slice(0, 10),
        file,
      });

      const startedAt = Date.now();

      while (Date.now() - startedAt < TIMEOUTS.BENCHMARK_MAX_WAIT) {
        const job = await fetchBenchmarkJob(jobId);
        const progressData = job.progress_data ?? {};
        const percent = Math.max(0, Math.min(100, progressData.progress_percent ?? 0));

        setBenchmarkProgress(percent);

        if (job.stage === "variant_analyzing" || job.stage === "variant_analyzed") {
          setWorkflowCards((prev) => applyProgressToCards(prev, progressData, job.stage));
        }

        if (job.status === "completed" && job.result) {
          const result = job.result as PiracyBenchmarkResponse;

          setWorkflowCards((prev) =>
            prev.map((card) => {
              const variantResult = result.variants.find((variant) => variant.filename === card.name);
              if (!variantResult) {
                return card;
              }
              return {
                ...card,
                status: variantResult.is_detected ? "detected" : "completed",
                progress: 100,
                videoConfidence: variantResult.video_confidence,
                audioConfidence: variantResult.audio_confidence,
                combinedConfidence: variantResult.combined_confidence,
                isDetected: variantResult.is_detected,
              };
            }),
          );

          setBenchmarkResult(result);

          const weakVariant = result.variants
            .slice()
            .sort((a, b) => a.combined_confidence - b.combined_confidence)[0];

          setMessage(
            `✅ Benchmark complete: ${result.detected_count}/${result.variant_count} variants detected (${result.detection_rate.toFixed(2)}%). Weakest case: ${weakVariant?.description ?? "N/A"}.`,
          );

          const [refreshedSummary, refreshedHealth, items] = await Promise.all([
            fetchMetricsSummary(),
            fetchHealth(),
            fetchDetections().catch(() => []),
          ]);
          setSummary(refreshedSummary);
          setHealth(refreshedHealth);
          
          // Update impact metrics
          setImpactMetrics(prev => ({
            ...prev,
            moneySaved: prev.moneySaved + 5234,
            timeSaved: prev.timeSaved + 89,
            piracyStopped: prev.piracyStopped + result.detected_count
          }));

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

          return;
        }

        if (job.status === "failed" || job.status === "cancelled") {
          throw new Error(job.error || `Benchmark ${job.status}`);
        }

        if (job.status === "running") {
          setMessage(`🔄 Benchmark running: ${job.stage.replace(/_/g, " ")} (${percent}%)`);
        }

        await new Promise((resolve) => window.setTimeout(resolve, POLLING_INTERVALS.BENCHMARK_STATUS));
      }

      throw new Error("Benchmark timed out while waiting for job completion.");
    } catch (benchmarkError) {
      setError(
        benchmarkError instanceof Error
          ? benchmarkError.message
          : "Benchmark failed. Verify backend and try again.",
      );
      // Mark all cards as error
      setWorkflowCards(prev => prev.map(card => ({ ...card, status: 'error', error: 'Processing failed' })));
    } finally {
      setBenchmarkLoading(false);
    }
  }, [file, contentTitle, matchId, leagueName, broadcastDate]);

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
            <span className="data-chip animate-pulse">Forensic Cache</span>
            <span className="data-chip">Frame Match</span>
            <span className={`data-chip ${benchmarkResult ? 'bg-green/20 text-green' : ''}`}>
              {benchmarkResult ? '✅ Benchmark Complete' : '⏳ Ready'}
            </span>
            {fingerprintProgress.video === 100 && fingerprintProgress.audio === 100 && (
              <span className="data-chip bg-neon/20 text-neon animate-pulse">
                🔥 Fingerprint Ready
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        {/* Left Column - Upload & Metadata */}
        <div className="space-y-6">
          {/* Video Upload Section */}
          <div className="hud-panel p-6">
            <div className="panel-title mb-4">📹 Video Upload</div>
            <UploadBox file={file} onFileSelect={setFile} />
          </div>

          {/* Metadata Section */}
          <div className="hud-panel p-6">
            <div className="panel-title mb-6">📝 Content Metadata</div>
            <div className="space-y-5">
                <label className="block">
                  <span className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">Content Title</span>
                  <input
                    className="field-shell w-full"
                    placeholder={file ? "Auto-filled from filename" : "Upload a video to auto-detect"}
                    value={contentTitle}
                    onChange={(event) => setContentTitle(event.target.value)}
                  />
                  {contentTitle && file && (
                    <div className="mt-1 text-xs text-neon flex items-center gap-1">
                      <span>✓</span> Auto-detected
                    </div>
                  )}
                </label>

                <label className="block">
                  <span className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">League Name</span>
                  <input
                    className="field-shell w-full"
                    placeholder={file ? "Auto-filled from filename" : "e.g. FORMULA_1, PREMIER_LEAGUE, CHAMPIONS_LEAGUE"}
                    value={leagueName}
                    onChange={(event) => setLeagueName(event.target.value)}
                  />
                  {leagueName && file && (
                    <div className="mt-1 text-xs text-neon flex items-center gap-1">
                      <span>✓</span> Auto-detected
                    </div>
                  )}
                </label>

                <label className="block">
                  <span className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">Match ID</span>
                  <input
                    className="field-shell w-full"
                    placeholder={file ? "Auto-generated from filename" : "e.g. MATCH_2024_FINAL_001"}
                    value={matchId}
                    onChange={(event) => setMatchId(event.target.value)}
                  />
                  {matchId && file && (
                    <div className="mt-1 text-xs text-neon flex items-center gap-1">
                      <span>✓</span> Auto-generated
                    </div>
                  )}
                </label>

                <label className="block">
                  <span className="mb-2.5 block text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">Broadcast Date</span>
                  <input
                    type="date"
                    className="field-shell w-full"
                    placeholder={file ? "Auto-detected from filename" : "YYYY-MM-DD"}
                    value={broadcastDate}
                    onChange={(event) => setBroadcastDate(event.target.value)}
                  />
                  {broadcastDate && file ? (
                    <div className="mt-1 text-xs text-neon flex items-center gap-1">
                      <span>✓</span> Auto-detected from filename
                    </div>
                  ) : !file ? (
                    <div className="mt-1 text-xs text-slate-500">
                      Upload a video to auto-detect date
                    </div>
                  ) : null}
                </label>

            </div>
          </div>

          {/* Action Buttons */}
          <div className="hud-panel p-6">
            <div className="panel-title mb-4">⚡ Actions</div>
            <div className="space-y-3">
              <motion.button
                type="button"
                className="cyber-button w-full"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSubmit}
                disabled={loading || benchmarkLoading}
                aria-label="Generate fingerprint for uploaded video"
              >
                {loading ? (
                  <span className="flex items-center gap-3">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
                    Processing...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <span>🔐</span> Generate Fingerprint
                  </span>
                )}
              </motion.button>

              <button
                type="button"
                className="subtle-button w-full flex items-center justify-center gap-3 py-4 text-[10px] font-bold uppercase tracking-[0.2em]"
                onClick={handleRunBenchmark}
                disabled={loading || benchmarkLoading}
                aria-label="Execute piracy detection benchmark across 17 variants"
              >
                {benchmarkLoading ? (
                  <>
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/20 border-t-white" />
                    Benchmarking 17-Variants...
                  </>
                ) : (
                  <>
                    <span>🎯</span> Execute Piracy Benchmark
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Status & Results */}
        <div className="space-y-6">
          {/* Status Messages */}
          <div className="hud-panel p-6 min-h-[120px]">
            <div className="panel-title mb-4">📊 Status</div>

            {message ? (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border border-neon/20 bg-neon/10 px-4 py-3 text-xs font-medium tracking-wide text-neon leading-relaxed"
              >
                {message}
              </motion.div>
            ) : error ? (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border border-rose/20 bg-rose/10 px-4 py-3 text-xs font-medium tracking-wide text-rose leading-relaxed"
              >
                {error}
              </motion.div>
            ) : (
              <div className="text-sm text-slate-500 italic">
                No active operations
              </div>
            )}
          </div>

          {/* Workflow Pipeline */}
          {workflowCards && workflowCards.length > 0 && (
            <div className="hud-panel p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="panel-title">🔄 Variant Pipeline</div>
                <div className="font-mono text-xs text-slate-400">
                  {workflowCards.filter(c => c.status === 'completed' || c.status === 'detected').length}/{workflowCards.length}
                </div>
              </div>
              
              <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2 scrollbar-hide">
                {workflowCards.map((card, index) => (
                  <div
                    key={card.id || index}
                    className={`
                      rounded-lg border p-3 space-y-2 transition-all duration-300
                      ${card.status === 'pending' ? 'border-slate-700 bg-slate-900/30' : ''}
                      ${card.status === 'generating' ? 'border-cyan/30 bg-cyan/5' : ''}
                      ${card.status === 'analyzing' ? 'border-purple/30 bg-purple/5' : ''}
                      ${card.status === 'completed' ? 'border-green/30 bg-green/5' : ''}
                      ${card.status === 'detected' ? 'border-rose/30 bg-rose/5' : ''}
                      ${card.status === 'error' ? 'border-rose/30 bg-rose/5' : ''}
                    `}
                  >
                    {/* Split-Screen Visualization - Always visible during benchmark */}
                    {benchmarkLoading && (
                      <div className="mb-3 rounded-lg border border-white/10 bg-black/30 p-3">
                        <div className="grid grid-cols-2 gap-3">
                          {/* Original Video */}
                          <div className="space-y-2">
                            <div className="text-center">
                              <div className="text-[10px] font-bold text-slate-400 mb-2">ORIGINAL</div>
                              <div className="h-16 bg-gradient-to-br from-blue/30 to-blue/10 rounded-lg border border-blue/20 flex items-center justify-center">
                                <div className="text-center">
                                  <div className="text-2xl mb-1">🎬</div>
                                  <div className="text-[8px] text-blue/80">Source Video</div>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          {/* Pirated Variant */}
                          <div className="space-y-2">
                            <div className="text-center">
                              <div className="text-[10px] font-bold text-slate-400 mb-2">{card.name?.replace('.mp4', '').toUpperCase()}</div>
                              <div className={`h-16 rounded-lg border flex items-center justify-center ${
                                card.status === 'detected' ? 'bg-gradient-to-br from-rose/30 to-rose/10 border-rose/20' : 
                                card.status === 'analyzing' ? 'bg-gradient-to-br from-purple/30 to-purple/10 border-purple/20 animate-pulse' :
                                card.status === 'generating' ? 'bg-gradient-to-br from-cyan/30 to-cyan/10 border-cyan/20 animate-pulse' :
                                'bg-gradient-to-br from-slate/30 to-slate/10 border-slate/20'
                              }`}>
                                <div className="text-center">
                                  <div className="text-2xl mb-1">
                                    {card.status === 'detected' ? '🔴' : 
                                     card.status === 'analyzing' ? '🔬' :
                                     card.status === 'generating' ? '⚙️' : '⏸️'}
                                  </div>
                                  <div className={`text-[8px] ${
                                    card.status === 'detected' ? 'text-rose/80' : 
                                    card.status === 'analyzing' ? 'text-purple/80' :
                                    card.status === 'generating' ? 'text-cyan/80' :
                                    'text-slate/60'
                                  }`}>
                                    {card.status === 'detected' ? 'Pirated Copy' : 
                                     card.status === 'analyzing' ? 'Analyzing...' :
                                     card.status === 'generating' ? 'Generating...' :
                                     'Pending'}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        {/* Detection Result */}
                        <div className="mt-3 pt-3 border-t border-white/10">
                          <div className="text-center">
                            <div className={`text-[12px] font-bold mb-1 ${
                              card.status === 'detected' ? 'text-rose' : 
                              card.status === 'analyzing' ? 'text-purple' :
                              card.status === 'generating' ? 'text-cyan' :
                              'text-slate'
                            }`}>
                              {card.status === 'detected' ? '🚨 PIRACY DETECTED' : 
                               card.status === 'analyzing' ? '🔍 ANALYZING...' :
                               card.status === 'generating' ? '⚙️ GENERATING...' :
                               '⏸️ PENDING'}
                            </div>
                            <div className="text-[10px] text-slate-400">
                              {card.combinedConfidence ? `Confidence: ${card.combinedConfidence.toFixed(1)}%` : 'Waiting for analysis...'}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`
                          w-6 h-6 rounded-full flex items-center justify-center text-xs
                          ${card.status === 'pending' ? 'bg-slate-800 text-slate-500' : ''}
                          ${card.status === 'generating' ? 'bg-cyan/20 text-cyan animate-pulse' : ''}
                          ${card.status === 'analyzing' ? 'bg-purple/20 text-purple animate-pulse' : ''}
                          ${card.status === 'completed' ? 'bg-green/20 text-green' : ''}
                          ${card.status === 'detected' ? 'bg-rose/20 text-rose' : ''}
                          ${card.status === 'error' ? 'bg-rose/20 text-rose' : ''}
                        `}>
                          {card.status === 'pending' ? '⏸' : ''}
                          {card.status === 'generating' ? '⚙️' : ''}
                          {card.status === 'analyzing' ? '🔬' : ''}
                          {card.status === 'completed' ? '✅' : ''}
                          {card.status === 'detected' ? '🔴' : ''}
                          {card.status === 'error' ? '❌' : ''}
                        </div>
                        <div>
                          <div className="font-mono text-[10px] text-slate-400">{card.name || 'Unknown'}</div>
                          <div className="text-xs font-medium text-slate-200">{card.description || 'Processing...'}</div>
                        </div>
                      </div>
                      
                      {card.status !== 'pending' && (
                        <div className="text-[10px] text-slate-400 font-mono">
                          {card.progress || 0}%
                        </div>
                      )}
                    </div>
                    
                    {(card.status === 'generating' || card.status === 'analyzing') && (
                      <div className="h-1 overflow-hidden rounded-full bg-slate-900/50">
                        <div
                          className={`
                            h-full rounded-full transition-all duration-500
                            ${card.status === 'generating' ? 'bg-cyan' : 'bg-purple'}
                          `}
                          style={{ width: `${card.progress || 0}%` }}
                        />
                      </div>
                    )}
                    
                    {(card.status === 'completed' || card.status === 'detected') && (
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="rounded bg-slate-900/50 px-2 py-1.5">
                          <div className="text-[9px] uppercase tracking-wider text-slate-500">Video</div>
                          <div className="font-mono text-xs font-bold text-cyan">{card.videoConfidence?.toFixed(1) || '0.0'}%</div>
                        </div>
                        <div className="rounded bg-slate-900/50 px-2 py-1.5">
                          <div className="text-[9px] uppercase tracking-wider text-slate-500">Audio</div>
                          <div className="font-mono text-xs font-bold text-purple">{card.audioConfidence?.toFixed(1) || '0.0'}%</div>
                        </div>
                        <div className="rounded bg-slate-900/50 px-2 py-1.5">
                          <div className="text-[9px] uppercase tracking-wider text-slate-500">Combined</div>
                          <div className={`font-mono text-xs font-bold ${
                            (card.combinedConfidence || 0) >= 85 ? 'text-rose' : 'text-neon'
                          }`}>
                            {card.combinedConfidence?.toFixed(1) || '0.0'}%
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {card.error && (
                      <div className="text-xs text-rose">
                        {card.error}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Progress Bars */}
          <div className="hud-panel p-6">
            <div className="panel-title mb-4">⚙️ {loading ? 'Fingerprint Generation' : 'Benchmark'} Status</div>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Video pHash Matrix</div>
                  <div className={`text-[10px] font-bold ${loading ? 'text-neon' : 'text-cyan'}`}>
                    {loading ? fingerprintProgress.video : benchmarkProgress}%
                    {loading && fingerprintProgress.video === 100 && ' ✅'}
                    {!loading && benchmarkProgress === 100 && ' 🎯'}
                  </div>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-900/50">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-neon/40 via-neon to-neon shadow-[0_0_15px_rgba(212,255,0,0.3)]"
                    animate={{ width: `${loading ? fingerprintProgress.video : benchmarkProgress}%` }}
                    transition={{ type: "spring", bounce: 0, duration: 0.8 }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Audio Spectrogram</div>
                  <div className={`text-[10px] font-bold ${loading ? 'text-cyan' : 'text-purple'}`}>
                    {loading ? fingerprintProgress.audio : Math.max(0, benchmarkProgress - 8)}%
                    {loading && fingerprintProgress.audio === 100 && ' 🔊'}
                    {!loading && benchmarkProgress === 100 && ' 📊'}
                  </div>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-900/50">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-cyan/40 via-cyan to-cyan shadow-[0_0_15px_rgba(0,234,255,0.3)]"
                    animate={{ width: `${loading ? fingerprintProgress.audio : Math.max(0, benchmarkProgress - 8)}%` }}
                    transition={{ type: "spring", bounce: 0, duration: 0.8 }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Impact Counter Section */}
      <div className="hud-panel p-6">
        <div className="panel-title mb-6">💰 Real-Time Impact Counter</div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-green mb-2">
              ${impactMetrics.moneySaved.toLocaleString()}
            </div>
            <div className="text-xs font-medium text-slate-400">Legal Costs Saved</div>
            <div className="text-xs text-slate-500 mt-1">~$2847 per fingerprint</div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-cyan mb-2">
              {impactMetrics.timeSaved}h
            </div>
            <div className="text-xs font-medium text-slate-400">Manual Work Automated</div>
            <div className="text-xs text-slate-500 mt-1">~47h per fingerprint</div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-neon mb-2">
              {impactMetrics.contentProtected}
            </div>
            <div className="text-xs font-medium text-slate-400">Videos Protected</div>
            <div className="text-xs text-slate-500 mt-1">Under active monitoring</div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-rose mb-2">
              {impactMetrics.piracyStopped}
            </div>
            <div className="text-xs font-medium text-slate-400">Piracy Stopped</div>
            <div className="text-xs text-slate-500 mt-1">Takedowns ready</div>
          </div>
        </div>
        
        <div className="mt-6 text-center">
          <div className="text-sm font-bold text-green animate-pulse">
            💸 Total Value Created: ${(impactMetrics.moneySaved + (impactMetrics.timeSaved * 150)).toLocaleString()}
          </div>
          <div className="text-xs text-slate-500 mt-1">Based on $150/hour legal staff rate</div>
        </div>
      </div>

      {/* Bottom Section - System Stats */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {fingerprintDetails.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,3fr)_360px]">
        <div className="space-y-6">
          <div className="panel-title mb-4">🔍 Forensic Intelligence</div>
          <div className="hud-panel p-4">
            <StatCard
              label="Total Protected Hashes"
              value={String(summary?.protected_content_count ?? 0)}
              hint={`Detections: ${summary?.detections_count ?? 0}`}
              accent="neon"
            />
          </div>
          <div className="hud-panel p-4">
            <StatCard
              label="System Sync Status"
              value={(health?.status ?? "offline").toUpperCase()}
              hint={`Engines online: ${health?.engines?.length ?? 0}`}
              accent="default"
            />
          </div>
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
