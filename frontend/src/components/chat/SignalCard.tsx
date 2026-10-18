"use client";

import { Badge } from "@/components/ui/badge";
import type { SignalResult } from "@/types/chat";
import { formatPrice, toNum } from "@/types/chat";
import { cn } from "@/lib/utils";

interface Props {
  signal: SignalResult;
}

export function SignalCard({ signal }: Props) {
  const variant =
    signal.signal === "Buy"
      ? "success"
      : signal.signal === "Sell"
      ? "danger"
      : "warning";

  const mape = toNum(signal.backtest?.mape_pct);
  const dirAcc = toNum(signal.backtest?.directional_accuracy_pct);

  return (
    <div className="mt-3 rounded-lg border border-white/[0.08] bg-zinc-950/60 p-3 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Badge variant={variant} className="text-xs px-2.5 py-0.5">
            {signal.signal}
          </Badge>
          <span className="text-xs font-mono text-zinc-300">
            Score {signal.score >= 0 ? "+" : ""}
            {signal.score}
          </span>
          <span className="text-[11px] text-muted-foreground">{signal.symbol}</span>
        </div>
        {(mape !== null || dirAcc !== null) && (
          <Badge variant="phase" className="text-[10px] font-normal">
            Backtest
            {mape !== null && ` MAPE ${mape.toFixed(1)}%`}
            {dirAcc !== null && ` · Dir ${dirAcc.toFixed(0)}%`}
          </Badge>
        )}
      </div>

      {signal.ltp != null && (
        <p className="text-[11px] text-muted-foreground">
          LTP <span className="font-mono text-zinc-200">{formatPrice(signal.ltp)}</span>
          {signal.support != null && (
            <>
              {" "}
              · Support <span className="font-mono">{formatPrice(signal.support)}</span>
            </>
          )}
          {signal.resistance != null && (
            <>
              {" "}
              · Resistance <span className="font-mono">{formatPrice(signal.resistance)}</span>
            </>
          )}
        </p>
      )}

      <ul className="space-y-1">
        {signal.factors.map((f) => (
          <li
            key={f.name}
            className="flex items-start gap-2 text-[11px] text-zinc-400"
          >
            <span
              className={cn(
                "mt-0.5 inline-flex h-4 min-w-6 items-center justify-center rounded font-mono text-[10px]",
                f.score > 0 && "bg-emerald-500/15 text-emerald-400",
                f.score < 0 && "bg-rose-500/15 text-rose-400",
                f.score === 0 && "bg-zinc-800 text-zinc-500"
              )}
            >
              {f.score > 0 ? "+1" : f.score < 0 ? "−1" : "0"}
            </span>
            <span>
              <span className="text-zinc-300">{f.name.replace(/_/g, " ")}</span>
              {" — "}
              {f.detail}
            </span>
          </li>
        ))}
      </ul>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 border-t border-white/[0.06]">
        {signal.entry_zone && (
          <div className="text-[11px]">
            <p className="text-zinc-500 mb-0.5">Entry zone</p>
            <p className="font-mono text-zinc-200">
              {formatPrice(signal.entry_zone.low)} – {formatPrice(signal.entry_zone.high)}
            </p>
          </div>
        )}
        {signal.stop_loss && (
          <div className="text-[11px]">
            <p className="text-zinc-500 mb-0.5">Stop-loss</p>
            <p className="font-mono text-rose-300/90">
              {formatPrice(signal.stop_loss.low)} – {formatPrice(signal.stop_loss.high)}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
