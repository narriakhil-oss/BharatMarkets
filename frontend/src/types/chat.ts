export interface PricePoint {
  date: string;
  close: number | string;
}

export interface HistorySummary {
  symbol: string;
  name?: string | null;
  period: string;
  start_price: number | string;
  end_price: number | string;
  change_pct: number | string;
  high: number | string;
  low: number | string;
  series: PricePoint[];
}

export interface ForecastPoint {
  date: string;
  predicted: number | string;
  lower: number | string;
  upper: number | string;
}

export interface BacktestMetrics {
  mape_pct?: number | string | null;
  directional_accuracy_pct?: number | string | null;
  samples: number;
  method: string;
  note?: string | null;
}

export interface ForecastResult {
  symbol: string;
  horizon_days: number;
  method: string;
  history_tail: PricePoint[];
  forecast: ForecastPoint[];
  backtest: BacktestMetrics;
  last_close?: number | string | null;
  forecast_change_pct?: number | string | null;
}

export interface SignalFactor {
  name: string;
  score: number;
  detail: string;
}

export interface PriceRange {
  low: number | string;
  high: number | string;
}

export interface SignalResult {
  symbol: string;
  signal: "Buy" | "Sell" | "Hold";
  score: number;
  factors: SignalFactor[];
  entry_zone?: PriceRange | null;
  stop_loss?: PriceRange | null;
  atr14?: number | string | null;
  support?: number | string | null;
  resistance?: number | string | null;
  backtest?: BacktestMetrics | null;
  ltp?: number | string | null;
}

export interface ChatStructuredData {
  history?: HistorySummary | null;
  forecast?: ForecastResult | null;
  signal?: SignalResult | null;
  market_overview?: Record<string, unknown> | null;
  analysis?: Record<string, unknown> | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  structured?: ChatStructuredData | null;
  status?: string | null;
  error?: boolean;
}

export type ChatStreamEvent =
  | { type: "session"; session_id: string }
  | { type: "text"; content: string }
  | { type: "status"; content: string }
  | { type: "structured"; data: ChatStructuredData }
  | { type: "error"; message: string }
  | { type: "done" };

export const QUICK_PROMPTS = [
  "How is the market today?",
  "Summarize RELIANCE's last 3 months",
  "Is TCS trending up or down?",
  "Compare INFY and TCS",
  "Should I buy HDFCBANK?",
] as const;

export function toNum(v: number | string | null | undefined): number | null {
  if (v === null || v === undefined || v === "") return null;
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : null;
}

export function formatPrice(v: number | string | null | undefined): string {
  const n = toNum(v);
  if (n === null) return "—";
  return n.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
