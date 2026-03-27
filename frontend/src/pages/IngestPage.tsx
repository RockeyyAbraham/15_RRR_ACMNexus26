import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import ChartPanel from "../components/ChartPanel";
import StatCard from "../components/StatCard";
import UploadBox from "../components/UploadBox";
import { generateFingerprint } from "../services/api";

const chartData = [
  { label: "08:00", value: 52 },
  { label: "09:00", value: 48 },
  { label: "10:00", value: 61 },
  { label: "11:00", value: 79 },
  { label: "12:00", value: 57 },
  { label: "13:00", value: 68 },
];

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [leagueName, setLeagueName] = useState("EURO_PREMIER_CHAMPIONSHIP");
  const [matchId, setMatchId] = useState("UUID_88392_B");
  const [broadcastDate, setBroadcastDate] = useState(new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState({ video: 91, audio: 64 });

  const fingerprintDetails = useMemo(
    () => [
      {
        label: "Encryption Status",
        value: "VERIFIED",
        hint: "Manifest handshake complete.",
        accent: "neon" as const,
      },
      {
        label: "Node Latency",
        value: "0.002 ms",
        hint: "Global sync alignment locked.",
        accent: "cyan" as const,
      },
      {
        label: "Geo Redundancy",
        value: "TRI-REGION",
        hint: "Paris-IX / US-East / AP-South mirror online.",
        accent: "default" as const,
      },
    ],
    [],
  );

  const handleSubmit = async () => {
    console.log("handleSubmit called, file:", file);
    
    if (!file) {
      console.error("No file in handleSubmit");
      setError("Upload a source video before generating a fingerprint.");
      setMessage(null);
      return;
    }

    console.log("File details:", {
      name: file.name,
      size: file.size,
      type: file.type
    });

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

  return (
    <div className="space-y-6">
      <div className="section-shell">
        <div className="relative z-10 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="panel-title">Ingestion Command</div>
            <h1 className="panel-heading mt-3">Ingest Portal</h1>
            <div className="mt-3 max-w-2xl text-sm text-slate-300">
              Register protected media, generate hash signatures, and push a new asset into the Sentinel monitoring mesh.
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="data-chip">Video Lock</span>
            <span className="data-chip">Hash Mesh</span>
            <span className="data-chip">Live Index</span>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,3fr)_340px]">
        <div className="space-y-6">
          <div className="hud-panel p-5 md:p-6">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,1fr)]">
              <div>
                <div className="panel-title mb-4">Reference Video Source</div>
                <UploadBox file={file} onFileSelect={setFile} />
              </div>

              <div className="space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm text-slate-300">League Name</span>
                  <input
                    className="field-shell w-full"
                    value={leagueName}
                    onChange={(event) => setLeagueName(event.target.value)}
                  />
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm text-slate-300">Match ID</span>
                  <input
                    className="field-shell w-full"
                    value={matchId}
                    onChange={(event) => setMatchId(event.target.value)}
                  />
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm text-slate-300">Broadcast Date</span>
                  <input
                    type="date"
                    className="field-shell w-full"
                    value={broadcastDate}
                    onChange={(event) => setBroadcastDate(event.target.value)}
                  />
                </label>

                <motion.button
                  type="button"
                  className="cyber-button w-full"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={handleSubmit}
                  disabled={loading}
                >
                  {loading ? "Generating..." : "Generate Fingerprint"}
                </motion.button>

                {message ? (
                  <div className="rounded-xl border border-neon/25 bg-neon/10 px-4 py-3 text-sm text-neon">
                    {message}
                  </div>
                ) : null}
                {error ? (
                  <div className="rounded-xl border border-rose-500/25 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                    {error}
                  </div>
                ) : null}
              </div>
            </div>

            <div className="mt-6 grid gap-6 md:grid-cols-2">
              <div>
                <div className="mb-2 font-display text-xs uppercase tracking-[0.22em] text-muted">Video pHash</div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-900">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-neon to-lime-500 shadow-neon"
                    animate={{ width: `${progress.video}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="mb-2 font-display text-xs uppercase tracking-[0.22em] text-muted">
                  Audio Spectrogram
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-900">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-cyan to-neon shadow-cyan"
                    animate={{ width: `${progress.audio}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {fingerprintDetails.map((card) => (
              <StatCard key={card.label} {...card} />
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="panel-title">Global Intelligence Feed</div>
          <StatCard label="Total Protected Hashes" value="14,209" hint="+24h: 182" accent="neon" />
          <StatCard label="System Sync Status" value="STABLE" accent="default" />
          <ChartPanel title="Threat Confidence History" data={chartData} />
          <div className="glass-card p-4 font-display text-[11px] uppercase tracking-[0.28em] text-muted">
            Global traffic monitor | Latency: 12ms | Uptime: 99.98%
          </div>
        </div>
      </div>
    </div>
  );
}
