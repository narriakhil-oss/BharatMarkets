"use client";

import { ChatPanel } from "@/components/chat/ChatPanel";

export default function AssistantPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-50">
          Market <span className="text-emerald-400">Assistant</span>
        </h1>
        <p className="mt-2 text-sm text-muted-foreground max-w-xl">
          Ask about past prices, trends, forecasts, and Buy/Sell/Hold signals for NSE stocks.
          Answers use live tool data only — educational, not financial advice.
        </p>
      </div>
      <ChatPanel variant="page" className="h-[min(75vh,40rem)]" />
    </div>
  );
}
