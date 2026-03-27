import { getDmcaDownloadUrl } from "../services/api";

const fallbackNotices = [
  { id: 1, caseId: "CASE_001", platform: "YouTube", status: "Under Review", priority: "High" },
  { id: 2, caseId: "CASE_002", platform: "Twitch", status: "Action Required", priority: "Critical" },
  { id: 3, caseId: "CASE_003", platform: "Kick", status: "Pending", priority: "High" },
  { id: 4, caseId: "CASE_004", platform: "Facebook", status: "Resolved", priority: "Medium" },
];

export default function LegalPage() {
  return (
    <div className="space-y-6">
      <div>
        <div className="panel-title">Compliance Command</div>
        <h1 className="panel-heading mt-3">Legal Enforcement</h1>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2.5fr)_320px]">
        <div className="space-y-5">
          <div className="rounded-2xl border border-rose-500/25 bg-rose-500/10 px-5 py-4 text-sm text-rose-100">
            DMCA NOTICE GENERATED FOR REVIEW - NOT AUTO-SENT. Legal team approval is required before platform submission.
          </div>

          <div className="glass-card overflow-hidden">
            <div className="grid grid-cols-[1.2fr_1fr_1fr_1fr_auto] gap-4 border-b border-white/10 px-5 py-4 font-display text-xs uppercase tracking-[0.22em] text-muted">
              <div>Case ID</div>
              <div>Platform</div>
              <div>Status</div>
              <div>Priority</div>
              <div>Action</div>
            </div>

            {fallbackNotices.map((notice) => (
              <div
                key={notice.caseId}
                className="grid grid-cols-[1.2fr_1fr_1fr_1fr_auto] items-center gap-4 border-b border-white/5 px-5 py-4 text-sm text-slate-200 last:border-b-0"
              >
                <div className="font-display tracking-[0.12em] text-white">{notice.caseId}</div>
                <div>{notice.platform}</div>
                <div>{notice.status}</div>
                <div>{notice.priority}</div>
                <a
                  className="subtle-button inline-flex items-center justify-center"
                  href={getDmcaDownloadUrl(notice.id)}
                >
                  Download
                </a>
              </div>
            ))}
          </div>

          <div className="flex flex-wrap gap-3">
            <button type="button" className="subtle-button">
              New Case
            </button>
            <button type="button" className="subtle-button">
              Export Report
            </button>
            <button type="button" className="subtle-button">
              Bulk Action
            </button>
          </div>
        </div>

        <div className="space-y-4">
          <div className="glass-card p-5">
            <div className="font-display text-xs uppercase tracking-[0.28em] text-muted">Active Cases</div>
            <div className="mt-3 font-display text-5xl tracking-[0.04em] text-neon">47</div>
          </div>
          <div className="glass-card p-5">
            <div className="font-display text-xs uppercase tracking-[0.28em] text-muted">Resolved This Month</div>
            <div className="mt-3 font-display text-5xl tracking-[0.04em] text-white">128</div>
          </div>
          <div className="glass-card p-5">
            <div className="font-display text-xs uppercase tracking-[0.28em] text-muted">Success Rate</div>
            <div className="mt-3 font-display text-5xl tracking-[0.04em] text-cyan">96.2%</div>
          </div>
        </div>
      </div>
    </div>
  );
}
