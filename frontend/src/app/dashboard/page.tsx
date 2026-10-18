"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { ArrowUpRight, ArrowDownRight, RefreshCw, Clock, ShieldAlert } from "lucide-react";

/* ─── Types ─── */
interface IndexData {
  symbol: string; display_name: string; exchange: string;
  ltp: number; change: number; change_pct: number;
  day_high: number | null; day_low: number | null;
}
interface StockQuote {
  symbol: string; name: string; ltp: number;
  change: number; change_pct: number; volume: number;
}
interface DashboardData {
  indices: IndexData[];
  gainers: StockQuote[];
  losers: StockQuote[];
  fetchedAt: Date;
}

/* ─── Formatters ─── */
function formatINR(v: number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(v);
}
function formatVol(v: number) {
  if (v >= 1e7) return `${(v / 1e7).toFixed(1)}Cr`;
  if (v >= 1e5) return `${(v / 1e5).toFixed(1)}L`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return String(v);
}
function formatTime(d: Date) {
  return new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", hour12: true }).format(d) + " IST";
}

/* ─── Index Card ─── */
function IndexCard({ d }: { d: IndexData }) {
  const pos = d.change >= 0;
  const border = pos ? "border-l-emerald-400" : "border-l-red-400";
  const txt = pos ? "text-emerald-400" : "text-red-400";
  const bg = pos ? "bg-emerald-400/10" : "bg-red-400/10";
  const bar = d.day_high && d.day_low && d.day_high > d.day_low
    ? Math.round(((d.ltp - d.day_low) / (d.day_high - d.day_low)) * 100) : 50;

  return (
    <div className={`rounded-xl border border-zinc-800 border-l-[3px] ${border} bg-zinc-900/70 p-4`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-zinc-200">{d.display_name}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${bg} ${txt} flex items-center gap-0.5`}>
          {pos ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
          {Math.abs(d.change_pct).toFixed(2)}%
        </span>
      </div>
      <div className="text-2xl font-bold font-mono text-white">{formatINR(d.ltp)}</div>
      <div className={`text-xs font-mono ${txt} mt-0.5`}>{pos ? "+" : ""}{d.change.toFixed(2)}</div>
      {d.day_high && d.day_low && (
        <div className="mt-3 pt-3 border-t border-zinc-800">
          <div className="flex justify-between text-[11px] text-zinc-500 font-mono mb-1">
            <span>L {formatINR(d.day_low)}</span>
            <span>H {formatINR(d.day_high)}</span>
          </div>
          <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
            <div className={`h-full rounded-full ${pos ? "bg-emerald-400" : "bg-red-400"}`} style={{ width: `${bar}%` }} />
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Movers Table ─── */
function MoversTable({ stocks, type }: { stocks: StockQuote[]; type: "gainers" | "losers" }) {
  const green = type === "gainers";
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-5">
      <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
        {green ? "🟢 Top Gainers" : "🔴 Top Losers"}
        <span className={`text-[11px] px-2 py-0.5 rounded-full ${green ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>NIFTY 50</span>
      </h2>
      {stocks.length === 0 ? (
        <p className="text-zinc-500 text-sm py-4 text-center">No data</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 text-[11px] text-zinc-500 uppercase tracking-wider">
              <th className="pb-2 text-left pl-1">#</th>
              <th className="pb-2 text-left">Symbol</th>
              <th className="pb-2 text-right">LTP</th>
              <th className="pb-2 text-right">Chg%</th>
              <th className="pb-2 text-right pr-1 hidden sm:table-cell">Volume</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {stocks.map((s, i) => {
              const pos = s.change_pct >= 0;
              return (
                <tr key={s.symbol} className="hover:bg-zinc-800/40 transition-colors">
                  <td className="py-2.5 pl-1 text-zinc-500 text-xs font-mono">{i + 1}</td>
                  <td className="py-2.5">
                    <Link href={`/stock/${s.symbol}`} className="font-mono font-bold text-zinc-100 hover:text-emerald-400 transition-colors">
                      {s.symbol.replace(".NS","").replace(".BO","")}
                    </Link>
                    <div className="text-[11px] text-zinc-500 truncate max-w-[120px]">{s.name}</div>
                  </td>
                  <td className="py-2.5 text-right font-mono text-zinc-200">{formatINR(s.ltp)}</td>
                  <td className="py-2.5 text-right">
                    <span className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${pos ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>
                      {pos ? "+" : ""}{s.change_pct.toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-mono text-xs text-zinc-400 pr-1 hidden sm:table-cell">{formatVol(s.volume)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

/* ─── Skeleton ─── */
function Skeleton({ className = "" }) {
  return <div className={`animate-pulse bg-zinc-800/70 rounded ${className}`} />;
}
function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-36 rounded-xl" />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Skeleton className="h-80 rounded-xl" />
        <Skeleton className="h-80 rounded-xl" />
      </div>
    </div>
  );
}

/* ─── Dashboard Page ─── */
export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [idxRes, movRes] = await Promise.all([
        fetch("/api/market/indices"),
        fetch("/api/market/movers"),
      ]);
      if (!idxRes.ok || !movRes.ok) throw new Error("Failed to fetch market data");
      const indices = await idxRes.json();
      const { gainers, losers } = await movRes.json();
      setData({ indices, gainers, losers, fetchedAt: new Date() });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  return (
    <div className="min-h-screen text-zinc-100 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Market Dashboard</h1>
          <p className="text-xs text-zinc-400 mt-0.5">NSE &amp; BSE — data delayed ~15 minutes via Yahoo Finance</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full font-medium">⏱ Delayed ~15m</span>
          {data?.fetchedAt && (
            <span className="text-xs text-zinc-400 flex items-center gap-1">
              <Clock className="h-3 w-3" /> {formatTime(data.fetchedAt)}
            </span>
          )}
          <button
            onClick={fetchAll}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs border border-zinc-700 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg transition-all disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </header>

      {/* Market Closed Banner (weekends / after hours) */}
      <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-2.5 text-xs text-amber-300 flex items-center gap-2">
        <span>📅 Market closed? Prices shown are from the last trading session.</span>
        <span className="ml-auto text-amber-400/60 hidden sm:block">NSE: Mon–Fri 9:15 AM – 3:30 PM IST</span>
      </div>

      {loading && !data && <LoadingState />}

      {error && !data && (
        <div className="rounded-xl border border-red-500/20 bg-red-950/20 p-8 text-center">
          <p className="text-red-400 font-medium mb-3">⚠️ {error}</p>
          <button onClick={fetchAll} className="text-sm border border-red-500/30 text-red-300 hover:bg-red-500/10 px-4 py-2 rounded-lg transition-all cursor-pointer">
            Retry
          </button>
        </div>
      )}

      {data && (
        <>
          {/* Index Cards */}
          <section>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {data.indices.map((idx) => <IndexCard key={idx.symbol} d={idx} />)}
            </div>
          </section>

          {/* Gainers / Losers */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MoversTable stocks={data.gainers} type="gainers" />
            <MoversTable stocks={data.losers} type="losers" />
          </section>
        </>
      )}

      {/* Disclaimer */}
      <footer className="pt-4 border-t border-zinc-900 text-center">
        <p className="text-xs text-zinc-600 flex items-center justify-center gap-2">
          <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
          Educational project only. Not SEBI-registered. Not investment advice. Data may be delayed.
        </p>
      </footer>
    </div>
  );
}
