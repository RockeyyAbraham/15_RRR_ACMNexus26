import axios from "axios";
import type {
  BenchmarkJobStartResponse,
  BenchmarkJobStatusResponse,
  DetectionApiItem,
  FingerprintResponse,
  HealthApi,
  MetricsSummaryApi,
  UploadPayload,
} from "../types";

// Connect directly to backend - CORS is enabled
const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: baseUrl,
  timeout: 120000, // 2 minutes for large video uploads
});

export async function generateFingerprint({
  title,
  league,
  broadcastDate,
  file,
}: UploadPayload): Promise<FingerprintResponse> {
  if (!file) {
    throw new Error("No file provided");
  }
  
  const formData = new FormData();
  formData.append("video", file);
  formData.append("title", title);
  formData.append("league", league);
  formData.append("broadcast_date", broadcastDate);

  const { data } = await api.post<FingerprintResponse>("/upload/protected", formData, {
    timeout: 10 * 60 * 1000,
  });

  return data;
}

export async function runPiracyBenchmark({
  title,
  league,
  broadcastDate,
  file,
}: UploadPayload): Promise<BenchmarkJobStartResponse> {
  if (!file) {
    throw new Error("No file provided");
  }

  const formData = new FormData();
  formData.append("video", file);
  formData.append("title", title);
  formData.append("league", league);
  formData.append("broadcast_date", broadcastDate);

  const { data } = await api.post<BenchmarkJobStartResponse>("/analysis/piracy-benchmark/async", formData, {
    timeout: 2 * 60 * 1000,
  });

  return data;
}

export async function fetchBenchmarkJob(jobId: string): Promise<BenchmarkJobStatusResponse> {
  const { data } = await api.get<BenchmarkJobStatusResponse>(`/jobs/${jobId}`);
  return data;
}

export async function fetchDetections(): Promise<DetectionApiItem[]> {
  const { data } = await api.get<{ detections?: DetectionApiItem[] } | DetectionApiItem[]>("/detections");
  if (Array.isArray(data)) {
    return data;
  }
  if (Array.isArray(data?.detections)) {
    return data.detections;
  }
  return [];
}

export async function fetchMetricsSummary(): Promise<MetricsSummaryApi | null> {
  try {
    const { data } = await api.get<MetricsSummaryApi>("/metrics/summary");
    return data;
  } catch {
    return null;
  }
}

export async function fetchHealth(): Promise<HealthApi | null> {
  try {
    const { data } = await api.get<HealthApi>("/health");
    return data;
  } catch {
    return null;
  }
}

export async function submitCandidate(payload: {
  url: string;
  platform?: string;
  eventContext?: string;
}) {
  const { data } = await api.post("/candidates/submit", {
    url: payload.url,
    platform: payload.platform ?? "manual",
    event_context: payload.eventContext ?? "Manual legal case submission",
  });
  return data;
}

export function getDmcaDownloadUrl(detectionId: number) {
  return `${api.defaults.baseURL}/detections/${detectionId}/dmca`;
}

export function getLiveSocketUrl() {
  // In development, connect directly to backend WebSocket (proxy doesn't handle WS well)
  if (import.meta.env.DEV) {
    return "ws://localhost:8000/live";
  }
  
  const base = api.defaults.baseURL ?? "http://localhost:8000";
  if (base.startsWith("https://")) {
    return `${base.replace("https://", "wss://")}/live`;
  }
  return `${base.replace("http://", "ws://")}/live`;
}
