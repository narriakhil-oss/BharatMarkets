/**
 * BharatMarkets Formatting Utilities
 * Specialized for the Indian financial context (₹, Lakh, Crore, IST).
 */

import { cn } from "@/lib/utils";

export { cn };

/**
 * Format a number into standard Indian Rupee currency format (e.g., ₹12,34,567.89).
 */
export function formatINR(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "₹0.00";
  }

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format large Indian currency values into compact readable units (Cr, L, or thousands).
 * Examples: ₹1.50 Cr, ₹2.30 L, ₹45,000
 */
export function formatCompact(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "₹0";
  }

  const isNegative = value < 0;
  const absValue = Math.abs(value);
  const prefix = isNegative ? "-₹" : "₹";

  // 1 Crore = 1,00,00,000 (10^7)
  if (absValue >= 10_000_000) {
    return `${prefix}${(absValue / 10_000_000).toFixed(2)} Cr`;
  }

  // 1 Lakh = 1,00,000 (10^5)
  if (absValue >= 100_000) {
    return `${prefix}${(absValue / 100_000).toFixed(2)} L`;
  }

  // Under 1 Lakh: standard Indian grouping without decimals
  return `${prefix}${new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(absValue)}`;
}

/**
 * Format percentage change with sign and 2 decimal places.
 * Examples: +2.34%, -1.23%, 0.00%
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "0.00%";
  }

  if (value > 0) {
    return `+${value.toFixed(2)}%`;
  }
  if (value < 0) {
    return `${value.toFixed(2)}%`;
  }
  return "0.00%";
}

/**
 * Format trading volume in short notation.
 * Examples: 1.2M, 45.3K, 850
 */
export function formatVolume(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "0";
  }

  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";

  if (abs >= 1_000_000_000) {
    return `${sign}${(abs / 1_000_000_000).toFixed(1)}B`;
  }
  if (abs >= 1_000_000) {
    return `${sign}${(abs / 1_000_000).toFixed(1)}M`;
  }
  if (abs >= 1_000) {
    return `${sign}${(abs / 1_000).toFixed(1)}K`;
  }
  return `${sign}${Math.round(abs).toString()}`;
}

/**
 * Format date string or Date object to "17 Oct 2026"
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return "--";

  try {
    const d = typeof date === "string" ? new Date(date) : date;
    if (isNaN(d.getTime())) return "--";

    return new Intl.DateTimeFormat("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
      timeZone: "Asia/Kolkata",
    }).format(d);
  } catch {
    return "--";
  }
}

/**
 * Format date string or Date object to "2:30 PM IST"
 */
export function formatTime(date: string | Date | null | undefined): string {
  if (!date) return "--";

  try {
    const d = typeof date === "string" ? new Date(date) : date;
    if (isNaN(d.getTime())) return "--";

    const formatted = new Intl.DateTimeFormat("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
      timeZone: "Asia/Kolkata",
    }).format(d);

    return `${formatted} IST`;
  } catch {
    return "--";
  }
}
