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
            <CartesianGrid stroke="#2a3a2e" strokeDasharray="3 3" />
            <XAxis
              type="number"
              stroke="#5e6b58"
              fontSize={11}
              fontFamily="JetBrains Mono"
              unit="%"
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="#5e6b58"
              fontSize={10}
              fontFamily="JetBrains Mono"
              width={150}
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
              formatter={(value: number) => [`${value}%`, "Error Rate"]}
            />
            <Bar dataKey="error_rate" fill="#e05555" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
