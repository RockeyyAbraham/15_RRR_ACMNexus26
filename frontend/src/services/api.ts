import axios from "axios";
import type {
  CandidateApiItem,
  DetectionApiItem,
  FingerprintResponse,
  HealthApi,
  MetricsSummaryApi,
  PiracyBenchmarkResponse,
  UploadPayload,
} from "../types";

// Connect directly to backend - CORS is enabled
const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 8 * 60 * 1000;

export const api = axios.create({
  baseURL: baseUrl,
  timeout: 120000, // 2 minutes for large video uploads
});

type AsyncUploadQueuedResponse = {
  job_id: string;
  status: "queued";
  job_type: "protected_upload" | "piracy_benchmark";
};

type AsyncUploadJobResponse<T> = {
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  result?: T;
  error?: string;
};

const sleep = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

async function waitForAsyncJob<T>(jobId: string): Promise<T> {
  const started = Date.now();

  while (Date.now() - started < POLL_TIMEOUT_MS) {
    let data: AsyncUploadJobResponse<T>;
    try {
      const response = await api.get<AsyncUploadJobResponse<T>>(`/jobs/${jobId}`);
      data = response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        throw new Error(
          "Async job was not found on the backend. The server may have restarted during processing. Please retry the upload.",
        );
      }
      throw error;
    }

    if (data.status === "completed") {
      if (!data.result) {
        throw new Error("Upload completed but no result payload was returned.");
      }
      return data.result;
    }

    if (data.status === "failed") {
      throw new Error(data.error || "Upload job failed.");
    }

    if (data.status === "cancelled") {
      throw new Error("Upload job was cancelled.");
    }

    await sleep(POLL_INTERVAL_MS);
  }

  throw new Error("Upload timed out while waiting for processing to complete.");
}

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

  const { data } = await api.post<AsyncUploadQueuedResponse>("/upload/protected/async", formData, {
    timeout: 30000,
  });

  const finalResult = await waitForAsyncJob<FingerprintResponse>(data.job_id);

  return finalResult;
}

export async function runPiracyBenchmark({
  title,
  league,
  broadcastDate,
  file,
}: UploadPayload): Promise<PiracyBenchmarkResponse> {
  if (!file) {
    throw new Error("No file provided");
  }

  const formData = new FormData();
  formData.append("video", file);
  formData.append("title", title);
  formData.append("league", league);
  formData.append("broadcast_date", broadcastDate);

  const { data } = await api.post<AsyncUploadQueuedResponse>("/analysis/piracy-benchmark/async", formData, {
    timeout: 30000,
  });

  return waitForAsyncJob<PiracyBenchmarkResponse>(data.job_id);
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

export async function fetchCandidates(limit = 20): Promise<CandidateApiItem[]> {
  try {
    const { data } = await api.get<{ candidates?: CandidateApiItem[] }>(`/candidates?limit=${limit}&offset=0`);
    return Array.isArray(data?.candidates) ? data.candidates : [];
  } catch {
    return [];
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
