import type { DetectionFeedItem } from "../types";

type DetectionFeedProps = {
  items: DetectionFeedItem[];
};

export default function DetectionFeed({ items }: DetectionFeedProps) {
  return (
    <div className="glass-card p-4">
      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="rounded-2xl border border-neon/15 bg-slate-950/85 px-4 py-4 transition duration-200 hover:border-neon/40 hover:shadow-neon"
          >
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div className="font-display text-lg tracking-[0.04em] text-neon">{item.matchId}</div>
              <div className="font-display text-xs uppercase tracking-[0.22em] text-cyan">
                Platform: {item.platform}
              </div>
            </div>

            <div className="mt-2 text-sm uppercase tracking-[0.18em] text-slate-300">
              TS: {item.timestamp} | Confidence: {item.confidence.toFixed(1)}% | Hash: {item.hashPreview}
            </div>

            <div className="mt-2 text-sm text-muted">{item.streamUrl}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
