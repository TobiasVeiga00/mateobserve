"use client";

import { LatencyEntry } from "@/lib/api";

interface Props {
  data: LatencyEntry[];
}

export function LatencyTable({ data }: Props) {
  const sorted = [...data].sort((a, b) => b.p95_latency_ms - a.p95_latency_ms);

  return (
    <div className="table-panel fade-in">
      <h3>Endpoint Latency</h3>
      {sorted.length === 0 ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          No latency data yet
        </p>
      ) : (
        <table className="endpoints-table">
          <thead>
            <tr>
              <th>Method</th>
              <th>Endpoint</th>
              <th>Reqs</th>
              <th>Avg</th>
              <th>P50</th>
              <th>P95</th>
              <th>P99</th>
              <th>Max</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => (
              <tr key={`${row.method}-${row.endpoint}`}>
                <td>
                  <span className={`method-badge method-${row.method}`}>
                    {row.method}
                  </span>
                </td>
                <td className="mono">{row.endpoint}</td>
                <td className="mono">{row.request_count}</td>
                <td className="mono">{row.avg_latency_ms.toFixed(0)}ms</td>
                <td className="mono">{row.p50_latency_ms.toFixed(0)}ms</td>
                <td className="mono">{row.p95_latency_ms.toFixed(0)}ms</td>
                <td className="mono">{row.p99_latency_ms.toFixed(0)}ms</td>
                <td className="mono">{row.max_latency_ms.toFixed(0)}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
