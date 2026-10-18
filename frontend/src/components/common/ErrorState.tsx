"use client";

import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  message = "Failed to load market data. Please check your connection and try again.",
  onRetry,
  className = "",
}: ErrorStateProps) {
  return (
    <div className={`rounded-xl border border-red-500/20 bg-red-950/20 p-6 text-center backdrop-blur-md ${className}`}>
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10 text-red-400">
        <AlertCircle className="h-6 w-6" />
      </div>
      <h3 className="text-base font-semibold text-zinc-100">Unable to load data</h3>
      <p className="mt-1 text-sm text-zinc-400 max-w-md mx-auto">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-red-500/10 px-4 py-2 text-xs font-medium text-red-300 hover:bg-red-500/20 active:scale-95 transition-all border border-red-500/30 cursor-pointer"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
