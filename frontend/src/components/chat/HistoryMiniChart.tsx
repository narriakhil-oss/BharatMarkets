"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { HistorySummary } from "@/types/chat";
import { formatPrice, toNum } from "@/types/chat";

interface Props {
  history: HistorySummary;
}

export function HistoryMiniChart({ history }: Props) {
  const data = (history.series || []).map((p) => ({
    date: p.date.slice(5),
    close: toNum(p.close) ?? 0,
  }));
  const change = toNum(history.change_pct) ?? 0;
  const up = change >= 0;

  return (
    <div className="mt-3 rounded-lg border border-white/[0.08] bg-zinc-950/60 p-3">
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-xs font-medium text-zinc-200">
            {history.symbol} · {history.period}
          </p>
          <p className="text-[11px] text-muted-foreground">
            {formatPrice(history.start_price)} → {formatPrice(history.end_price)}
            <span className={up ? " text-emerald-400" : " text-rose-400"}>
              {" "}
              ({up ? "+" : ""}
              {change.toFixed(2)}%)
            </span>
          </p>
        </div>
        <p className="text-[10px] font-mono text-zinc-500">
          H {formatPrice(history.high)} · L {formatPrice(history.low)}
        </p>
      </div>
      {data.length > 1 && (
        <div className="h-28 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
              <XAxis dataKey="date" hide />
              <YAxis domain={["auto", "auto"]} hide />
              <Tooltip
                contentStyle={{
                  background: "#121624",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 8,
                  fontSize: 11,
                }}
                labelStyle={{ color: "#94a3b8" }}
                formatter={(v) => [formatPrice(Number(v)), "Close"]}
              />
              <Line
                type="monotone"
                dataKey="close"
                stroke={up ? "#00dc82" : "#ef4444"}
                strokeWidth={1.75}
                dot={false}
                isAnimationActive
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
