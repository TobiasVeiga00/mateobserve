"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ErrorEntry } from "@/lib/api";

interface Props {
  data: ErrorEntry[];
}

export function ErrorChart({ data }: Props) {
  const formatted = data
    .filter((d) => d.error_count > 0)
    .sort((a, b) => b.error_rate - a.error_rate)
    .slice(0, 10)
    .map((d) => ({
      name: `${d.method} ${d.endpoint}`,
      error_rate: d.error_rate,
      errors: d.error_count,
    }));

  return (
    <div className="chart-panel fade-in">
      <h3>Error Rate by Endpoint</h3>
      {formatted.length === 0 ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          No errors — looking good! 🧉
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={formatted} layout="vertical">
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              stroke="var(--text-muted)"
              fontSize={11}
              fontFamily="JetBrains Mono"
              unit="%"
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="var(--text-muted)"
              fontSize={10}
              fontFamily="JetBrains Mono"
              width={150}
              tickLine={false}
              axisLine={false}
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
              formatter={(value: number) => [`${value}%`, "Error Rate"]}
              cursor={{ fill: "var(--bg-secondary)" }}
            />
            <Bar dataKey="error_rate" fill="var(--error)" radius={[0, 6, 6, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
