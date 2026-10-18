"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { DashboardData } from "@/types/market";
import { getDashboardData } from "@/lib/api";
import { isWithinMarketHours, POLL_INTERVAL_MS } from "@/lib/constants";

interface UseDashboardDataReturn {
  data: DashboardData | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refetch: () => Promise<void>;
  sectorPeriod: string;
  setSectorPeriod: (period: string) => void;
}

export function useDashboardData(): UseDashboardDataReturn {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [sectorPeriod, setSectorPeriod] = useState("1d");
  const isMounted = useRef(true);

  const fetchData = useCallback(
    async (isBackground = false) => {
      if (!isBackground) setIsLoading(true);

      try {
        const result = await getDashboardData(sectorPeriod);
        if (!isMounted.current) return;
        setData(result);
        setLastUpdated(new Date());
        setError(null);
      } catch (err) {
        if (!isMounted.current) return;
        // Keep stale data on background refresh failure
        if (!isBackground) {
          setError(err instanceof Error ? err.message : "Failed to fetch dashboard data");
        }
      } finally {
        if (isMounted.current) setIsLoading(false);
      }
    },
    [sectorPeriod]
  );

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    await fetchData(false);
  }, [fetchData]);

  useEffect(() => {
    isMounted.current = true;
    fetchData(false);

    let intervalId: ReturnType<typeof setInterval> | null = null;

    if (isWithinMarketHours()) {
      intervalId = setInterval(() => {
        fetchData(true);
      }, POLL_INTERVAL_MS);
    }

    return () => {
      isMounted.current = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [fetchData]);

  return { data, isLoading, error, lastUpdated, refetch, sectorPeriod, setSectorPeriod };
}
