import { NextResponse } from "next/server";

const YF_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "en-US,en;q=0.9",
  "Accept-Encoding": "gzip, deflate, br",
  "Origin": "https://finance.yahoo.com",
  "Referer": "https://finance.yahoo.com/",
};

const INDICES = [
  { symbol: "^NSEI",    display_name: "NIFTY 50",    exchange: "NSE" },
  { symbol: "^BSESN",   display_name: "SENSEX",      exchange: "BSE" },
  { symbol: "^NSEBANK", display_name: "BANK NIFTY",  exchange: "NSE" },
  { symbol: "^CNXIT",   display_name: "NIFTY IT",    exchange: "NSE" },
];

async function fetchChart(symbol: string) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d&includePrePost=false`;
  const res = await fetch(url, { headers: YF_HEADERS, cache: "no-store" });
  if (!res.ok) throw new Error(`${symbol}: HTTP ${res.status}`);
  const json = await res.json();
  const meta = json?.chart?.result?.[0]?.meta;
  if (!meta) throw new Error(`${symbol}: no meta`);
  const ltp: number = meta.regularMarketPrice ?? meta.previousClose ?? 0;
  const prev: number = meta.chartPreviousClose ?? meta.previousClose ?? ltp;
  const change = +(ltp - prev).toFixed(2);
  const change_pct = prev ? +((change / prev) * 100).toFixed(2) : 0;
  return {
    ltp, change, change_pct,
    day_high: meta.regularMarketDayHigh ?? null,
    day_low:  meta.regularMarketDayLow  ?? null,
  };
}

export async function GET() {
  const results = await Promise.allSettled(
    INDICES.map(async (idx) => {
      const q = await fetchChart(idx.symbol);
      return { ...idx, ...q };
    })
  );

  const data = results
    .filter((r): r is PromiseFulfilledResult<typeof INDICES[0] & ReturnType<typeof fetchChart> extends Promise<infer T> ? T : never> => r.status === "fulfilled")
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    .map((r) => (r as any).value);

  if (data.length === 0) {
    return NextResponse.json({ error: "All index fetches failed" }, { status: 502 });
  }
  return NextResponse.json(data);
}
