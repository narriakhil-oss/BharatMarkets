import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowLeft,
  BarChart2,
  PieChart,
  Activity,
  Layers,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { TIMEFRAMES } from "@/lib/constants";

interface PageProps {
  params: Promise<{
    symbol: string;
  }>;
}

// Next.js 15 Dynamic Metadata with awaited params Promise
export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { symbol } = await params;
  const decodedSymbol = decodeURIComponent(symbol).toUpperCase();

  return {
    title: `${decodedSymbol} Technical Analysis & Charts — BharatMarkets`,
    description: `Detailed charts, RSI, MACD, fundamentals, and moving averages for ${decodedSymbol} on NSE/BSE.`,
  };
}

// Server Component: params is a Promise in Next.js 15
export default async function StockDetailPage({ params }: PageProps) {
  const { symbol } = await params;
  const decodedSymbol = decodeURIComponent(symbol).toUpperCase();
  const cleanTicker = decodedSymbol.replace(".NS", "").replace(".BO", "");
  const exchange = decodedSymbol.includes(".BO") ? "BSE" : "NSE";

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center gap-2">
        <Button
          asChild
          variant="ghost"
          size="sm"
          className="text-zinc-400 hover:text-white -ml-2 text-xs"
        >
          <Link href="/dashboard" className="flex items-center gap-1">
            <ArrowLeft className="size-4" />
            Back to Dashboard
          </Link>
        </Button>
      </div>

      {/* Stock Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl border border-white/[0.08] bg-card/60 backdrop-blur-xl">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white font-mono">
              {cleanTicker}
            </h1>
            <Badge variant="outline" className="border-cyan-500/30 text-cyan-400">
              {exchange}
            </Badge>
            <Badge variant="warning" className="text-[11px]">
              Delayed ~15m
            </Badge>
          </div>
          <p className="text-sm text-zinc-400">
            {decodedSymbol} · Real-time Technical & Educational Overview
          </p>
        </div>

        {/* Price & Change Block Placeholder */}
        <div className="flex flex-col md:items-end">
          <div className="text-3xl font-extrabold font-mono text-white tracking-tight">
            ₹2,845.60
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-emerald-400 font-mono text-sm font-semibold flex items-center">
              <TrendingUp className="size-4 mr-0.5 inline" />
              +₹42.30 (+1.51%)
            </span>
            <span className="text-xs text-zinc-500">Today</span>
          </div>
        </div>
      </div>

      {/* ─── SECTION 1: Candlestick Chart Placeholder ─────────────────── */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart2 className="size-4 text-emerald-400" />
            <h2 className="text-lg font-semibold text-white">
              TradingView Lightweight Chart
            </h2>
          </div>
          <Badge variant="phase">Coming in Phase 3</Badge>
        </div>

        <Card className="border-white/[0.08] bg-card/40">
          <CardHeader className="pb-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base text-zinc-200">
                  Interactive Candlestick & Volume
                </CardTitle>
                <CardDescription className="text-xs">
                  Historical OHLCV data with EMA 20/50/200 overlays
                </CardDescription>
              </div>

              {/* Timeframe Selector Pills */}
              <div className="flex items-center gap-1 p-1 rounded-lg bg-zinc-900/80 border border-white/[0.06]">
                {TIMEFRAMES.slice(0, 6).map((tf, index) => (
                  <button
                    key={tf.value}
                    type="button"
                    disabled
                    className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                      index === 0
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Chart Skeleton */}
            <LoadingSkeleton variant="chart" />
          </CardContent>
        </Card>
      </section>

      {/* ─── SECTION 2: Technical Analysis & Fundamentals Grid ────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Technical Indicators Card */}
        <Card className="border-white/[0.08] bg-card/40">
          <CardHeader className="pb-3 border-b border-white/[0.06]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="size-4 text-cyan-400" />
                <CardTitle className="text-base text-white">
                  Technical Indicators & Trend
                </CardTitle>
              </div>
              <Badge variant="phase">Coming in Phase 3</Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { label: "RSI (14)", val: "58.4", badge: "NEUTRAL", color: "text-amber-400" },
                { label: "MACD Line", val: "+14.2", badge: "BULLISH", color: "text-emerald-400" },
                { label: "20 EMA", val: "₹2,810.00", badge: "ABOVE", color: "text-emerald-400" },
                { label: "50 SMA", val: "₹2,740.50", badge: "ABOVE", color: "text-emerald-400" },
                { label: "200 SMA", val: "₹2,520.10", badge: "SUPPORT", color: "text-emerald-400" },
                { label: "Bollinger Upper", val: "₹2,890.00", badge: "RESISTANCE", color: "text-rose-400" },
              ].map((item) => (
                <div
                  key={item.label}
                  className="p-3 rounded-lg border border-white/[0.04] bg-white/[0.02]"
                >
                  <div className="text-xs text-zinc-400">{item.label}</div>
                  <div className="font-mono text-sm font-semibold text-white mt-1">
                    {item.val}
                  </div>
                  <div className={`text-[10px] font-mono mt-0.5 ${item.color}`}>
                    {item.badge}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-3.5 rounded-xl border border-white/[0.06] bg-zinc-900/50 space-y-1.5">
              <div className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Sparkles className="size-3.5 text-cyan-400" />
                Algorithmic Trend Summary
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Trading above all key moving averages with mild bullish divergence on MACD. Strong support near ₹2,740 level.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Fundamental Metrics Card */}
        <Card className="border-white/[0.08] bg-card/40">
          <CardHeader className="pb-3 border-b border-white/[0.06]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <PieChart className="size-4 text-indigo-400" />
                <CardTitle className="text-base text-white">
                  Key Fundamentals & Ratios
                </CardTitle>
              </div>
              <Badge variant="phase">Coming in Phase 3</Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Market Cap", val: "₹19.25 Lakh Cr" },
                { label: "P/E Ratio (TTM)", val: "26.4" },
                { label: "52-Week High", val: "₹3,024.90" },
                { label: "52-Week Low", val: "₹2,220.30" },
                { label: "Sector P/E", val: "28.1" },
                { label: "Dividend Yield", val: "0.85%" },
                { label: "Average Volume (3M)", val: "8.4M" },
                { label: "Beta (1Y)", val: "0.92" },
              ].map((fund) => (
                <div
                  key={fund.label}
                  className="flex items-center justify-between p-2.5 rounded-lg border border-white/[0.04] bg-white/[0.02]"
                >
                  <span className="text-xs text-zinc-400">{fund.label}</span>
                  <span className="font-mono text-xs font-semibold text-zinc-200">
                    {fund.val}
                  </span>
                </div>
              ))}
            </div>

            <div className="p-3.5 rounded-xl border border-white/[0.06] bg-zinc-900/50 flex items-center justify-between text-xs text-zinc-400">
              <div className="flex items-center gap-2">
                <Layers className="size-4 text-emerald-400" />
                <span>Sector: <strong>Energy & Petrochemicals</strong></span>
              </div>
              <Badge variant="outline" className="text-[10px]">Large Cap</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
