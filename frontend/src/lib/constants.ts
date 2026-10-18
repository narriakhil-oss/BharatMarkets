/**
 * BharatMarkets Constants
 */

// Market hours in IST
export const MARKET_HOURS = {
  NSE: { open: "09:15", close: "15:30", preOpen: "09:00", timezone: "Asia/Kolkata" },
  BSE: { open: "09:15", close: "15:30", preOpen: "09:00", timezone: "Asia/Kolkata" },
} as const;

// Polling interval (30 seconds)
export const POLL_INTERVAL_MS = 30_000;

// Timeframe options
export const TIMEFRAMES = [
  { label: "1D", value: "1d" },
  { label: "1W", value: "1wk" },
  { label: "1M", value: "1mo" },
  { label: "3M", value: "3mo" },
  { label: "6M", value: "6mo" },
  { label: "1Y", value: "1y" },
  { label: "ALL", value: "max" },
] as const;

// Index symbols
export const INDEX_SYMBOLS = [
  { symbol: "^NSEI", name: "NIFTY 50" },
  { symbol: "^BSESN", name: "SENSEX" },
  { symbol: "^NSEBANK", name: "BANK NIFTY" },
  { symbol: "^CNXIT", name: "NIFTY IT" },
] as const;

// Sector list
export const SECTORS = [
  "Information Technology",
  "Financial Services",
  "Oil Gas & Consumable Fuels",
  "Fast Moving Consumer Goods",
  "Automobile and Auto Components",
  "Healthcare",
  "Metals & Mining",
  "Construction",
  "Telecommunication",
  "Consumer Durables",
  "Power",
  "Capital Goods",
  "Chemicals",
] as const;

// Disclaimer
export const DISCLAIMER_TEXT =
  "Educational purposes only. Not SEBI-registered investment advice. Data may be delayed ~15 minutes. Do not make investment decisions based on this data.";

/**
 * Check if current time is within NSE market hours (9:15 AM - 3:30 PM IST, Mon-Fri)
 */
export function isWithinMarketHours(): boolean {
  const now = new Date();
  const istOffset = 5.5 * 60; // IST is UTC+5:30 in minutes
  const utcMinutes = now.getUTCHours() * 60 + now.getUTCMinutes();
  const istMinutes = utcMinutes + istOffset;
  const istHour = Math.floor(istMinutes / 60) % 24;
  const istMin = istMinutes % 60;

  // Calculate IST day (handle day rollover near midnight)
  const day = now.getUTCDay();
  const istDay = istMinutes >= 1440 ? (day + 1) % 7 : day;

  // Weekend check (0 = Sunday, 6 = Saturday)
  if (istDay === 0 || istDay === 6) return false;

  const currentIST = istHour * 60 + istMin;
  const marketOpen = 9 * 60 + 15;  // 9:15 AM
  const marketClose = 15 * 60 + 30; // 3:30 PM

  return currentIST >= marketOpen && currentIST < marketClose;
}
