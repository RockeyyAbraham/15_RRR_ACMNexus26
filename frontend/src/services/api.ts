import axios from "axios";
import type { DetectionApiItem, FingerprintResponse, UploadPayload } from "../types";

const fallbackBaseUrl = "http://localhost:8000";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? fallbackBaseUrl,
});

export async function generateFingerprint({
  title,
  league,
  broadcastDate,
  file,
}: UploadPayload): Promise<FingerprintResponse> {
  const formData = new FormData();
  formData.append("video", file);
  formData.append("title", title);
  formData.append("league", league);
  formData.append("broadcast_date", broadcastDate);

  const { data } = await api.post<FingerprintResponse>("/upload/protected", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

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
  const base = api.defaults.baseURL ?? fallbackBaseUrl;
  if (base.startsWith("https://")) {
    return `${base.replace("https://", "wss://")}/live`;
  }
  return `${base.replace("http://", "ws://")}/live`;
}
