import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchDetections, fetchMetricsSummary, getDmcaDownloadUrl } from "../services/api";
import StatCard from "../components/StatCard";
import type { DetectionApiItem, MetricsSummaryApi } from "../types";
import { extractPlatform } from "../utils/platform";
import { POLLING_INTERVALS } from "../constants/thresholds";

export default function EvidencePage() {
  const [summary, setSummary] = useState<MetricsSummaryApi | null>(null);
  const [detections, setDetections] = useState<DetectionApiItem[]>([]);
  const [selectedDetection, setSelectedDetection] = useState<DetectionApiItem | null>(null);
  const [graphMode, setGraphMode] = useState<'network' | 'timeline' | 'confidence'>('network');
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);

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
          <div className="flex items-center justify-between mb-8">
            <div className="panel-title">Interactive Evidence Graph</div>
            <div className="flex gap-2">
              <button
                onClick={() => setGraphMode('network')}
                className={`px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all ${
                  graphMode === 'network' ? 'bg-neon/20 text-neon border-neon/30' : 'bg-slate/10 text-slate border-slate/30'
                } border`}
              >
                Network
              </button>
              <button
                onClick={() => setGraphMode('timeline')}
                className={`px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all ${
                  graphMode === 'timeline' ? 'bg-cyan/20 text-cyan border-cyan/30' : 'bg-slate/10 text-slate border-slate/30'
                } border`}
              >
                Timeline
              </button>
              <button
                onClick={() => setGraphMode('confidence')}
                className={`px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all ${
                  graphMode === 'confidence' ? 'bg-rose/20 text-rose border-rose/30' : 'bg-slate/10 text-slate border-slate/30'
                } border`}
              >
                Confidence
              </button>
            </div>
          </div>
          
          {/* Interactive Graph Container */}
          <div className="relative h-[380px] rounded-3xl border border-white/5 bg-slate-950/40 overflow-hidden">
            {graphMode === 'network' && (
              <div 
                className="absolute inset-0 p-6"
                onMouseMove={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  setMousePosition({
                    x: e.clientX - rect.left,
                    y: e.clientY - rect.top
                  });
                }}
                onMouseLeave={() => {
                  setMousePosition({ x: 0, y: 0 });
                  setHoveredNode(null);
                }}
              >
                {/* Network Graph Visualization */}
                <div className="relative w-full h-full">
                  {/* Central Node */}
                  <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-r from-neon to-cyan border-2 border-neon/50 flex items-center justify-center animate-pulse">
                      <span className="text-2xl">🎯</span>
                    </div>
                    <div className="text-center mt-2 text-xs font-bold text-neon">Sentinel Core</div>
                  </div>
                  
                  {/* Detection Nodes with Cursor Proximity */}
                  {detections.slice(0, 8).map((detection, index) => {
                    const angle = (index * 45) * (Math.PI / 180);
                    const baseRadius = 120;
                    const x = Math.cos(angle) * baseRadius;
                    const y = Math.sin(angle) * baseRadius;
                    
                    // Calculate cursor proximity effect
                    const nodeCenterX = 190 + x; // 190 is center of container
                    const nodeCenterY = 190 + y;
                    const distance = Math.sqrt(
                      Math.pow(mousePosition.x - nodeCenterX, 2) + 
                      Math.pow(mousePosition.y - nodeCenterY, 2)
                    );
                    
                    const maxDistance = 80;
                    const proximityEffect = Math.max(0, 1 - distance / maxDistance);
                    const scale = 1 + proximityEffect * 0.3;
                    const glowIntensity = proximityEffect;
                    const isHovered = hoveredNode === index;
                    
                    return (
                      <div
                        key={detection.id}
                        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all duration-200 ease-out"
                        style={{ 
                          transform: `translate(${x}px, ${y}px) translate(-50%, -50%) scale(${scale})`,
                          zIndex: isHovered ? 20 : Math.floor(proximityEffect * 10)
                        }}
                        onClick={() => setSelectedDetection(detection)}
                        onMouseEnter={() => setHoveredNode(index)}
                        onMouseLeave={() => setHoveredNode(null)}
                      >
                        <div className={`w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${
                          detection.confidence_score >= 90 ? 'bg-rose/20 border-rose/50 text-rose' :
                          detection.confidence_score >= 70 ? 'bg-yellow/20 border-yellow/50 text-yellow' :
                          'bg-slate/20 border-slate/50 text-slate'
                        } ${
                          isHovered || glowIntensity > 0.3 ? 'shadow-lg' : ''
                        }`}
                        style={{
                          boxShadow: isHovered || glowIntensity > 0.3 
                            ? `0 0 ${20 + glowIntensity * 30}px rgba(${
                                detection.confidence_score >= 90 ? '248, 113, 113' :
                                detection.confidence_score >= 70 ? '250, 204, 21' :
                                '148, 163, 184'
                              }, ${0.3 + glowIntensity * 0.4})`
                            : 'none'
                        }}
                        >
                          <span className={`text-lg transition-transform duration-200 ${
                            isHovered || glowIntensity > 0.3 ? 'scale-125' : ''
                          }`}>
                            {detection.confidence_score >= 90 ? '🔴' : detection.confidence_score >= 70 ? '🟡' : '⚪'}
                          </span>
                        </div>
                        <div className={`text-center mt-1 text-[8px] font-mono transition-all duration-200 ${
                          isHovered || glowIntensity > 0.3 ? 'text-white font-bold' : 'text-slate-400'
                        }`}>
                          {detection.id}
                        </div>
                        
                        {/* Proximity Ring Effect */}
                        {glowIntensity > 0.1 && (
                          <div 
                            className="absolute inset-0 rounded-full border-2 animate-ping"
                            style={{
                              borderColor: `rgba(${
                                detection.confidence_score >= 90 ? '248, 113, 113' :
                                detection.confidence_score >= 70 ? '250, 204, 21' :
                                '148, 163, 184'
                              }, ${glowIntensity * 0.5})`,
                              transform: `scale(${1.5 + glowIntensity})`
                            }}
                          />
                        )}
                      </div>
                    );
                  })}
                  
                  {/* Connection Lines */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    {detections.slice(0, 8).map((_, index) => {
                      const angle = (index * 45) * (Math.PI / 180);
                      const radius = 120;
                      const x = Math.cos(angle) * radius + 50; // 50 is center offset
                      const y = Math.sin(angle) * radius + 50;
                      
                      return (
                        <line
                          key={index}
                          x1="50%"
                          y1="50%"
                          x2={`${x}%`}
                          y2={`${y}%`}
                          stroke="rgba(212, 255, 0, 0.2)"
                          strokeWidth="1"
                          className="animate-pulse"
                        />
                      );
                    })}
                  </svg>
                </div>
                
                {selectedDetection && (
                  <div className="absolute bottom-4 left-4 right-4 bg-slate-900/90 border border-neon/20 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-bold text-neon">Detection #{selectedDetection.id}</div>
                        <div className="text-[10px] text-slate-400">{extractPlatform(selectedDetection.stream_url)}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-rose">{selectedDetection.confidence_score.toFixed(1)}%</div>
                        <div className="text-[8px] text-slate-400">confidence</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {graphMode === 'timeline' && (
              <div 
                className="absolute inset-0 p-6"
                onMouseMove={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  setMousePosition({
                    x: e.clientX - rect.left,
                    y: e.clientY - rect.top
                  });
                }}
                onMouseLeave={() => {
                  setMousePosition({ x: 0, y: 0 });
                  setHoveredNode(null);
                }}
              >
                {/* Timeline Graph */}
                <div className="h-full flex items-end justify-between gap-2">
                  {detections.slice(0, 12).map((detection, index) => {
                    // Calculate cursor proximity for timeline bars
                    const barWidth = 30; // Approximate width of each bar
                    const barLeft = (index * barWidth) + 24; // 24 is padding
                    const barHeight = (detection.confidence_score / 100) * 280; // 280 is max height
                    const barTop = 380 - barHeight; // 380 is container height
                    
                    const barCenterX = barLeft + (barWidth / 2);
                    const barCenterY = barTop + (barHeight / 2);
                    const distance = Math.sqrt(
                      Math.pow(mousePosition.x - barCenterX, 2) + 
                      Math.pow(mousePosition.y - barCenterY, 2)
                    );
                    
                    const maxDistance = 60;
                    const proximityEffect = Math.max(0, 1 - distance / maxDistance);
                    const scale = 1 + proximityEffect * 0.2;
                    const glowIntensity = proximityEffect;
                    const isHovered = hoveredNode === index;
                    
                    return (
                      <div
                        key={detection.id}
                        className="flex-1 flex flex-col items-center gap-2 cursor-pointer group transition-all duration-200 ease-out"
                        onClick={() => setSelectedDetection(detection)}
                        onMouseEnter={() => setHoveredNode(index)}
                        onMouseLeave={() => setHoveredNode(null)}
                        style={{ transform: `scaleY(${scale})` }}
                      >
                        <div 
                          className={`w-full rounded-t-lg transition-all duration-200 ${
                            detection.confidence_score >= 90 ? 'bg-rose' :
                            detection.confidence_score >= 70 ? 'bg-yellow' :
                            'bg-slate'
                          } ${isHovered || glowIntensity > 0.3 ? 'shadow-lg' : ''}`}
                          style={{ 
                            height: `${(detection.confidence_score / 100) * 80}%`,
                            boxShadow: isHovered || glowIntensity > 0.3 
                              ? `0 0 ${15 + glowIntensity * 20}px rgba(${
                                  detection.confidence_score >= 90 ? '248, 113, 113' :
                                  detection.confidence_score >= 70 ? '250, 204, 21' :
                                  '148, 163, 184'
                                }, ${0.3 + glowIntensity * 0.4})`
                              : 'none'
                          }}
                        />
                        <div className={`text-[8px] font-mono transition-all duration-200 ${
                          isHovered || glowIntensity > 0.3 ? 'text-white font-bold' : 'text-slate-400'
                        }`}>
                          {detection.id}
                        </div>
                        
                        {/* Proximity Glow Effect */}
                        {glowIntensity > 0.1 && (
                          <div 
                            className="absolute inset-0 rounded-t-lg animate-pulse"
                            style={{
                              background: `linear-gradient(to top, rgba(${
                                detection.confidence_score >= 90 ? '248, 113, 113' :
                                detection.confidence_score >= 70 ? '250, 204, 21' :
                                '148, 163, 184'
                              }, ${glowIntensity * 0.3}), transparent)`,
                              transform: `scaleY(${1.2 + glowIntensity * 0.3})`
                            }}
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
                
                {selectedDetection && (
                  <div className="absolute top-4 left-4 bg-slate-900/90 border border-cyan/20 rounded-lg p-3">
                    <div className="text-xs font-bold text-cyan">Timeline View</div>
                    <div className="text-[10px] text-slate-400">Detection #{selectedDetection.id}</div>
                    <div className="text-lg font-bold text-cyan">{selectedDetection.confidence_score.toFixed(1)}%</div>
                  </div>
                )}
              </div>
            )}
            
            {graphMode === 'confidence' && (
              <div className="absolute inset-0 p-6">
                {/* Confidence Distribution */}
                <div className="h-full flex flex-col justify-center gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <div className="w-20 text-[10px] text-rose font-bold">HIGH (90%+)</div>
                      <div className="flex-1 h-8 bg-rose/20 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-rose transition-all duration-1000"
                          style={{ width: `${(detections.filter(d => d.confidence_score >= 90).length / Math.max(detections.length, 1)) * 100}%` }}
                        />
                      </div>
                      <div className="text-[10px] text-rose font-bold">
                        {detections.filter(d => d.confidence_score >= 90).length}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <div className="w-20 text-[10px] text-yellow font-bold">MED (70-89%)</div>
                      <div className="flex-1 h-8 bg-yellow/20 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-yellow transition-all duration-1000"
                          style={{ width: `${(detections.filter(d => d.confidence_score >= 70 && d.confidence_score < 90).length / Math.max(detections.length, 1)) * 100}%` }}
                        />
                      </div>
                      <div className="text-[10px] text-yellow font-bold">
                        {detections.filter(d => d.confidence_score >= 70 && d.confidence_score < 90).length}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <div className="w-20 text-[10px] text-slate font-bold">LOW (&lt;70%)</div>
                      <div className="flex-1 h-8 bg-slate/20 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-slate transition-all duration-1000"
                          style={{ width: `${(detections.filter(d => d.confidence_score < 70).length / Math.max(detections.length, 1)) * 100}%` }}
                        />
                      </div>
                      <div className="text-[10px] text-slate font-bold">
                        {detections.filter(d => d.confidence_score < 70).length}
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-6 text-center">
                    <div className="text-2xl font-bold text-neon">
                      {detections.length > 0 ? (detections.reduce((sum, d) => sum + d.confidence_score, 0) / detections.length).toFixed(1) : '0.0'}%
                    </div>
                    <div className="text-xs text-slate-400">Average Confidence</div>
                  </div>
                </div>
              </div>
            )}
            
            {detections.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center text-slate-500">
                <div className="mb-4 h-16 w-16 animate-pulse rounded-full border border-neon/20 bg-neon/5" />
                <div className="text-sm uppercase tracking-[0.2em]">No detections captured yet</div>
                <div className="text-xs mt-2">Run a benchmark to populate evidence graph</div>
              </div>
            )}
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
