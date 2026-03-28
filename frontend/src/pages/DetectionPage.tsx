import { useCallback, useEffect, useMemo, useState } from "react";
import ChartPanel from "../components/ChartPanel";
import DetectionFeed from "../components/DetectionFeed";
import StatCard from "../components/StatCard";
import { fetchDetections, fetchHealth, fetchMetricsSummary, getLiveSocketUrl } from "../services/api";
import type { DetectionApiItem, DetectionFeedItem, HealthApi, LivePayload, MetricsSummaryApi } from "../types";
import { extractPlatform } from "../utils/platform";
import { POLLING_INTERVALS, DISPLAY_LIMITS } from "../constants/thresholds";

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
  const [lastDetectionTime, setLastDetectionTime] = useState<string | null>(null);
  const [detectionStreak, setDetectionStreak] = useState(0);

  useEffect(() => {
    let mounted = true;
    let socket: WebSocket | null = null;
    let pollInterval: number | null = null;

    const loadData = async () => {
      if (!mounted) return;

      try {
        const [items, summaryData, healthData] = await Promise.all([
          fetchDetections().catch(() => []),
          fetchMetricsSummary().catch(() => null),
          fetchHealth().catch(() => null),
        ]);

        if (!mounted) return;

        console.log('DetectionPage - Loaded items:', items.length);
        console.log('DetectionPage - Summary:', summaryData);
        
        if (items.length > 0) {
          const formattedDetections = items.map(formatDetection);
          setDetections(formattedDetections);
          
          // Update streak and last detection time
          if (formattedDetections.length > 0) {
            setLastDetectionTime(formattedDetections[0].timestamp);
            setDetectionStreak(prev => prev + 1);
          }
        } else {
          setDetections([]);
          setDetectionStreak(0);
        }
        setSummary(summaryData);
        setHealth(healthData);
      } catch (error) {
        console.error('DetectionPage - Load error:', error);
        if (mounted) {
          setDetections([]);
          setSummary(null);
          setHealth(null);
        }
      }
    };

    loadData();

    pollInterval = window.setInterval(async () => {
      if (mounted) {
        try {
          const [items, summaryData, healthData] = await Promise.all([
            fetchDetections().catch(() => []),
            fetchMetricsSummary().catch(() => null),
            fetchHealth().catch(() => null),
          ]);
          
          if (mounted) {
            if (items.length > 0) {
              const formattedDetections = items.map(formatDetection);
              setDetections(formattedDetections);
              
              // Update streak and last detection time
              if (formattedDetections.length > 0) {
                setLastDetectionTime(formattedDetections[0].timestamp);
                setDetectionStreak(prev => prev + 1);
              }
            }
            setSummary(summaryData);
            setHealth(healthData);
          }
        } catch (error) {
          console.error('Error polling data:', error);
        }
      }
    }, POLLING_INTERVALS.METRICS);

    try {
      socket = new WebSocket(getLiveSocketUrl());

      socket.onopen = () => {
        if (mounted) setSocketLive(true);
      };
      socket.onclose = () => {
        if (mounted) setSocketLive(false);
      };
      socket.onerror = () => {
        if (mounted) setSocketLive(false);
      };
      socket.onmessage = (event) => {
        if (!mounted) return;
        try {
          const payload = JSON.parse(event.data) as LivePayload;
          if (payload.type === "detections_update" && Array.isArray(payload.data) && payload.data.length > 0) {
            const formattedDetections = payload.data.map(formatDetection);
            setDetections(formattedDetections);
            
            // Update streak and last detection time
            if (formattedDetections.length > 0) {
              setLastDetectionTime(formattedDetections[0].timestamp);
              setDetectionStreak(prev => prev + 1);
            }
          }
        } catch {
          setSocketLive(false);
        }
      };
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      setSocketLive(false);
    }

    return () => {
      mounted = false;
      if (socket) {
        socket.close();
      }
      if (pollInterval !== null) {
        window.clearInterval(pollInterval);
      }
    };
  }, []);

  const chartData = useMemo(
    () =>
      detections
        .slice(0, DISPLAY_LIMITS.RECENT_DETECTIONS)
        .reverse()
        .map((item, index) => ({
          label: String(index + 1).padStart(2, "0"),
          value: Math.round(item.confidence),
        })),
    [detections],
  );

  const exportCsv = useCallback(() => {
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
  }, [detections]);

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
            <span className="data-chip animate-pulse">Realtime Feed</span>
            <span className="data-chip">Confidence Sync</span>
            <span className={`data-chip ${socketLive ? 'bg-neon/20 text-neon animate-pulse' : ''}`}>
              {socketLive ? '🟢 Live WebSocket' : '🔴 WebSocket Offline'}
            </span>
            {detectionStreak > 0 && (
              <span className="data-chip bg-cyan/20 text-cyan">
                🔥 {detectionStreak} Streak
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,3fr)_360px]">
        <div className="space-y-8">
          {/* AI Summary Section */}
          {summary?.ai_summary && (
            <div className="hud-panel p-6">
              <div className="panel-title mb-4">🤖 AI Intelligence Briefing</div>
              <div className="rounded-xl border border-cyan/20 bg-cyan/5 p-4">
                <div className="flex items-start gap-3">
                  <div className="mt-1 text-cyan text-lg">🧠</div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-cyan mb-2">Sentinel AI Analysis</div>
                    <div className="text-xs leading-relaxed text-slate-300 italic">
                      "{summary.ai_summary}"
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI Per-Detection Analysis */}
          {detections.length > 0 && (
            <div className="hud-panel p-6">
              <div className="panel-title mb-4">🎯 AI Detection Analyst</div>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {detections.slice(0, 5).map((detection, index) => (
                  <div key={detection.id} className="rounded-xl border border-neon/20 bg-neon/5 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-bold text-neon">DETECTION #{detection.id}</span>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            detection.confidence >= 90 ? 'bg-rose/20 text-rose' : 
                            detection.confidence >= 70 ? 'bg-yellow/20 text-yellow' : 
                            'bg-slate/20 text-slate'
                          }`}>
                            {detection.confidence >= 90 ? 'HIGH PRIORITY' : 
                             detection.confidence >= 70 ? 'MEDIUM PRIORITY' : 
                             'LOW PRIORITY'}
                          </span>
                        </div>
                        
                        <div className="text-xs font-medium text-slate-300 mb-1">
                          {detection.matchId} • {detection.platform}
                        </div>
                        
                        <div className="text-xs text-slate-400 mb-2">
                          Confidence: {detection.confidence.toFixed(1)}% • {detection.timestamp}
                        </div>
                        
                        <div className="border-l-2 border-cyan/30 pl-3">
                          <div className="text-xs font-medium text-cyan mb-1">AI Recommendation:</div>
                          <div className="text-xs text-slate-300 italic">
                            {detection.confidence >= 90 ? 
                              "⚡ IMMEDIATE TAKEDOWN RECOMMENDED - High confidence match, strong legal standing" :
                              detection.confidence >= 70 ? 
                              "🔍 ENHANCED MONITORING - Monitor for escalation, gather additional evidence" :
                              "📊 LOGGING ONLY - Low confidence, continue monitoring pattern"
                            }
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-lg font-bold text-neon">
                          {detection.confidence.toFixed(0)}%
                        </div>
                        <div className="text-xs text-slate-400">match</div>
                      </div>
                    </div>
                  </div>
                ))}
                {detections.length > 5 && (
                  <div className="text-center text-xs text-slate-500 py-2">
                    +{detections.length - 5} more detections analyzed
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AI Pattern Analysis */}
          {detections.length > 1 && (
            <div className="hud-panel p-6">
              <div className="panel-title mb-4">📈 AI Pattern Analysis</div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-purple/20 bg-purple/5 p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-purple">🎯</span>
                    <span className="text-xs font-bold text-purple">Threat Assessment</span>
                  </div>
                  <div className="text-xs text-slate-300">
                    {detections.filter(d => d.confidence >= 90).length >= 3 ? 
                      "🚨 CRITICAL - Multiple high-confidence detections require immediate action" :
                      detections.filter(d => d.confidence >= 70).length >= 5 ? 
                      "⚠️ ELEVATED - Pattern of systematic piracy detected" :
                      "✅ STABLE - Isolated incidents, normal monitoring sufficient"
                    }
                  </div>
                </div>
                
                <div className="rounded-lg border border-green/20 bg-green/5 p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-green">📊</span>
                    <span className="text-xs font-bold text-green">Success Rate</span>
                  </div>
                  <div className="text-xs text-slate-300">
                    Historical takedown success: {detections.filter(d => d.confidence >= 85).length > 0 ? 
                      "~87% based on confidence thresholds" : 
                      "Insufficient data for prediction"
                    }
                  </div>
                </div>
              </div>
              
              <div className="mt-4 rounded-lg border border-cyan/20 bg-cyan/5 p-3">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-cyan">🤖</span>
                  <span className="text-xs font-bold text-cyan">AI Strategy Recommendation</span>
                </div>
                <div className="text-xs text-slate-300">
                  {detections.filter(d => d.confidence >= 90).length > 0 ? 
                    `Prioritize ${detections.filter(d => d.confidence >= 90).length} high-confidence targets for immediate takedown. Monitor ${detections.filter(d => d.confidence < 90).length} lower-confidence targets for pattern escalation.` :
                    "Continue monitoring all detections. Current confidence levels suggest enhanced evidence gathering before legal action."
                  }
                </div>
              </div>
            </div>
          )}

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
            <button type="button" className="subtle-button px-6" onClick={exportCsv} aria-label="Export detection feed to CSV">
              Export CSV
            </button>
            <button type="button" className="subtle-button px-6" onClick={() => setDetections([])} aria-label="Clear detection log">
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
          <div className="hud-panel p-4">
            <StatCard
              label="Protected Hash Mesh"
              value={String(summary?.protected_content_count ?? 0)}
              hint={`Last detection: ${lastDetectionTime || 'Never'}`}
              accent="neon"
            />
          </div>
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
