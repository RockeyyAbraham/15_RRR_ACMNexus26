import { useEffect, useMemo, useState } from "react";
import ChartPanel from "../components/ChartPanel";
import DetectionFeed from "../components/DetectionFeed";
import StatCard from "../components/StatCard";
import { fetchDetections, getLiveSocketUrl } from "../services/api";
import type { DetectionApiItem, DetectionFeedItem, LivePayload } from "../types";

const fallbackDetections: DetectionFeedItem[] = [
  {
    id: 1,
    matchId: "MATCH #1247",
    platform: "TWITCH",
    timestamp: "14:23:17 UTC",
    confidence: 92.3,
    hashPreview: "8F2A...91E2",
    league: "EURO_PREMIER_CHAMPIONSHIP",
    streamUrl: "twitch.tv/piratesports123",
  },
  {
    id: 2,
    matchId: "MATCH #1246",
    platform: "KICK",
    timestamp: "14:22:04 UTC",
    confidence: 88.1,
    hashPreview: "3C1B...44D0",
    league: "EURO_PREMIER_CHAMPIONSHIP",
    streamUrl: "kick.com/mirrorstream",
  },
  {
    id: 3,
    matchId: "MATCH #1245",
    platform: "YOUTUBE",
    timestamp: "14:19:55 UTC",
    confidence: 94.7,
    hashPreview: "7E9D...01FF",
    league: "EURO_PREMIER_CHAMPIONSHIP",
    streamUrl: "youtube.com/live/watchcopy",
  },
];

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
  const [detections, setDetections] = useState<DetectionFeedItem[]>(fallbackDetections);
  const [socketLive, setSocketLive] = useState(false);

  useEffect(() => {
    let mounted = true;

    fetchDetections()
      .then((items) => {
        if (mounted && items.length > 0) {
          setDetections(items.map(formatDetection));
        }
      })
      .catch(() => undefined);

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
    <div className="space-y-6">
      <div>
        <div className="panel-title">Threat Surveillance</div>
        <h1 className="panel-heading mt-3">Detection Feed</h1>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,3fr)_340px]">
        <div className="space-y-5">
          <div className="grid gap-4 md:grid-cols-3">
            <StatCard label="Active Sessions" value="03" hint="/NODE_CLUSTER" accent="neon" />
            <StatCard label="Encryption Status" value="AES-256" />
            <StatCard label="Peak Threat Level" value="CRITICAL" accent="danger" />
          </div>

          <div className="flex flex-wrap gap-3">
            <button type="button" className="subtle-button" onClick={exportCsv}>
              Export CSV
            </button>
            <button type="button" className="subtle-button" onClick={() => setDetections([])}>
              Clear Log
            </button>
            <div
              className={[
                "rounded-full border px-4 py-3 font-display text-xs uppercase tracking-[0.22em]",
                socketLive
                  ? "border-neon/50 bg-neon/10 text-neon shadow-neon"
                  : "border-rose-500/30 bg-rose-500/10 text-rose-200",
              ].join(" ")}
            >
              {socketLive ? "WebSocket Live" : "WebSocket Offline"}
            </div>
          </div>

          <DetectionFeed items={detections} />
        </div>

        <div className="space-y-4">
          <StatCard label="Total Protected Hashes" value="14,209" accent="neon" />
          <StatCard label="System Sync Status" value="STABLE" />
          <ChartPanel
            title="Threat Confidence History"
            data={chartData.length > 0 ? chartData : [{ label: "00", value: 0 }]}
          />
          <div className="glass-card p-4">
            <div className="font-display text-xs uppercase tracking-[0.28em] text-neon">Global Traffic Monitor</div>
            <div className="mt-3 text-sm text-slate-300">
              Cross-referencing 4.2M packets/sec against known fingerprint signatures.
            </div>
            <div className="mt-4 font-display text-sm uppercase tracking-[0.22em] text-cyan">Latency: 12ms</div>
            <div className="mt-1 font-display text-sm uppercase tracking-[0.22em] text-neon">Uptime: 99.98%</div>
          </div>
        </div>
      </div>
    </div>
  );
}
