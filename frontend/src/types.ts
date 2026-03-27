export type DetectionApiItem = {
  id: number;
  title: string;
  league: string;
  stream_url: string;
  confidence_score: number;
  detected_at: string;
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
  hash_count: number;
  processing_time_seconds: number;
};

export type LivePayload = {
  type: string;
  data: DetectionApiItem[];
};
