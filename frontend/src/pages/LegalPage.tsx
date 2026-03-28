import { useCallback, useEffect, useMemo } from "react";
import { fetchDetections, fetchMetricsSummary, getDmcaDownloadUrl, submitCandidate } from "../services/api";
import type { DetectionApiItem, MetricsSummaryApi } from "../types";
import usePersistedState from "../hooks/usePersistedState";
import { extractPlatform } from "../utils/platform";
import { CONFIDENCE_THRESHOLDS, POLLING_INTERVALS, DISPLAY_LIMITS } from "../constants/thresholds";

export default function LegalPage() {
  const [detections, setDetections] = usePersistedState<DetectionApiItem[]>("sentinel.legal.detections", []);
  const [summary, setSummary] = usePersistedState<MetricsSummaryApi | null>("sentinel.legal.summary", null);
  const [actionMessage, setActionMessage] = usePersistedState<string | null>("sentinel.legal.actionMessage", null);

  const loadPageData = async () => {
    const [detectionItems, summaryData] = await Promise.all([
      fetchDetections().catch(() => []),
      fetchMetricsSummary().catch(() => null),
    ]);
    setDetections(detectionItems);
    setSummary(summaryData);
  };

  useEffect(() => {
    let mounted = true;
    let pollInterval: number | null = null;

    if (mounted) {
      loadPageData();
    }

    pollInterval = window.setInterval(() => {
      if (mounted) {
        loadPageData();
      }
    }, POLLING_INTERVALS.METRICS);

    return () => {
      mounted = false;
      if (pollInterval !== null) {
        window.clearInterval(pollInterval);
      }
    };
  }, []);

  const legalNotices = useMemo(
    () =>
      detections.slice(0, DISPLAY_LIMITS.LEGAL_NOTICES).map((detection) => {
        const confidence = detection.confidence_score ?? 0;
        const status = detection.dmca_generated
          ? "Notice Generated"
          : confidence >= CONFIDENCE_THRESHOLDS.HIGH
            ? "Action Required"
            : "Under Review";
        const priority = confidence >= CONFIDENCE_THRESHOLDS.CRITICAL ? "Critical" : confidence >= CONFIDENCE_THRESHOLDS.AUTO_ACTION ? "High" : "Medium";
        return {
          id: detection.id,
          caseId: `CASE_${String(detection.id).padStart(4, "0")}`,
          platform: extractPlatform(detection.stream_url),
          status,
          priority,
        };
      }),
    [detections],
  );

  const successRate = useMemo(() => {
    const total = summary?.detections_count ?? 0;
    if (!total) {
      return "0.0%";
    }
    const ratio = ((summary?.auto_action_count ?? 0) / total) * 100;
    return `${ratio.toFixed(1)}%`;
  }, [summary]);

  const handleNewCase = useCallback(async () => {
    const rawUrl = window.prompt("Enter stream URL for new case:", "https://");
    if (!rawUrl) {
      return;
    }

    const url = rawUrl.trim();
    if (!url) {
      return;
    }

    try {
      const platform = extractPlatform(url).toLowerCase();
      const result = await submitCandidate({
        url,
        platform,
        eventContext: "Manual legal escalation",
      });
      setActionMessage(`New case queued: ${result.candidate_id}`);
      await loadPageData();
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : "Failed to create case");
    }
  }, [setActionMessage]);

  const handleExportReport = useCallback(() => {
    const header = "Case ID,Platform,Status,Priority,Detection ID";
    const rows = legalNotices.map((notice) =>
      [notice.caseId, notice.platform, notice.status, notice.priority, String(notice.id)]
        .map((value) => `\"${String(value).replace(/\"/g, '\"\"')}\"`)
        .join(","),
    );

    const blob = new Blob([[header, ...rows].join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "sentinel_legal_report.csv";
    link.click();
    URL.revokeObjectURL(url);
    setActionMessage("Legal report exported");
  }, [legalNotices, setActionMessage]);

  const handleBulkAction = useCallback(() => {
    const prioritized = legalNotices.filter((item) => item.priority === "Critical" || item.priority === "High");
    const selected = (prioritized.length > 0 ? prioritized : legalNotices).slice(0, DISPLAY_LIMITS.BULK_ACTION_MAX);
    selected.forEach((item) => {
      window.open(getDmcaDownloadUrl(item.id), "_blank", "noopener,noreferrer");
    });
    setActionMessage(`Opened ${selected.length} DMCA notice tabs`);
  }, [legalNotices, setActionMessage]);

  return (
    <div className="space-y-6">
      <div className="section-shell">
        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="panel-title mb-2">Compliance Command</div>
            <h1 className="panel-heading">Legal Enforcement</h1>
            <div className="mt-4 max-w-2xl text-[13px] font-medium leading-relaxed tracking-wide text-slate-400">
              Queue notices for review, package infringement evidence, and move takedown actions through the Sentinel compliance lane with full chain-of-custody.
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <span className="data-chip">Review Gate</span>
            <span className="data-chip">DMCA Queue</span>
            <span className="data-chip">Audit Trail</span>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2.5fr)_320px]">
        <div className="space-y-5">
          <div className="rounded-2xl border border-rose-500/25 bg-rose-500/10 px-5 py-4 text-sm text-rose-100">
            DMCA NOTICE GENERATED FOR REVIEW - NOT AUTO-SENT. Legal team approval is required before platform submission.
          </div>
          {actionMessage ? (
            <div className="rounded-2xl border border-neon/20 bg-neon/10 px-5 py-3 text-sm text-neon">{actionMessage}</div>
          ) : null}

          <div className="glass-card overflow-hidden">
            <div className="grid grid-cols-[1.4fr_1fr_1.2fr_1fr_auto] gap-4 border-b border-white/5 bg-white/[0.02] px-6 py-5 font-display text-[9px] font-bold uppercase tracking-[0.3em] text-muted/60">
              <div>Case Reference</div>
              <div>Platform</div>
              <div>Status</div>
              <div>Priority</div>
              <div className="text-right">Action</div>
            </div>

            <div className="divide-y divide-white/5">
              {legalNotices.map((notice) => (
                <div
                  key={notice.caseId}
                  className="grid grid-cols-[1.4fr_1fr_1.2fr_1fr_auto] items-center gap-4 px-6 py-5 transition-colors hover:bg-white/[0.01]"
                >
                  <div className="font-mono text-xs font-medium tracking-tight text-white">{notice.caseId}</div>
                  <div className="text-[11px] font-bold uppercase tracking-widest text-slate-400">{notice.platform}</div>
                  <div className="flex items-center gap-2 text-[11px] font-bold tracking-wide text-slate-300">
                    <span className={`h-1.5 w-1.5 rounded-full ${
                      notice.status.includes('Generated') ? 'bg-cyan shadow-[0_0_8px_rgba(0,234,255,0.4)]' : 
                      notice.status.includes('Required') ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]' : 'bg-slate-600'
                    }`} />
                    {notice.status}
                  </div>
                  <div className={`text-[11px] font-bold uppercase tracking-widest ${
                    notice.priority === 'Critical' ? 'text-rose-400' : 
                    notice.priority === 'High' ? 'text-amber-400' : 'text-slate-500'
                  }`}>
                    {notice.priority}
                  </div>
                  <div className="text-right">
                    <a
                      className="subtle-button px-4 py-2 text-[10px] uppercase font-bold tracking-widest"
                      href={getDmcaDownloadUrl(notice.id)}
                    >
                      Process
                    </a>
                  </div>
                </div>
              ))}
            </div>
            {legalNotices.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <div className="font-display text-[10px] font-bold uppercase tracking-[0.3em] text-muted/30">
                  No records staged for review
                </div>
              </div>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-4 pt-2">
            <button type="button" className="subtle-button min-w-[140px]" onClick={handleNewCase} aria-label="Create new legal case">
              New Case
            </button>
            <button type="button" className="subtle-button min-w-[140px]" onClick={handleExportReport} aria-label="Export legal report to CSV">
              Export Report
            </button>
            <button
              type="button"
              className="subtle-button min-w-[140px]"
              onClick={handleBulkAction}
              disabled={legalNotices.length === 0}
              aria-label="Process bulk DMCA actions"
            >
              Bulk Action
            </button>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-8 border-white/5 bg-white/[0.02]">
            <div className="font-display text-[10px] font-bold uppercase tracking-[0.35em] text-muted/40 mb-5">Command Stats</div>
            <div className="space-y-8">
              <div>
                <div className="font-display text-[9px] font-bold uppercase tracking-[0.2em] text-muted/60 mb-1">Active Cases</div>
                <div className="font-display text-4xl font-extrabold tracking-tighter text-neon">{summary?.detections_count ?? 0}</div>
              </div>
              <div>
                <div className="font-display text-[9px] font-bold uppercase tracking-[0.2em] text-muted/60 mb-1">Resolved MTD</div>
                <div className="font-display text-4xl font-extrabold tracking-tighter text-white">{summary?.auto_action_count ?? 0}</div>
              </div>
              <div>
                <div className="font-display text-[9px] font-bold uppercase tracking-[0.2em] text-muted/60 mb-1">Success Matrix</div>
                <div className="font-display text-4xl font-extrabold tracking-tighter text-cyan">{successRate}</div>
              </div>
            </div>
          </div>
          
          <div className="glass-card p-6 border-white/5 bg-white/[0.02]">
            <div className="font-display text-[9px] font-bold uppercase tracking-[0.3em] text-muted/60 mb-4">Chain of Custody</div>
            <div className="text-[11px] font-medium leading-relaxed text-slate-500">
              All legal actions are logged to the immutable forensic ledger with timestamped operator signatures.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
