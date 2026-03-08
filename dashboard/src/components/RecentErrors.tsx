"use client";

import { RecentError } from "@/lib/api";

interface Props {
  data: RecentError[];
}

export function RecentErrors({ data }: Props) {
  return (
    <div className="table-panel fade-in">
      <h3>Recent Errors</h3>
      {data.length === 0 ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          No errors recorded — all clear! 🧉
        </p>
      ) : (
        <div className="error-log">
          {data.map((err, i) => (
            <div key={`${err.timestamp}-${i}`} className="error-row">
              <div className="error-row-header">
                <span className={`status-badge status-${Math.floor(err.status_code / 100)}xx`}>
                  {err.status_code}
                </span>
                <span className={`method-badge method-${err.method}`}>
                  {err.method}
                </span>
                <span className="mono error-endpoint">{err.endpoint}</span>
                <span className="error-time">
                  {new Date(err.timestamp).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })}
                </span>
              </div>
              <div className="error-row-details">
                {err.error && (
                  <span className="error-type">{err.error}</span>
                )}
                <span className="error-latency">{err.latency_ms.toFixed(1)}ms</span>
                <span className="error-service">{err.service}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
