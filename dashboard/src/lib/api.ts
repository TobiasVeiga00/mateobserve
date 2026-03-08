// All API calls go through the Next.js server-side proxy at /api/collector/
// which injects the API key server-side — no secrets in the browser bundle.
const PROXY_BASE =
  typeof window !== "undefined"
    ? "/api/collector"
    : (process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://collector:8001");

interface RequestOptions {
  service?: string | null;
  minutes?: number;
}

async function fetchJSON<T>(path: string, opts?: RequestOptions & { limit?: number }): Promise<T> {
  const params = new URLSearchParams();
  if (opts?.service) params.set("service", opts.service);
  if (opts?.minutes) params.set("minutes", String(opts.minutes));
  if (opts?.limit) params.set("limit", String(opts.limit));
  const qs = params.toString();
  const url = `${PROXY_BASE}${path}${qs ? `?${qs}` : ""}`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Collector error: ${res.status}`);
  return res.json();
}

export interface Service {
  service: string;
  total_requests: number;
  last_seen: string | null;
}

export interface Overview {
  total_requests: number;
  error_count: number;
  error_rate: number;
  avg_latency_ms: number;
  max_latency_ms: number;
  requests_per_minute: number;
}

export interface LatencyEntry {
  endpoint: string;
  method: string;
  request_count: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  max_latency_ms: number;
}

export interface ErrorEntry {
  endpoint: string;
  method: string;
  total_requests: number;
  error_count: number;
  error_rate: number;
}

export interface TrafficBucket {
  bucket: string;
  requests: number;
}

export interface RecentError {
  service: string;
  endpoint: string;
  method: string;
  status_code: number;
  error: string | null;
  latency_ms: number;
  timestamp: string;
}

export const api = {
  services: () => fetchJSON<Service[]>("/services"),
  overview: (opts?: RequestOptions) =>
    fetchJSON<Overview>("/metrics/overview", opts),
  latency: (opts?: RequestOptions) =>
    fetchJSON<LatencyEntry[]>("/metrics/latency", opts),
  errors: (opts?: RequestOptions) =>
    fetchJSON<ErrorEntry[]>("/metrics/errors", opts),
  traffic: (opts?: RequestOptions) =>
    fetchJSON<TrafficBucket[]>("/metrics/traffic", opts),
  recentErrors: (opts?: RequestOptions & { limit?: number }) =>
    fetchJSON<RecentError[]>("/metrics/errors/recent", opts),
};
