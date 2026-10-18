import {
  DashboardData,
  IndexData,
  MarketBreadth,
  MarketStatus,
  SectorPerformance,
  StockQuote,
  OHLCVData,
  TechnicalAnalysis,
} from "@/types/market";
import type { ChatStreamEvent } from "@/types/chat";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function fetchJson<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new ApiError(res.status, `API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * Stream chat replies from POST /api/v1/chat (SSE).
 * Yields parsed events; throws ApiError on HTTP failures (incl. 429).
 */
export async function* streamChat(params: {
  message: string;
  sessionId?: string | null;
}): AsyncGenerator<ChatStreamEvent, void, unknown> {
  let res: Response;
  const controller = new AbortController();
  // Hard stop so the UI never spins for minutes on Gemini 503 / hangs
  const timer = setTimeout(() => controller.abort(), 90_000);
  try {
    res = await fetch(`${API_BASE}/api/v1/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({
        message: params.message,
        session_id: params.sessionId || undefined,
      }),
      cache: "no-store",
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timer);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(
        408,
        "Request timed out (90s). Gemini may be busy — wait a bit and try again."
      );
    }
    throw new ApiError(0, "Backend not running. Start the FastAPI server on port 8000.");
  }

  if (!res.ok) {
    clearTimeout(timer);
    if (res.status === 429) {
      throw new ApiError(
        429,
        "Rate limit reached (20 messages/min). Please wait a moment and try again."
      );
    }
    throw new ApiError(res.status, `Chat API error ${res.status}: ${res.statusText}`);
  }

  if (!res.body) {
    clearTimeout(timer);
    throw new ApiError(res.status, "Empty chat stream from backend.");
  }

  try {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        const line = chunk
          .split("\n")
          .map((l) => l.trim())
          .find((l) => l.startsWith("data:"));
        if (!line) continue;
        const raw = line.replace(/^data:\s*/, "");
        if (!raw || raw === "[DONE]") continue;
        try {
          yield JSON.parse(raw) as ChatStreamEvent;
        } catch {
          // skip malformed
        }
      }
    }
  } finally {
    clearTimeout(timer);
  }
}

export async function getMarketStatus(): Promise<MarketStatus> {
  return fetchJson<MarketStatus>("/api/v1/market/status");
}

export async function getIndices(): Promise<IndexData[]> {
  return fetchJson<IndexData[]>("/api/v1/market/indices");
}

export async function getGainers(): Promise<StockQuote[]> {
  return fetchJson<StockQuote[]>("/api/v1/market/gainers");
}

export async function getLosers(): Promise<StockQuote[]> {
  return fetchJson<StockQuote[]>("/api/v1/market/losers");
}

export async function getSectors(period: string = "1d"): Promise<SectorPerformance[]> {
  return fetchJson<SectorPerformance[]>(`/api/v1/market/sectors?period=${encodeURIComponent(period)}`);
}

export async function getMarketBreadth(): Promise<MarketBreadth> {
  return fetchJson<MarketBreadth>("/api/v1/market/breadth");
}

export async function searchStocks(query: string): Promise<StockQuote[]> {
  return fetchJson<StockQuote[]>(`/api/v1/stocks/search?q=${encodeURIComponent(query)}`);
}

export async function getStockQuote(symbol: string): Promise<StockQuote> {
  return fetchJson<StockQuote>(`/api/v1/stocks/${encodeURIComponent(symbol)}`);
}

export async function getOHLCV(symbol: string, interval = "1d", period = "1mo"): Promise<OHLCVData[]> {
  return fetchJson<OHLCVData[]>(`/api/v1/stocks/${encodeURIComponent(symbol)}/ohlcv?interval=${interval}&period=${period}`);
}

export async function getAnalysis(symbol: string): Promise<TechnicalAnalysis> {
  return fetchJson<TechnicalAnalysis>(`/api/v1/stocks/${encodeURIComponent(symbol)}/analysis`);
}

export async function getDashboardData(sectorPeriod: string = "1d"): Promise<DashboardData> {
  const [statusRes, indicesRes, gainersRes, losersRes, sectorsRes, breadthRes] =
    await Promise.allSettled([
      getMarketStatus(),
      getIndices(),
      getGainers(),
      getLosers(),
      getSectors(sectorPeriod),
      getMarketBreadth(),
    ]);

  return {
    status: statusRes.status === "fulfilled" ? statusRes.value : null,
    indices: indicesRes.status === "fulfilled" ? indicesRes.value || [] : [],
    gainers: gainersRes.status === "fulfilled" ? gainersRes.value || [] : [],
    losers: losersRes.status === "fulfilled" ? losersRes.value || [] : [],
    sectors: sectorsRes.status === "fulfilled" ? sectorsRes.value || [] : [],
    breadth: breadthRes.status === "fulfilled" ? breadthRes.value : null,
  };
}
