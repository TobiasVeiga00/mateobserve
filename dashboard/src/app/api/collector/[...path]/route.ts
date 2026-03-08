import { NextRequest, NextResponse } from "next/server";

const COLLECTOR_URL =
  process.env.COLLECTOR_URL || process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://collector:8001";
const API_KEY = process.env.MATEOBSERVE_API_KEY || "";

const ALLOWED_PATHS = new Set([
  "/services",
  "/metrics/overview",
  "/metrics/latency",
  "/metrics/errors",
  "/metrics/traffic",
  "/metrics/errors/recent",
  "/metrics/stream",
  "/health",
]);

function isAllowedPath(path: string): boolean {
  return ALLOWED_PATHS.has(path);
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const targetPath = "/" + path.join("/");

  if (!isAllowedPath(targetPath)) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const url = new URL(targetPath, COLLECTOR_URL);
  request.nextUrl.searchParams.forEach((value: string, key: string) => {
    url.searchParams.set(key, value);
  });

  const headers: Record<string, string> = {};
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }

  // SSE stream — pass through the response body directly
  if (targetPath === "/metrics/stream") {
    headers["Accept"] = "text/event-stream";
    try {
      const res = await fetch(url.toString(), {
        headers,
        cache: "no-store",
      });
      if (!res.ok || !res.body) {
        return NextResponse.json({ error: "Stream unavailable" }, { status: 502 });
      }
      return new Response(res.body, {
        status: 200,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    } catch {
      return NextResponse.json({ error: "Collector unreachable" }, { status: 502 });
    }
  }

  // Regular JSON endpoints
  headers["Content-Type"] = "application/json";
  try {
    const res = await fetch(url.toString(), {
      headers,
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json(
      { error: "Collector unreachable" },
      { status: 502 },
    );
  }
}
