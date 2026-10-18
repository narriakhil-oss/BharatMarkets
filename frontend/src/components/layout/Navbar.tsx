"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  TrendingUp,
  Clock,
  Menu,
  X,
  LayoutDashboard,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useMarketStatus } from "@/hooks/useMarketStatus";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const { data: marketStatus, isLoading } = useMarketStatus();

  const isDashboardActive = pathname === "/dashboard";
  const isAssistantActive = pathname === "/assistant" || pathname.startsWith("/assistant/");

  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/[0.08] bg-background/80 backdrop-blur-xl transition-all">
      {/* Subtle top indicator line with vibrant Indian tricolor accent glow */}
      <div className="h-[2px] w-full bg-gradient-to-r from-orange-500 via-white/80 to-emerald-500 opacity-80" />

      <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo and Brand */}
        <div className="flex items-center gap-6">
          <Link
            href="/"
            className="flex items-center gap-2.5 group transition-transform active:scale-95"
          >
            <div className="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 via-cyan-500/20 to-blue-500/20 border border-emerald-500/40 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.25)] group-hover:border-emerald-400">
              <TrendingUp className="size-5 transition-transform group-hover:scale-110" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
                Bharat<span className="text-emerald-400">Markets</span>
              </span>
              <span className="text-[10px] tracking-wider uppercase text-muted-foreground -mt-1 font-mono">
                NSE · BSE Intel
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-white/[0.08]">
            <Link
              href="/dashboard"
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                isDashboardActive
                  ? "bg-white/[0.08] text-white shadow-xs"
                  : "text-muted-foreground hover:text-white hover:bg-white/[0.04]"
              )}
            >
              <LayoutDashboard className="size-4" />
              <span>Dashboard</span>
            </Link>

            <Link
              href="/assistant"
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                isAssistantActive
                  ? "bg-white/[0.08] text-white shadow-xs"
                  : "text-muted-foreground hover:text-white hover:bg-white/[0.04]"
              )}
            >
              <Sparkles className="size-3.5 text-cyan-400" />
              <span>Assistant</span>
            </Link>
          </nav>
        </div>

        {/* Right side items: Market Status & Delayed Data Badge */}
        <div className="hidden sm:flex items-center gap-3">
          {/* Market Status Pill */}
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full border border-white/[0.08] bg-zinc-900/60 text-xs">
            <span className="relative flex h-2 w-2">
              <span
                className={cn(
                  "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                  marketStatus?.is_open ? "bg-emerald-400" : "bg-zinc-500"
                )}
              />
              <span
                className={cn(
                  "relative inline-flex rounded-full h-2 w-2",
                  marketStatus?.is_open ? "bg-emerald-500" : "bg-zinc-400"
                )}
              />
            </span>
            <span className="text-zinc-300 font-mono text-[11px]">
              {isLoading
                ? "Connecting..."
                : marketStatus?.is_open
                ? "NSE Open"
                : "NSE Closed"}
            </span>
          </div>

          {/* Delayed Data Badge */}
          <Badge
            variant="warning"
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-normal"
            title="Quotes are delayed by ~15 minutes (Yahoo Finance source)"
          >
            <Clock className="size-3 text-amber-400" />
            <span>Delayed ~15m</span>
          </Badge>

          {/* Quick Dashboard Action */}
          {!isDashboardActive && (
            <Button asChild size="sm" variant="outline" className="text-xs">
              <Link href="/dashboard">Launch App</Link>
            </Button>
          )}
        </div>

        {/* Mobile Hamburger Toggle */}
        <div className="flex sm:hidden items-center gap-2">
          <Badge variant="warning" className="text-[10px] px-1.5 py-0.5">
            Delayed ~15m
          </Badge>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
            className="text-zinc-300 hover:text-white"
          >
            {mobileMenuOpen ? (
              <X className="size-5" />
            ) : (
              <Menu className="size-5" />
            )}
          </Button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="sm:hidden border-t border-white/[0.08] bg-background/95 backdrop-blur-2xl px-4 py-4 space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] text-xs text-muted-foreground">
            <span>Market Status:</span>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  marketStatus?.is_open ? "bg-emerald-500" : "bg-zinc-400"
                )}
              />
              <span className="text-zinc-200 font-medium">
                {marketStatus?.is_open ? "NSE Open" : "NSE Closed"}
              </span>
            </div>
          </div>

          <div className="flex flex-col space-y-1">
            <Link
              href="/"
              onClick={() => setMobileMenuOpen(false)}
              className={cn(
                "px-3 py-2 rounded-md text-sm font-medium transition-colors",
                pathname === "/"
                  ? "bg-white/[0.08] text-white"
                  : "text-muted-foreground hover:text-white hover:bg-white/[0.04]"
              )}
            >
              Home
            </Link>
            <Link
              href="/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className={cn(
                "flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isDashboardActive
                  ? "bg-white/[0.08] text-white"
                  : "text-muted-foreground hover:text-white hover:bg-white/[0.04]"
              )}
            >
              <span className="flex items-center gap-2">
                <LayoutDashboard className="size-4" />
                Dashboard
              </span>
              <Badge variant="phase" className="text-[10px]">
                Phase 2
              </Badge>
            </Link>
            <Link
              href="/assistant"
              onClick={() => setMobileMenuOpen(false)}
              className={cn(
                "flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isAssistantActive
                  ? "bg-white/[0.08] text-white"
                  : "text-muted-foreground hover:text-white hover:bg-white/[0.04]"
              )}
            >
              <span className="flex items-center gap-2">
                <Sparkles className="size-4 text-cyan-400" />
                Assistant
              </span>
              <Badge variant="phase" className="text-[10px]">
                AI
              </Badge>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
