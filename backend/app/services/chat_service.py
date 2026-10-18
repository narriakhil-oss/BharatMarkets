"""Chat orchestration: Gemini tool calling + structured chart payloads."""

from __future__ import annotations

import json
import logging
import time
import uuid
from decimal import Decimal
from typing import Any, AsyncIterator, Dict, List, Optional

from app.providers.base import MarketDataProvider
from app.providers.llm.base import LLMMessage, LLMProvider, LLMToolSpec
from app.providers.llm.gemini_provider import GeminiProvider
from app.schemas.chat import ChatMessage, ChatStructuredPayload
from app.services.analysis_tool_service import AnalysisToolService
from app.services.forecast_service import ForecastService
from app.services.history_service import HistoryService
from app.services.market_service import MarketService
from app.services.signal_service import SignalService
from app.services.sentiment_service import SentimentService

logger = logging.getLogger(__name__)

MAX_SESSION_MESSAGES = 10
MAX_TOOL_ROUNDS = 4

SYSTEM_PROMPT = """You are BharatMarkets Assistant — a friendly stock-market tutor for beginners learning about NSE stocks.

Rules you MUST follow:
1. ONLY use numbers, dates, prices, percentages, forecasts, and signals returned by tools. Never invent prices, dates, indicators, or predictions.
2. If a tool fails or returns an error, say so clearly and do not guess the missing numbers.
3. Speak in plain English for beginners. Keep answers focused and concise.
4. Past values: summarize start price, end price, % change, period high/low, and any notable move visible in the tool data.
5. When asked "Should I buy X?": call get_signal (and supporting tools as needed). Give Buy/Sell/Hold with the numeric score, 3–5 reasons taken ONLY from tool outputs, plus the entry zone and stop-loss ranges from the signal tool.
6. Forecasts: present them as a range (lower–upper) and mention the backtest MAPE / directional accuracy from the tool. Always end forecast or signal answers with exactly:
   Model-generated signal for a college project. Not financial advice.
7. You may compare two stocks (call tools for each) and answer questions about today's market via get_market_overview.
8. Map casual names like "Reliance" or "TCS" using the symbol fields returned by tools (NSE Yahoo symbols like RELIANCE.NS).
9. Never guarantee returns or future performance. Refuse gambling/guaranteed-profit framing politely.
10. Keep off-topic answers brief and steer back to Indian stocks / this educational app.
11. Sentiment/news analysis is not available yet — do not claim news sentiment.
"""


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return str(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


class ChatSessionStore:
    """In-memory last-N messages per session_id."""

    def __init__(self, max_messages: int = MAX_SESSION_MESSAGES):
        self.max_messages = max_messages
        self._sessions: Dict[str, List[ChatMessage]] = {}
        self._updated: Dict[str, float] = {}

    def get(self, session_id: str) -> List[ChatMessage]:
        return list(self._sessions.get(session_id, []))

    def append(self, session_id: str, role: str, content: str) -> None:
        msgs = self._sessions.setdefault(session_id, [])
        msgs.append(ChatMessage(role=role, content=content))  # type: ignore[arg-type]
        if len(msgs) > self.max_messages:
            self._sessions[session_id] = msgs[-self.max_messages :]
        self._updated[session_id] = time.time()


# Process-wide session store (fine for local college project)
session_store = ChatSessionStore()


class ChatService:
    """Runs tool-augmented Gemini chats and emits SSE-friendly events."""

    def __init__(
        self,
        provider: MarketDataProvider,
        market_service: MarketService,
        llm: Optional[LLMProvider] = None,
    ):
        self.market_provider = provider
        self.market_service = market_service
        self.history_service = HistoryService(provider)
        self.forecast_service = ForecastService(provider)
        self.signal_service = SignalService(provider, self.forecast_service)
        self.analysis_service = AnalysisToolService(provider)
        self.sentiment_service = SentimentService()  # hook only
        self.llm = llm or GeminiProvider()

    def tool_specs(self) -> List[LLMToolSpec]:
        return [
            LLMToolSpec(
                name="get_history",
                description="Past daily prices for an NSE stock: start/end, % change, high, low, series. Periods: 1W, 1M, 3M, 6M, 1Y.",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Ticker or company name, e.g. RELIANCE, TCS, Infosys",
                        },
                        "period": {
                            "type": "string",
                            "enum": ["1W", "1M", "3M", "6M", "1Y"],
                            "description": "Lookback period",
                        },
                    },
                    "required": ["symbol"],
                },
            ),
            LLMToolSpec(
                name="get_analysis",
                description="Technical indicators (SMA, RSI, MACD, ATR, support/resistance, 52w high/low) and trend summary.",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Ticker or company name"},
                    },
                    "required": ["symbol"],
                },
            ),
            LLMToolSpec(
                name="get_forecast",
                description="Forecast next 7 or 30 trading days of closes with lower/upper band and walk-forward backtest metrics.",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "horizon_days": {
                            "type": "string",
                            "enum": ["7", "30"],
                            "description": "Forecast horizon in trading days (7 or 30)",
                        },
                    },
                    "required": ["symbol"],
                },
            ),
            LLMToolSpec(
                name="get_signal",
                description="Transparent Buy/Sell/Hold score with factor breakdown, entry zone, and stop-loss ranges.",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                    },
                    "required": ["symbol"],
                },
            ),
            LLMToolSpec(
                name="get_market_overview",
                description="Today's market snapshot: indices, top gainers, top losers.",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "How many gainers/losers to include (default 5)",
                        }
                    },
                },
            ),
        ]

    async def _exec_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "get_history":
                period = str(args.get("period") or "3M").upper()
                result = await self.history_service.get_history(str(args["symbol"]), period)
                return {"ok": True, "data": _json_safe(result)}
            if name == "get_analysis":
                result = await self.analysis_service.get_analysis(str(args["symbol"]))
                return {"ok": True, "data": result}
            if name == "get_forecast":
                horizon = int(args.get("horizon_days") or 7)
                result = await self.forecast_service.get_forecast(str(args["symbol"]), horizon)
                return {"ok": True, "data": _json_safe(result)}
            if name == "get_signal":
                result = await self.signal_service.get_signal(str(args["symbol"]))
                return {"ok": True, "data": _json_safe(result)}
            if name == "get_market_overview":
                limit = int(args.get("limit") or 5)
                indices = await self.market_service.get_indices()
                gainers = await self.market_service.get_top_gainers(limit=limit)
                losers = await self.market_service.get_top_losers(limit=limit)
                status = self.market_service.get_market_status()
                return {
                    "ok": True,
                    "data": {
                        "status": _json_safe(status),
                        "indices": _json_safe(indices),
                        "gainers": _json_safe(gainers),
                        "losers": _json_safe(losers),
                    },
                }
            return {"ok": False, "error": f"Unknown tool: {name}"}
        except Exception as e:
            logger.exception("Tool %s failed: %s", name, e)
            return {"ok": False, "error": str(e)}

    def _merge_structured(
        self,
        structured: ChatStructuredPayload,
        tool_name: str,
        payload: Dict[str, Any],
    ) -> None:
        if not payload.get("ok"):
            return
        data = payload.get("data")
        if data is None:
            return
        try:
            if tool_name == "get_history":
                from app.schemas.chat import HistorySummary

                structured.history = HistorySummary(**data)
            elif tool_name == "get_forecast":
                from app.schemas.chat import ForecastResult

                structured.forecast = ForecastResult(**data)
            elif tool_name == "get_signal":
                from app.schemas.chat import SignalResult

                structured.signal = SignalResult(**data)
            elif tool_name == "get_market_overview":
                structured.market_overview = data
            elif tool_name == "get_analysis":
                structured.analysis = data
        except Exception as e:
            logger.debug("Could not attach structured data for %s: %s", tool_name, e)

    async def stream_chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        client_history: Optional[List[ChatMessage]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Yield dict events:
          {"type":"session","session_id":...}
          {"type":"text","content":...}
          {"type":"structured","data":...}
          {"type":"error","message":...}
          {"type":"done"}
        """
        sid = session_id or str(uuid.uuid4())
        yield {"type": "session", "session_id": sid}

        # Seed from client history if server session empty
        if not session_store.get(sid) and client_history:
            for m in client_history[-MAX_SESSION_MESSAGES:]:
                session_store.append(sid, m.role, m.content)

        session_store.append(sid, "user", message)

        history = session_store.get(sid)
        llm_messages = [
            LLMMessage(role=m.role, content=m.content) for m in history
        ]

        structured = ChatStructuredPayload()
        tools = self.tool_specs()
        assistant_text_parts: List[str] = []

        async def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
            result = await self._exec_tool(name, args)
            self._merge_structured(structured, name, result)
            return result

        try:
            # Keep Gemini Content objects inside the provider so thought_signature
            # is never dropped between tool rounds.
            run = getattr(self.llm, "run_tool_loop", None)
            if run is None:
                raise RuntimeError("LLM provider does not support run_tool_loop")

            async for event in run(
                SYSTEM_PROMPT,
                llm_messages,
                tools,
                execute_tool,
                max_rounds=MAX_TOOL_ROUNDS,
            ):
                if event.type == "error":
                    yield {"type": "error", "message": event.error}
                    yield {"type": "done"}
                    return
                if event.type == "status" and event.text:
                    yield {"type": "status", "content": event.text}
                elif event.type == "text" and event.text:
                    assistant_text_parts.append(event.text)
                    yield {"type": "text", "content": event.text}
                elif event.type == "done":
                    break

            structured_dump = structured.model_dump(mode="json", exclude_none=True)
            if structured_dump:
                yield {"type": "structured", "data": structured_dump}

            full_text = "".join(assistant_text_parts).strip()
            if not full_text:
                if structured_dump:
                    full_text = (
                        "I pulled the latest tool data for you. "
                        "See the charts and signal card below for the numbers. "
                        "Model-generated signal for a college project. Not financial advice."
                    )
                    yield {"type": "text", "content": full_text}
                else:
                    full_text = (
                        "I could not produce an answer. "
                        "Please try again, or check that the Gemini API key is configured."
                    )
                    yield {"type": "error", "message": full_text}

            if full_text:
                session_store.append(sid, "assistant", full_text)

            yield {"type": "done"}
        except Exception as e:
            logger.exception("Chat stream failed: %s", e)
            msg = str(e)
            if "GEMINI_API_KEY" in msg or "api key" in msg.lower():
                msg = "Gemini API key is missing. Add GEMINI_API_KEY to backend/.env and restart the server."
            yield {"type": "error", "message": msg}
            yield {"type": "done"}
