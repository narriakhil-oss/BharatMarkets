"use client";

import Link from "next/link";
import { StockQuote } from "@/types/market";
import { formatINR, formatVolume } from "@/lib/format";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

interface MoversTableProps {
  stocks: StockQuote[];
  type: "gainers" | "losers";
  title: string;
}

export function MoversTable({ stocks, type, title }: MoversTableProps) {
  const isGainers = type === "gainers";

  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          {title}
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${isGainers ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
            NIFTY 100
          </span>
        </h2>
        <span className="text-xs text-zinc-400">Top {stocks.length}</span>
      </div>

      {stocks.length === 0 ? (
        <div className="py-8 text-center text-sm text-zinc-500">No {type} data available</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                <th className="pb-3 pl-2 w-8">#</th>
                <th className="pb-3">Symbol</th>
                <th className="pb-3 hidden md:table-cell">Company</th>
                <th className="pb-3 text-right">LTP</th>
                <th className="pb-3 text-right">Change%</th>
                <th className="pb-3 text-right pr-2 hidden md:table-cell">Volume</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {stocks.map((stock, index) => {
                const isPos = stock.change_pct >= 0;
                return (
                  <tr key={stock.symbol} className="group hover:bg-zinc-800/40 transition-colors">
                    <td className="py-3 pl-2 text-xs font-mono text-zinc-500">{index + 1}</td>
                    <td className="py-3">
                      <Link href={`/stock/${stock.symbol}`} className="font-mono font-bold text-zinc-100 hover:text-emerald-400 transition-colors">
                        {stock.symbol.replace(".NS", "").replace(".BO", "")}
                      </Link>
                    </td>
                    <td className="py-3 text-zinc-400 max-w-[160px] truncate hidden md:table-cell text-xs">
                      <Link href={`/stock/${stock.symbol}`} className="hover:text-zinc-200">{stock.name}</Link>
                    </td>
                    <td className="py-3 text-right font-mono font-medium text-zinc-200">{formatINR(stock.ltp)}</td>
                    <td className="py-3 text-right">
                      <span className={`inline-flex items-center gap-0.5 rounded-md px-2 py-0.5 text-xs font-mono font-semibold ${isPos ? "bg-[#00dc82]/10 text-[#00dc82]" : "bg-[#ef4444]/10 text-[#ef4444]"}`}>
                        {isPos ? <ArrowUpRight className="h-3 w-3 stroke-[2.5]" /> : <ArrowDownRight className="h-3 w-3 stroke-[2.5]" />}
                        {isPos ? "+" : ""}{stock.change_pct.toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-3 pr-2 text-right font-mono text-xs text-zinc-400 hidden md:table-cell">
                      {stock.volume ? formatVolume(stock.volume) : "-"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
