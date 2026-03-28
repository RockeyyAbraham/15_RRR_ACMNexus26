import { useEffect, useMemo, useState } from "react";
import ChartPanel from "../components/ChartPanel";
import DetectionFeed from "../components/DetectionFeed";
import StatCard from "../components/StatCard";
import { fetchDetections, fetchHealth, fetchMetricsSummary, getLiveSocketUrl } from "../services/api";
import type { DetectionApiItem, DetectionFeedItem, HealthApi, LivePayload, MetricsSummaryApi } from "../types";

function extractPlatform(streamUrl: string) {
  try {
    return new URL(streamUrl.startsWith("http") ? streamUrl : `https://${streamUrl}`).hostname
      .replace("www.", "")
      .split(".")[0]
      .toUpperCase();
  } catch {
    return "UNKNOWN";
  }
}

function formatDetection(item: DetectionApiItem): DetectionFeedItem {
  const timestamp = item.detected_at ? new Date(item.detected_at).toLocaleString() : "UNKNOWN";
  return {
    id: item.id,
    matchId: item.title || `MATCH #${item.id}`,
    platform: extractPlatform(item.stream_url),
    timestamp,
    confidence: item.confidence_score,
    hashPreview: `DET-${String(item.id).padStart(4, "0")}`,
    league: item.league,
    streamUrl: item.stream_url,
  };
}

export default function DetectionPage() {
  const [detections, setDetections] = useState<DetectionFeedItem[]>([]);
  const [socketLive, setSocketLive] = useState(false);
  const [summary, setSummary] = useState<MetricsSummaryApi | null>(null);
  const [health, setHealth] = useState<HealthApi | null>(null);

  useEffect(() => {
    let mounted = true;

    fetchDetections()
      .then((items) => {
        if (mounted && items.length > 0) {
          setDetections(items.map(formatDetection));
        }
      })
      .catch(() => undefined);

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

    const socket = new WebSocket(getLiveSocketUrl());

    socket.onopen = () => setSocketLive(true);
    socket.onclose = () => setSocketLive(false);
    socket.onerror = () => setSocketLive(false);
    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as LivePayload;
        if (payload.type === "detections_update" && Array.isArray(payload.data) && payload.data.length > 0) {
          setDetections(payload.data.map(formatDetection));
        }
      } catch {
        setSocketLive(false);
      }
    };

    return () => {
      mounted = false;
      socket.close();
    };
  }, []);

  const chartData = useMemo(
    () =>
      detections
        .slice(0, 7)
        .reverse()
        .map((item, index) => ({
          label: String(index + 1).padStart(2, "0"),
          value: Math.round(item.confidence),
        })),
    [detections],
  );

  const exportCsv = () => {
    const header = "Match ID,Platform,Timestamp,Confidence,Hash Preview,League,Stream URL";
    const rows = detections.map((item) =>
      [
        item.matchId,
        item.platform,
        item.timestamp,
        item.confidence.toFixed(1),
        item.hashPreview,
        item.league,
        item.streamUrl,
      ]
        .map((value) => `"${String(value).replace(/"/g, '""')}"`)
        .join(","),
    );
    const blob = new Blob([[header, ...rows].join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "sentinel_detection_feed.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      <div className="section-shell">
        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="panel-title mb-2">Threat Surveillance</div>
            <h1 className="panel-heading">Detection Feed</h1>
            <div className="mt-4 max-w-2xl text-[13px] font-medium leading-relaxed tracking-wide text-slate-400">
              Watch the active piracy stream ledger, confidence shifts, and live feed updates coming back from the Sentinel detection layer in real-time.
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <span className="data-chip">Realtime Feed</span>
            <span className="data-chip">Confidence Sync</span>
            <span className="data-chip">Live WebSocket</span>
          </div>
        </div>
      </div>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,3fr)_360px]">
        <div className="space-y-8">
          <div className="grid gap-6 md:grid-cols-3">
            <StatCard
              label="Detections Logged"
              value={String(summary?.detections_count ?? 0)}
              hint={`Auto action: ${summary?.auto_action_count ?? 0}`}
              accent="neon"
            />
            <StatCard
              label="Avg Confidence"
              value={`${(summary?.average_confidence ?? 0).toFixed(1)}%`}
              hint={`Manual review: ${summary?.manual_review_count ?? 0}`}
              accent="cyan"
            />
            <StatCard
              label="Peak Threat Level"
              value={(summary?.auto_action_count ?? 0) > 0 ? "CRITICAL" : "ELEVATED"}
              accent={(summary?.auto_action_count ?? 0) > 0 ? "danger" : "default"}
            />
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <button type="button" className="subtle-button px-6" onClick={exportCsv}>
              Export CSV
            </button>
            <button type="button" className="subtle-button px-6" onClick={() => setDetections([])}>
              Clear Log
            </button>
            <div
              className={`flex items-center gap-3 rounded-full border px-5 py-2.5 font-display text-[10px] font-bold uppercase tracking-widest transition-all duration-300 ${
                socketLive
                  ? "border-neon/20 bg-neon/5 text-neon shadow-[0_0_15px_rgba(212,255,0,0.1)]"
                  : "border-rose-500/20 bg-rose-500/5 text-rose-300"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${socketLive ? 'bg-neon animate-pulse shadow-[0_0_8px_rgba(212,255,0,0.6)]' : 'bg-rose-500'}`} />
              {socketLive ? "WebSocket Active" : "WebSocket Offline"}
            </div>
          </div>

          <DetectionFeed items={detections} />
        </div>

        <div className="space-y-6">
          <StatCard
            label="Protected Hash Mesh"
            value={String(summary?.protected_content_count ?? 0)}
            accent="neon"
          />
          <StatCard 
            label="System Health" 
            value={(health?.status ?? "offline").toUpperCase()} 
            accent={health?.status === 'online' ? 'cyan' : 'default'}
          />
          <ChartPanel
            title="Search Confidence Flow"
            data={chartData.length > 0 ? chartData : [{ label: "00", value: 0 }]}
          />
          <div className="glass-card p-8">
            <div className="font-display text-[9px] font-bold uppercase tracking-[0.3em] text-muted/60 mb-6">Network Telemetry</div>
            <div className="space-y-6">
              <div>
                <div className="font-display text-[10px] font-bold uppercase tracking-[0.15em] text-slate-400 mb-2">Active Nodes</div>
                <div className="flex flex-wrap gap-2">
                  {health?.engines?.map(engine => (
                    <span key={engine} className="rounded-md border border-white/5 bg-white/[0.02] px-2 py-1 text-[10px] font-bold text-cyan">
                      {engine}
                    </span>
                  )) ?? <span className="text-[10px] font-bold text-slate-600">NO NODES ONLINE</span>}
                </div>
              </div>
              <div className="flex items-center justify-between border-t border-white/5 pt-6">
                <span className="font-display text-[9px] font-bold uppercase tracking-[0.2em] text-muted/50 text-white/40">Latest Sync</span>
                <span className="font-mono text-[10px] font-bold text-slate-500">
                  {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : "--:--:--"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
