import { NextResponse } from "next/server";

const YF_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "en-US,en;q=0.9",
  "Origin": "https://finance.yahoo.com",
  "Referer": "https://finance.yahoo.com/",
};

const NIFTY50 = [
  "RELIANCE.NS","TCS.NS","HDFCBANK.NS","BHARTIARTL.NS","ICICIBANK.NS",
  "INFOSYS.NS","SBIN.NS","HINDUNILVR.NS","ITC.NS","KOTAKBANK.NS",
  "LT.NS","AXISBANK.NS","MARUTI.NS","SUNPHARMA.NS","TITAN.NS",
  "BAJFINANCE.NS","NTPC.NS","WIPRO.NS","HCLTECH.NS","ULTRACEMCO.NS",
  "POWERGRID.NS","ADANIENT.NS","ADANIPORTS.NS","ASIANPAINT.NS","BAJAJFINSV.NS",
  "COALINDIA.NS","DRREDDY.NS","EICHERMOT.NS","GRASIM.NS","HEROMOTOCO.NS",
  "HINDALCO.NS","INDUSINDBK.NS","JSWSTEEL.NS","TATAMOTORS.NS","NESTLEIND.NS",
  "ONGC.NS","SBILIFE.NS","SHRIRAMFIN.NS","TATACONSUM.NS","MM.NS",
  "TATASTEEL.NS","TECHM.NS","TRENT.NS","BPCL.NS","ZOMATO.NS",
  "CIPLA.NS","DIVISLAB.NS","APOLLOHOSP.NS","BEL.NS","BRITANNIA.NS",
];

type Quote = {
  symbol: string; name: string; ltp: number;
  change: number; change_pct: number; volume: number;
};

async function fetchSingleChart(symbol: string): Promise<Quote | null> {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`;
    const res = await fetch(url, { headers: YF_HEADERS, cache: "no-store" });
    if (!res.ok) return null;
    const json = await res.json();
    const meta = json?.chart?.result?.[0]?.meta;
    if (!meta) return null;
    const ltp: number = meta.regularMarketPrice ?? meta.previousClose ?? 0;
    const prev: number = meta.chartPreviousClose ?? meta.previousClose ?? ltp;
    const change = +(ltp - prev).toFixed(2);
    const change_pct = prev ? +((change / prev) * 100).toFixed(2) : 0;
    const shortName: string = (meta.shortName ?? meta.symbol ?? symbol)
      .replace(/ Limited$/i, "").replace(/ Ltd\.?$/i, "");
    return {
      symbol,
      name: shortName,
      ltp, change, change_pct,
      volume: meta.regularMarketVolume ?? 0,
    };
  } catch {
    return null;
  }
}

export async function GET() {
  // Fetch all in parallel using v8 chart (avoids 401 on v7)
  const results = await Promise.all(NIFTY50.map(fetchSingleChart));
  const quotes: Quote[] = results.filter((q): q is Quote => q !== null && q.ltp > 0);

  if (quotes.length === 0) {
    return NextResponse.json({ gainers: [], losers: [], error: "No data from Yahoo Finance" }, { status: 502 });
  }

  const sorted = [...quotes].sort((a, b) => b.change_pct - a.change_pct);
  return NextResponse.json({
    gainers: sorted.slice(0, 10),
    losers:  sorted.slice(-10).reverse(),
  });
}
