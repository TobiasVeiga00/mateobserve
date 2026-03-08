"use client";

import { Overview } from "@/lib/api";

interface Props {
  data: Overview | null;
}

export function StatCards({ data }: Props) {
  if (!data) return null;

  const cards: Array<{ label: string; value: string; sub: string; variant: "good" | "warning" | "error" }> = [
    {
      label: "Requests / min",
      value: data.requests_per_minute.toFixed(1),
      sub: `${data.total_requests.toLocaleString()} total`,
      variant: "good",
    },
    {
      label: "Avg Latency",
      value: `${data.avg_latency_ms.toFixed(0)}ms`,
      sub: `max ${data.max_latency_ms.toFixed(0)}ms`,
      variant: data.avg_latency_ms > 500 ? "warning" : "good",
    },
    {
      label: "Error Rate",
      value: `${data.error_rate.toFixed(1)}%`,
      sub: `${data.error_count} errors`,
      variant: data.error_rate > 5 ? "error" : data.error_rate > 1 ? "warning" : "good",
    },
    {
      label: "Total Errors",
      value: data.error_count.toLocaleString(),
      sub: "in time window",
      variant: data.error_count > 0 ? "error" : "good",
    },
  ];

  return (
    <div className="stats-grid">
      {cards.map((card, i) => (
        <div
          key={card.label}
          className={`stat-card fade-in fade-in-delay-${i + 1}`}
        >
          <div className="stat-label">{card.label}</div>
          <div className={`stat-value ${card.variant}`}>{card.value}</div>
          <div className="stat-sub">{card.sub}</div>
        </div>
      ))}
    </div>
  );
}
