import axios from "axios";
import type { DetectionApiItem, FingerprintResponse, UploadPayload } from "../types";

// Connect directly to backend - CORS is enabled
const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
  console.log("generateFingerprint called with:", { title, league, broadcastDate, file });
  
  if (!file) {
    console.error("No file provided to generateFingerprint");
    throw new Error("No file provided");
  }
  
  const formData = new FormData();
  formData.append("video", file);
  formData.append("title", title);
  formData.append("league", league);
  formData.append("broadcast_date", broadcastDate);

  console.log("FormData entries:");
  for (let [key, value] of formData.entries()) {
    console.log(key, value);
  }

  const { data } = await api.post<FingerprintResponse>("/upload/protected", formData);

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
