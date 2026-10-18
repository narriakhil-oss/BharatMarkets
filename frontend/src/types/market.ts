export interface MarketStatus {
  is_open: boolean;
  status: string;
  status_text: string;
  current_time_ist: string;
  next_open_ist: string;
  exchange: string;
  last_updated_ist?: string;
}

export interface IndexData {
  symbol: string;
  display_name: string;
  ltp: number;
  change: number;
  change_pct: number;
  exchange: string;
  day_high?: number | null;
  day_low?: number | null;
}

export interface StockQuote {
  symbol: string;
  name: string;
  sector?: string | null;
  ltp: number;
  prev_close?: number | null;
  change: number;
  change_pct: number;
  day_high?: number | null;
  day_low?: number | null;
  high_52w?: number | null;
  low_52w?: number | null;
  volume?: number | null;
  exchange?: string;
  updated_at?: string;
}

export interface OHLCVData {
  date: string;
  timestamp?: string | null;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SectorPerformance {
  sector: string;
  change_pct: number;
  stock_count: number;
}

export interface MarketBreadth {
  advances: number;
  declines: number;
  unchanged: number;
  total: number;
  advance_decline_ratio: number | null;
}

export interface TechnicalAnalysis {
  symbol: string;
  name: string;
  ltp: number;
  indicators: Record<string, number | null>;
  trend: {
    trend: string;
    strength: string;
    score: number;
    reasons: string[];
  };
  analyzed_at: string;
}

export interface DashboardData {
  status: MarketStatus | null;
  indices: IndexData[];
  gainers: StockQuote[];
  losers: StockQuote[];
  sectors: SectorPerformance[];
  breadth: MarketBreadth | null;
}
