"use client";

import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { IndexData } from "@/types/market";
import { formatINR } from "@/lib/format";

export function IndexCard({ data }: { data: IndexData }) {
  const isPositive = data.change >= 0;
  const changeColor = isPositive ? "text-[#00dc82]" : "text-[#ef4444]";
  const borderColor = isPositive ? "border-l-[#00dc82]" : "border-l-[#ef4444]";
  const badgeBg = isPositive ? "bg-[#00dc82]/10 text-[#00dc82]" : "bg-[#ef4444]/10 text-[#ef4444]";

  const dayHigh = data.day_high ?? null;
  const dayLow = data.day_low ?? null;
  const hasRange = dayHigh !== null && dayLow !== null && dayHigh > dayLow;

  let rangePct = 50;
  if (hasRange) {
    const clamped = Math.min(dayHigh!, Math.max(dayLow!, data.ltp));
    rangePct = Math.round(((clamped - dayLow!) / (dayHigh! - dayLow!)) * 100);
  }

  return (
    <div className={`rounded-xl border border-zinc-800/80 border-l-[3px] ${borderColor} bg-zinc-900/60 p-4 backdrop-blur-md hover:border-zinc-700/80 transition-all duration-200`}>
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-zinc-100 text-sm tracking-wide">{data.display_name}</h3>
        <span className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-semibold ${badgeBg}`}>
          {isPositive ? <ArrowUpRight className="h-3.5 w-3.5 stroke-[2.5]" /> : <ArrowDownRight className="h-3.5 w-3.5 stroke-[2.5]" />}
          {Math.abs(data.change_pct).toFixed(2)}%
        </span>
      </div>

      <div className="mt-2.5">
        <div className="text-2xl font-bold tracking-tight text-white font-mono">{formatINR(data.ltp)}</div>
        <div className={`mt-0.5 text-xs font-medium ${changeColor} flex items-center gap-1 font-mono`}>
          <span>{isPositive ? "+" : ""}{data.change.toFixed(2)}</span>
          <span className="text-zinc-500">({isPositive ? "+" : ""}{data.change_pct.toFixed(2)}%)</span>
        </div>
      </div>

      {hasRange && (
        <div className="mt-3.5 pt-3 border-t border-zinc-800/60">
          <div className="flex items-center justify-between text-[11px] text-zinc-400 font-mono mb-1">
            <span>L: {formatINR(dayLow!)}</span>
            <span>H: {formatINR(dayHigh!)}</span>
          </div>
          <div className="relative h-1.5 w-full rounded-full bg-zinc-800 overflow-hidden">
            <div className={`h-full rounded-full ${isPositive ? "bg-[#00dc82]" : "bg-[#ef4444]"}`} style={{ width: `${rangePct}%` }} />
          </div>
        </div>
      )}
    </div>
  );
}
