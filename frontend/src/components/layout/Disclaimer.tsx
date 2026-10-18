"use client";

import * as React from "react";
import { AlertTriangle, X } from "lucide-react";
import { DISCLAIMER_TEXT } from "@/lib/constants";

/**
 * Dismissible footer disclaimer banner.
 * Reminds users that BharatMarkets is an educational platform and not SEBI-registered advisory.
 */
export function Disclaimer() {
  const [isDismissed, setIsDismissed] = React.useState(false);

  if (isDismissed) {
    return null;
  }

  return (
    <aside
      aria-label="Legal Disclaimer"
      className="fixed bottom-0 inset-x-0 z-30 border-t border-amber-500/30 bg-amber-950/80 backdrop-blur-md px-4 py-2.5 shadow-lg transition-all animate-in slide-in-from-bottom-2 duration-300"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3 text-xs sm:text-sm text-amber-200">
        <div className="flex items-center gap-2.5 flex-1 min-w-0">
          <AlertTriangle className="size-4 shrink-0 text-amber-400" />
          <p className="truncate sm:whitespace-normal font-medium leading-tight">
            {DISCLAIMER_TEXT}
          </p>
        </div>

        <button
          onClick={() => setIsDismissed(true)}
          type="button"
          aria-label="Dismiss disclaimer banner"
          className="rounded-md p-1 text-amber-400 hover:bg-amber-900/60 hover:text-amber-100 transition-colors shrink-0"
        >
          <X className="size-4" />
        </button>
      </div>
    </aside>
  );
}
