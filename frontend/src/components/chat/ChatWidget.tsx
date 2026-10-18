"use client";

import * as React from "react";
import { MessageCircle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { cn } from "@/lib/utils";

export function ChatWidget() {
  const [open, setOpen] = React.useState(false);

  return (
    <>
      {/* Floating panel */}
      <div
        className={cn(
          "fixed z-50 bottom-20 right-4 sm:bottom-24 sm:right-6",
          "w-[min(100vw-2rem,24rem)] h-[min(70vh,32rem)]",
          "transition-all duration-300 ease-out origin-bottom-right",
          open
            ? "opacity-100 scale-100 pointer-events-auto"
            : "opacity-0 scale-95 pointer-events-none"
        )}
      >
        <ChatPanel variant="drawer" onClose={() => setOpen(false)} className="h-full" />
      </div>

      {/* FAB — sits above the disclaimer bar */}
      <Button
        type="button"
        size="icon"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close assistant" : "Open assistant"}
        className={cn(
          "fixed z-50 bottom-16 right-4 sm:bottom-20 sm:right-6",
          "size-12 rounded-full shadow-lg shadow-emerald-900/40",
          "bg-emerald-600 hover:bg-emerald-500 text-white border border-emerald-400/30"
        )}
      >
        {open ? <X className="size-5" /> : <MessageCircle className="size-5" />}
      </Button>
    </>
  );
}
