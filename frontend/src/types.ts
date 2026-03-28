export type DetectionApiItem = {
  id: number;
  title: string;
  league: string;
  stream_url: string;
  confidence_score: number;
  detected_at: string;
  dmca_generated?: boolean;
};

export type MetricsSummaryApi = {
  protected_content_count: number;
  detections_count: number;
  average_confidence: number;
  auto_action_count: number;
  manual_review_count: number;
  candidate_count: number;
  queued_candidates: number;
  thresholds: {
    auto_action: number;
    manual_review: number;
  };
  async: {
    max_workers: number;
    max_queue_size: number;
    tracked_jobs: number;
    active_jobs: number;
  };
};

export type HealthApi = {
  status: string;
  engines: string[];
  async: {
    max_workers: number;
    max_queue_size: number;
    tracked_jobs: number;
    active_jobs: number;
  };
  timestamp: string;
};

export type CandidateApiItem = {
  candidate_id: string;
  url: string;
  platform: string;
  keyword_hits: string[];
  event_context: string;
  suspicion_score: number;
  source_timestamp?: string;
  status: string;
  verification_job_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
};

export type DetectionFeedItem = {
  id: number;
  matchId: string;
  platform: string;
  timestamp: string;
  confidence: number;
  hashPreview: string;
  league: string;
  streamUrl: string;
};

export type UploadPayload = {
  title: string;
  league: string;
  broadcastDate: string;
  file: File;
};

export type FingerprintResponse = {
  message: string;
  content_id: number;
  video_hash_count: number;
  processing_time_seconds: number;
};

export type PiracyBenchmarkVariant = {
  filename: string;
  description: string;
  issue_type: string;
  generation_status: string;
  generation_note?: string | null;
  video_confidence: number;
  audio_confidence: number;
  combined_confidence: number;
  consistency_ratio?: number | null;
  pattern_score: number;
  adaptive_threshold: number;
  decision_reason: string;
  is_detected: boolean;
};

export type PiracyBenchmarkResponse = {
  message: string;
  protected: FingerprintResponse;
  output_dir: string;
  variant_count: number;
  detected_count: number;
  detection_rate: number;
  variants: PiracyBenchmarkVariant[];
};

export type LivePayload = {
  type: string;
  data: DetectionApiItem[];
};
