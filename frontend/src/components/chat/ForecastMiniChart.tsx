"use client";

import {
  Area,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ForecastResult } from "@/types/chat";
import { formatPrice, toNum } from "@/types/chat";

interface Props {
  forecast: ForecastResult;
}

export function ForecastMiniChart({ forecast }: Props) {
  const hist = (forecast.history_tail || []).map((p) => ({
    date: p.date.slice(5),
    past: toNum(p.close),
    predicted: null as number | null,
    lowerBase: null as number | null,
    band: null as number | null,
  }));

  const fc = (forecast.forecast || []).map((p) => {
    const lo = toNum(p.lower) ?? 0;
    const hi = toNum(p.upper) ?? 0;
    return {
      date: p.date.slice(5),
      past: null as number | null,
      predicted: toNum(p.predicted),
      lowerBase: lo,
      band: hi - lo,
    };
  });

  const data = [...hist, ...fc];
  const change = toNum(forecast.forecast_change_pct);
  const mape = toNum(forecast.backtest?.mape_pct);
  const dirAcc = toNum(forecast.backtest?.directional_accuracy_pct);

  return (
    <div className="mt-3 rounded-lg border border-white/[0.08] bg-zinc-950/60 p-3">
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-xs font-medium text-zinc-200">
            {forecast.symbol} · {forecast.horizon_days}d forecast
          </p>
          <p className="text-[11px] text-muted-foreground">
            Last {formatPrice(forecast.last_close)}
            {change !== null && (
              <span className={change >= 0 ? " text-emerald-400" : " text-rose-400"}>
                {" "}
                → {change >= 0 ? "+" : ""}
                {change.toFixed(2)}% (mid)
              </span>
            )}
          </p>
        </div>
        <p className="text-[10px] text-zinc-500">
          {mape !== null && `MAPE ${mape.toFixed(1)}%`}
          {dirAcc !== null && ` · Dir ${dirAcc.toFixed(0)}%`}
        </p>
      </div>
      <div className="h-32 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <XAxis dataKey="date" hide />
            <YAxis domain={["auto", "auto"]} hide />
            <Tooltip
              contentStyle={{
                background: "#121624",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 8,
                fontSize: 11,
              }}
              formatter={(v, name) => {
                const label =
                  String(name) === "past"
                    ? "Past"
                    : String(name) === "predicted"
                    ? "Forecast"
                    : String(name);
                return [formatPrice(Number(v)), label];
              }}
            />
            <Area
              type="monotone"
              dataKey="lowerBase"
              stackId="band"
              stroke="none"
              fill="transparent"
              isAnimationActive={false}
              connectNulls={false}
            />
            <Area
              type="monotone"
              dataKey="band"
              stackId="band"
              stroke="none"
              fill="#00dc82"
              fillOpacity={0.18}
              isAnimationActive
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="past"
              stroke="#94a3b8"
              strokeWidth={1.5}
              dot={false}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="#00dc82"
              strokeWidth={1.75}
              strokeDasharray="4 3"
              dot={false}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
