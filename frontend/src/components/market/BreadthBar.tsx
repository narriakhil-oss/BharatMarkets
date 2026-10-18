"use client";

import { MarketBreadth } from "@/types/market";

export function BreadthBar({ data }: { data: MarketBreadth }) {
  const total = data.total > 0 ? data.total : data.advances + data.declines + data.unchanged || 1;
  const advPct = Math.max(0, (data.advances / total) * 100);
  const decPct = Math.max(0, (data.declines / total) * 100);
  const unchPct = Math.max(0, (data.unchanged / total) * 100);

  const adRatio =
    data.advance_decline_ratio !== null && data.advance_decline_ratio !== undefined
      ? data.advance_decline_ratio.toFixed(2)
      : data.declines > 0
      ? (data.advances / data.declines).toFixed(2)
      : "N/A";

  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-bold text-white">Market Breadth</h2>
        <div className="text-xs font-mono font-medium text-zinc-300 bg-zinc-800/70 px-2.5 py-1 rounded-md border border-zinc-700/50">
          A/D Ratio: <span className="text-white font-bold">{adRatio}</span>
        </div>
      </div>

      <div className="h-3 w-full rounded-full bg-zinc-800 overflow-hidden flex shadow-inner">
        <div className="bg-[#00dc82] transition-all duration-500" style={{ width: `${advPct}%` }} title={`Advances: ${data.advances}`} />
        <div className="bg-zinc-600 transition-all duration-500" style={{ width: `${unchPct}%` }} title={`Unchanged: ${data.unchanged}`} />
        <div className="bg-[#ef4444] transition-all duration-500" style={{ width: `${decPct}%` }} title={`Declines: ${data.declines}`} />
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between text-xs font-medium text-zinc-400 gap-2">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[#00dc82]" />
          <span className="font-semibold text-zinc-200">{data.advances}</span> Advances
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-zinc-500" />
          <span className="font-semibold text-zinc-200">{data.unchanged}</span> Unchanged
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[#ef4444]" />
          <span className="font-semibold text-zinc-200">{data.declines}</span> Declines
        </div>
      </div>
    </div>
  );
}
