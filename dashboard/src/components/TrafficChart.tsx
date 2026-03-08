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
                <stop offset="5%" stopColor="#5a9670" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#5a9670" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#2a3a2e" strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              stroke="#5e6b58"
              fontSize={11}
              fontFamily="JetBrains Mono"
            />
            <YAxis
              stroke="#5e6b58"
              fontSize={11}
              fontFamily="JetBrains Mono"
            />
            <Tooltip
              contentStyle={{
                background: "#1c251f",
                border: "1px solid #2a3a2e",
                borderRadius: "8px",
                fontFamily: "JetBrains Mono",
                fontSize: "12px",
                color: "#e8e2d6",
              }}
            />
            <Area
              type="monotone"
              dataKey="requests"
              stroke="#5a9670"
              strokeWidth={2}
              fill="url(#trafficGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
