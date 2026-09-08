"use client";

import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SEVERITY_META, SEVERITY_ORDER } from "@/lib/severity";
import type { SeverityBreakdownEntry } from "@/lib/types";

export function SeverityChart({ data }: { data: SeverityBreakdownEntry[] }) {
  const chartData = SEVERITY_ORDER.map((s) => ({
    severity: s,
    count: data.find((d) => d.severity === s)?.count ?? 0,
  }));

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 28, bottom: 4, left: 4 }}
          barCategoryGap={14}
        >
          <XAxis type="number" hide domain={[0, "dataMax + 1"]} />
          <YAxis
            dataKey="severity"
            type="category"
            axisLine={false}
            tickLine={false}
            width={72}
            tick={{ fontSize: 12, fill: "var(--muted-foreground)", fontWeight: 600 }}
            tickFormatter={(s: string) => SEVERITY_META[s as keyof typeof SEVERITY_META]?.label ?? s}
          />
          <Tooltip
            cursor={{ fill: "rgba(128,128,128,0.12)" }}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--popover)",
              color: "var(--popover-foreground)",
            }}
            formatter={(value) => [`${value}건`, "이슈 수"]}
            labelFormatter={(label) => {
              const meta = SEVERITY_META[label as keyof typeof SEVERITY_META];
              return `${meta?.label ?? label} 위험도`;
            }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={22} isAnimationActive={false}>
            {chartData.map((entry) => (
              <Cell key={entry.severity} fill={SEVERITY_META[entry.severity].hex} />
            ))}
            <LabelList dataKey="count" position="right" style={{ fontSize: 12, fontWeight: 600, fill: "var(--foreground)" }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
