"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TrafficBucket } from "@/lib/api";

interface Props {
  data: TrafficBucket[];
}

export function TrafficChart({ data }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    time: new Date(d.bucket).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
  }));

  return (
    <div className="chart-panel fade-in">
      <h3>Requests Over Time</h3>
      {formatted.length === 0 ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          No traffic data yet
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={formatted}>
            <defs>
              <linearGradient id="trafficGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.5} />
                <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="var(--text-muted)"
              fontSize={11}
              fontFamily="JetBrains Mono"
              tickLine={false}
              axisLine={false}
              tickMargin={10}
            />
            <YAxis
              stroke="var(--text-muted)"
              fontSize={11}
              fontFamily="JetBrains Mono"
              tickLine={false}
              axisLine={false}
              tickMargin={10}
            />
            <Tooltip
              contentStyle={{
                background: "var(--bg-card)",
                backdropFilter: "blur(12px)",
                border: "1px solid var(--border)",
                borderRadius: "12px",
                fontFamily: "JetBrains Mono",
                fontSize: "12px",
                color: "var(--text-primary)",
                boxShadow: "0 8px 32px rgba(0, 0, 0, 0.2)",
              }}
            />
            <Area
              type="monotone"
              dataKey="requests"
              stroke="var(--accent)"
              strokeWidth={3}
              fill="url(#trafficGrad)"
              activeDot={{ r: 6, fill: "var(--accent)", stroke: "var(--bg-primary)", strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
