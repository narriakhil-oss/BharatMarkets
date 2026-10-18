"use client";

import { useEffect, useState, useCallback } from "react";
import { MarketStatus } from "@/types/market";
import { getMarketStatus } from "@/lib/api";

interface UseMarketStatusReturn {
  data: MarketStatus | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Custom React hook to poll Indian market open/close status every 60 seconds.
 */
export function useMarketStatus(): UseMarketStatusReturn {
  const [data, setData] = useState<MarketStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const result = await getMarketStatus();
      setData(result);
      setError(null);
    } catch (err) {
      // In development or when backend isn't up yet, fallback gracefully
      const fallbackError =
        err instanceof Error ? err : new Error("Failed to fetch market status");
      setError(fallbackError);

      // Provide sensible default fallback state for UI continuity
      setData((prev) =>
        prev
          ? prev
          : {
              is_open: false,
              status: "CLOSED",
              status_text: "Market Closed (Offline / Delayed)",
              current_time_ist: new Intl.DateTimeFormat("en-IN", {
                timeZone: "Asia/Kolkata",
                hour: "2-digit",
                minute: "2-digit",
                hour12: true,
              }).format(new Date()),
              next_open_ist: "",
              exchange: "NSE",
            }
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch
    fetchStatus();

    // 60-second polling interval
    const intervalId = setInterval(fetchStatus, 60_000);

    return () => clearInterval(intervalId);
  }, [fetchStatus]);

  return { data, isLoading, error, refetch: fetchStatus };
}
