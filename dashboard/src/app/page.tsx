"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  api,
  Overview,
  Service,
  LatencyEntry,
  ErrorEntry,
  TrafficBucket,
  RecentError,
} from "@/lib/api";
import { StatCards } from "@/components/StatCards";
import { TrafficChart } from "@/components/TrafficChart";
import { ErrorChart } from "@/components/ErrorChart";
import { LatencyTable } from "@/components/LatencyTable";
import { RecentErrors } from "@/components/RecentErrors";

const PROXY_BASE = "/api/collector";
const POLL_INTERVAL = 10_000; // fallback polling interval (ms)

type ConnectionStatus = "connecting" | "live" | "reconnecting" | "offline";

export default function DashboardPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [latency, setLatency] = useState<LatencyEntry[]>([]);
  const [errors, setErrors] = useState<ErrorEntry[]>([]);
  const [traffic, setTraffic] = useState<TrafficBucket[]>([]);
  const [recentErrors, setRecentErrors] = useState<RecentError[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connStatus, setConnStatus] = useState<ConnectionStatus>("connecting");
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Apply a full data snapshot from SSE or fetch
  const applySnapshot = useCallback(
    (data: {
      services: Service[];
      overview: Overview;
      latency: LatencyEntry[];
      errors: ErrorEntry[];
      traffic: TrafficBucket[];
      recent_errors: RecentError[];
    }) => {
      setServices(data.services);
      setOverview(data.overview);
      setLatency(data.latency);
      setErrors(data.errors);
      setTraffic(data.traffic);
      setRecentErrors(data.recent_errors);
      setError(null);
      setLoading(false);
      setLastUpdate(new Date());
    },
    [],
  );

  // Fallback: full fetch via REST
  const fetchAll = useCallback(async () => {
    try {
      const opts = { service: selectedService, minutes: 60 };
      const [svc, ov, lat, err, trf, recErr] = await Promise.all([
        api.services(),
        api.overview(opts),
        api.latency(opts),
        api.errors(opts),
        api.traffic(opts),
        api.recentErrors({ ...opts, limit: 50 }),
      ]);
      applySnapshot({
        services: svc,
        overview: ov,
        latency: lat,
        errors: err,
        traffic: trf,
        recent_errors: recErr,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch data");
      setLoading(false);
    }
  }, [selectedService, applySnapshot]);

  // SSE connection with auto-reconnect
  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedService) params.set("service", selectedService);
    params.set("minutes", "60");
    const qs = params.toString();
    const url = `${PROXY_BASE}/metrics/stream${qs ? `?${qs}` : ""}`;

    let retryCount = 0;

    function connect() {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      setConnStatus("connecting");
      const es = new EventSource(url);
      eventSourceRef.current = es;

      es.onopen = () => {
        setConnStatus("live");
        retryCount = 0;
      };

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.error) return;
          applySnapshot(data);
          setConnStatus("live");
        } catch {
          // ignore malformed events
        }
      };

      es.onerror = () => {
        es.close();
        setConnStatus("reconnecting");

        // Exponential backoff: 1s, 2s, 4s, 8s, max 15s
        const delay = Math.min(1000 * Math.pow(2, retryCount), 15000);
        retryCount++;

        if (retryCount > 5) {
          setConnStatus("offline");
          return;
        }

        reconnectTimer.current = setTimeout(connect, delay);
      };
    }

    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
    };
  }, [selectedService, applySnapshot]);

  // Fallback polling when SSE is offline
  useEffect(() => {
    if (connStatus !== "offline") return;
    fetchAll();
    const id = setInterval(fetchAll, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [connStatus, fetchAll]);

  if (loading) {
    return (
      <div className="app">
        <div className="loading-screen">
          <div className="loading-mate">🧉</div>
          <p>Brewing your metrics...</p>
        </div>
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="app">
        <Header
          services={services}
          selected={selectedService}
          onSelect={setSelectedService}
          connStatus={connStatus}
          lastUpdate={lastUpdate}
        />
        <main className="main">
          <div className="empty-state">
            <div className="icon">🧉</div>
            <h2>Collector Unreachable</h2>
            <p>
              Make sure the MateObserve collector is running. Start it with:
            </p>
            <code>docker compose up</code>
          </div>
        </main>
      </div>
    );
  }

  const hasData = overview && overview.total_requests > 0;

  return (
    <div className="app">
      <Header
        services={services}
        selected={selectedService}
        onSelect={setSelectedService}
        connStatus={connStatus}
        lastUpdate={lastUpdate}
      />

      <main className="main">
        {!hasData ? (
          <div className="empty-state">
            <div className="icon">🧉</div>
            <h2>Waiting for metrics...</h2>
            <p>
              Add the MateObserve middleware to your API and start making
              requests. Data will appear here automatically.
            </p>
            <code>
              from mateobserve import ObserveMiddleware
              <br />
              app.add_middleware(ObserveMiddleware)
            </code>
          </div>
        ) : (
          <>
            <StatCards data={overview} />
            <div className="charts-grid">
              <TrafficChart data={traffic} />
              <ErrorChart data={errors} />
            </div>
            <LatencyTable data={latency} />
            <div style={{ marginTop: "1.5rem" }}>
              <RecentErrors data={recentErrors} />
            </div>
          </>
        )}
      </main>

      <footer className="footer">
        MateObserve — Observability for APIs in 30 seconds 🧉
      </footer>
    </div>
  );
}

function Header({
  services,
  selected,
  onSelect,
  connStatus,
  lastUpdate,
}: {
  services: Service[];
  selected: string | null;
  onSelect: (s: string | null) => void;
  connStatus: ConnectionStatus;
  lastUpdate: Date | null;
}) {
  const statusLabel: Record<ConnectionStatus, string> = {
    connecting: "Connecting",
    live: "Live",
    reconnecting: "Reconnecting",
    offline: "Polling",
  };

  return (
    <header className="header">
      <div className="logo">
        <span className="logo-icon">🧉</span>
        <h1>MateObserve</h1>
      </div>
      <div className="header-meta">
        <span className={`conn-status conn-${connStatus}`}>
          <span className="conn-dot" />
          {statusLabel[connStatus]}
          {lastUpdate && connStatus === "live" && (
            <span className="conn-time">
              {lastUpdate.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
          )}
        </span>
        {services.length > 0 && (
          <select
            className="service-select"
            value={selected || ""}
            onChange={(e) => onSelect(e.target.value || null)}
          >
            <option value="">All services</option>
            {services.map((s) => (
              <option key={s.service} value={s.service}>
                {s.service}
              </option>
            ))}
          </select>
        )}
      </div>
    </header>
  );
}
