export function extractPlatform(streamUrl: string): string {
  try {
    const url = streamUrl.startsWith("http") ? streamUrl : `https://${streamUrl}`;
    return new URL(url).hostname
      .replace("www.", "")
      .split(".")[0]
      .toUpperCase();
  } catch {
    return "UNKNOWN";
  }
}
