"use client";

import * as React from "react";
import Link from "next/link";
import { Bot, Loader2, Send, Maximize2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError, streamChat } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  ChatMessage,
  ChatStructuredData,
  QUICK_PROMPTS,
} from "@/types/chat";
import { HistoryMiniChart } from "@/components/chat/HistoryMiniChart";
import { ForecastMiniChart } from "@/components/chat/ForecastMiniChart";
import { SignalCard } from "@/components/chat/SignalCard";

interface ChatPanelProps {
  variant?: "drawer" | "page";
  onClose?: () => void;
  className?: string;
}

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function ChatPanel({ variant = "drawer", onClose, className }: ChatPanelProps) {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState("");
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [streaming, setStreaming] = React.useState(false);
  const [statusLine, setStatusLine] = React.useState<string | null>(null);
  const [errorBanner, setErrorBanner] = React.useState<string | null>(null);
  const bottomRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLTextAreaElement>(null);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming, statusLine]);

  const send = React.useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || streaming) return;

      setErrorBanner(null);
      setStatusLine(null);
      setInput("");

      const userMsg: ChatMessage = { id: uid(), role: "user", content: trimmed };
      const assistantId = uid();
      setMessages((prev) => [
        ...prev,
        userMsg,
        { id: assistantId, role: "assistant", content: "", structured: null },
      ]);
      setStreaming(true);

      try {
        let structured: ChatStructuredData | null = null;
        for await (const event of streamChat({
          message: trimmed,
          sessionId,
        })) {
          if (event.type === "session") {
            setSessionId(event.session_id);
          } else if (event.type === "status") {
            setStatusLine(event.content);
          } else if (event.type === "text") {
            setStatusLine(null);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + event.content }
                  : m
              )
            );
          } else if (event.type === "structured") {
            structured = event.data;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, structured: event.data } : m
              )
            );
          } else if (event.type === "error") {
            setErrorBanner(event.message);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: m.content || event.message,
                      error: true,
                    }
                  : m
              )
            );
          }
        }

        // If structured arrived after empty text, keep it
        if (structured) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, structured } : m
            )
          );
        }
      } catch (err) {
        const msg =
          err instanceof ApiError
            ? err.message
            : "Something went wrong talking to the assistant.";
        setErrorBanner(msg);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: msg, error: true }
              : m
          )
        );
      } finally {
        setStreaming(false);
        setStatusLine(null);
        inputRef.current?.focus();
      }
    },
    [sessionId, streaming]
  );

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send(input);
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col bg-card border border-white/[0.08] overflow-hidden",
        variant === "drawer" && "h-full rounded-xl shadow-2xl",
        variant === "page" && "min-h-[70vh] rounded-xl",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2 border-b border-white/[0.08] px-4 py-3 bg-zinc-950/40">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex size-8 items-center justify-center rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
            <Bot className="size-4" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-zinc-100 truncate">
              Market Assistant
            </p>
            <p className="text-[10px] text-muted-foreground truncate">
              Educational · NSE data via tools · Not financial advice
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {variant === "drawer" && (
            <Button asChild variant="ghost" size="icon" className="size-8 text-zinc-400">
              <Link href="/assistant" title="Open full page">
                <Maximize2 className="size-4" />
              </Link>
            </Button>
          )}
          {onClose && (
            <Button
              variant="ghost"
              size="icon"
              className="size-8 text-zinc-400"
              onClick={onClose}
              aria-label="Close chat"
            >
              <X className="size-4" />
            </Button>
          )}
        </div>
      </div>

      {errorBanner && (
        <div className="px-4 py-2 text-xs bg-rose-500/10 text-rose-300 border-b border-rose-500/20">
          {errorBanner}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-sm text-zinc-300">
              Ask about past prices, trends, forecasts, or Buy/Sell/Hold signals for NSE stocks.
            </p>
            <div className="flex flex-wrap gap-2">
              {QUICK_PROMPTS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => void send(q)}
                  disabled={streaming}
                  className="text-left text-[11px] px-2.5 py-1.5 rounded-md border border-white/[0.1] bg-white/[0.03] text-zinc-300 hover:bg-white/[0.06] hover:text-white transition-colors disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={cn(
              "flex",
              m.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[92%] rounded-lg px-3 py-2 text-sm leading-relaxed",
                m.role === "user"
                  ? "bg-emerald-600/20 text-emerald-50 border border-emerald-500/25"
                  : m.error
                  ? "bg-rose-500/10 text-rose-200 border border-rose-500/20"
                  : "bg-zinc-900/80 text-zinc-200 border border-white/[0.06]"
              )}
            >
              {m.content ? (
                <p className="whitespace-pre-wrap">{m.content}</p>
              ) : (
                streaming && (
                  <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Loader2 className="size-3.5 animate-spin" />
                    Thinking…
                  </span>
                )
              )}

              {m.structured?.history && (
                <HistoryMiniChart history={m.structured.history} />
              )}
              {m.structured?.forecast && (
                <ForecastMiniChart forecast={m.structured.forecast} />
              )}
              {m.structured?.signal && <SignalCard signal={m.structured.signal} />}
            </div>
          </div>
        ))}

        {statusLine && (
          <p className="text-[11px] text-cyan-400/90 flex items-center gap-1.5">
            <Loader2 className="size-3 animate-spin" />
            {statusLine}
          </p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      <div className="border-t border-white/[0.08] p-3 bg-zinc-950/30">
        {messages.length > 0 && (
          <div className="mb-2 flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {QUICK_PROMPTS.slice(0, 3).map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => void send(q)}
                disabled={streaming}
                className="shrink-0 text-[10px] px-2 py-1 rounded border border-white/[0.08] text-zinc-400 hover:text-zinc-200 disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Ask about RELIANCE, TCS, the market…"
            disabled={streaming}
            className="flex-1 resize-none rounded-md border border-white/[0.1] bg-zinc-900/80 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 disabled:opacity-60 max-h-28"
          />
          <Button
            size="icon"
            disabled={streaming || !input.trim()}
            onClick={() => void send(input)}
            className="shrink-0"
            aria-label="Send message"
          >
            {streaming ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
