import Link from "next/link";
import {
  TrendingUp,
  ArrowRight,
  BarChart3,
  Compass,
  ShieldCheck,
  Zap,
  Clock,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DISCLAIMER_TEXT } from "@/lib/constants";

export default function HomePage() {
  return (
    <div className="relative min-h-[calc(100vh-4rem)] flex flex-col justify-between overflow-hidden">
      {/* Dynamic Background Glow & Grid */}
      <div className="absolute inset-0 terminal-grid pointer-events-none opacity-40" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[350px] bg-gradient-to-tr from-emerald-500/15 via-cyan-500/10 to-indigo-500/15 rounded-full blur-[110px] pointer-events-none" />
      <div className="absolute top-2/3 right-10 w-[300px] h-[300px] bg-emerald-500/10 rounded-full blur-[90px] pointer-events-none" />

      {/* Main Hero Container */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-20 flex-1 flex flex-col items-center justify-center text-center">
        {/* Top Tag Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 text-xs font-medium mb-8 backdrop-blur-md shadow-[0_0_20px_rgba(16,185,129,0.15)] animate-in fade-in slide-in-from-top-4 duration-700">
          <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Educational Stock Terminal 🇮🇳</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight max-w-4xl leading-[1.1] mb-6">
          <span className="bg-gradient-to-b from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
            Master the Indian Market with
          </span>{" "}
          <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_35px_rgba(52,211,153,0.35)]">
            BharatMarkets
          </span>
        </h1>

        {/* Tagline */}
        <p className="text-lg sm:text-xl md:text-2xl text-zinc-300 max-w-2xl font-light mb-10 leading-relaxed">
          Track, learn, and master NSE & BSE benchmarks, top gainers, technical
          indicators, and sector rotations — data delayed ~15 minutes.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 mb-16 w-full sm:w-auto">
          <Button
            asChild
            size="lg"
            className="w-full sm:w-auto bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-zinc-950 font-bold px-8 py-6 rounded-xl text-base shadow-[0_0_30px_rgba(16,185,129,0.4)] transition-all transform hover:-translate-y-0.5 active:translate-y-0"
          >
            <Link href="/dashboard" className="flex items-center justify-center gap-2">
              Launch Dashboard
              <ArrowRight className="size-5 transition-transform group-hover:translate-x-1" />
            </Link>
          </Button>

          <Button
            asChild
            variant="outline"
            size="lg"
            className="w-full sm:w-auto border-white/10 hover:border-emerald-500/50 bg-white/[0.03] hover:bg-white/[0.08] text-zinc-200 px-6 py-6 rounded-xl text-base backdrop-blur-md transition-all"
          >
            <Link href="/stock/RELIANCE.NS" className="flex items-center justify-center gap-2">
              <BarChart3 className="size-5 text-cyan-400" />
              Stock Detail Demo
            </Link>
          </Button>
        </div>

        {/* Feature Grid / Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full text-left">
          {/* Feature 1 */}
          <div className="p-6 rounded-2xl border border-white/[0.08] bg-card/50 backdrop-blur-md hover:border-emerald-500/30 transition-all group">
            <div className="size-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <TrendingUp className="size-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2 flex items-center justify-between">
              Live Index Tracking
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-400"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />Live</span>
            </h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Track NIFTY 50, SENSEX, and BANK NIFTY indices with daily changes, intraday highs, and historical trends.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="p-6 rounded-2xl border border-white/[0.08] bg-card/50 backdrop-blur-md hover:border-cyan-500/30 transition-all group">
            <div className="size-11 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Layers className="size-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2 flex items-center justify-between">
              Sector Heatmaps
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-400"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />Live</span>
            </h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Understand market breadth across IT, Banking, FMCG, Auto, and Pharma sectors with visual performance tiles.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="p-6 rounded-2xl border border-white/[0.08] bg-card/50 backdrop-blur-md hover:border-indigo-500/30 transition-all group">
            <div className="size-11 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Zap className="size-5" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2 flex items-center justify-between">
              Technical Indicators
              <Badge variant="phase" className="text-[10px]">Phase 3</Badge>
            </h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Learn how RSI-14, MACD, and 200 EMA work with interactive educational explanations for every indicator.
            </p>
          </div>
        </div>

        {/* Quick Highlights Row */}
        <div className="mt-14 flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-xs sm:text-sm text-zinc-400 font-mono">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-emerald-400" />
            <span>100% Free & Open Source</span>
          </div>
          <div className="flex items-center gap-2">
            <Compass className="size-4 text-cyan-400" />
            <span>No Auth or Login Required</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="size-4 text-amber-400" />
            <span>Yahoo Finance ~15m Delayed</span>
          </div>
        </div>
      </div>

      {/* Footer Disclaimer Notice */}
      <footer className="relative z-10 border-t border-white/[0.06] bg-black/40 py-6 text-center text-xs text-zinc-500">
        <div className="max-w-4xl mx-auto px-4">
          <p className="leading-relaxed">
            🇮🇳 <strong className="text-zinc-400">BharatMarkets</strong>: {DISCLAIMER_TEXT}
          </p>
        </div>
      </footer>
    </div>
  );
}
